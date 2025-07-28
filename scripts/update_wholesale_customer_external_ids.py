#!/usr/bin/env python3
"""
Webex Wholesale Customer External ID Batch Update Script

This script updates external IDs for wholesale customers by reading from a CSV export
and using the simplified Update Wholesale Customer API. It replaces the existing externalId
with the customerId value for each customer.

The script supports:
- Dry-run mode to preview changes without making API calls
- Execute mode to perform actual updates
- Organization filtering by name patterns, exact matches, or exclusions
- Batch processing with progress tracking and error handling
- Comprehensive reporting of results

API Endpoint: PUT https://webexapis.com/v1/wholesale/customers/{customerId}
Request Body: {"externalId": "new_id", "packages": ["package1", "package2"]}
Authentication: Webex API token stored in .env file

Note: This version uses the simplified API that only requires externalId and packages.
No address or provisioning parameters are needed.
"""

import os
import csv
import json
import requests
import argparse
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# Constants
API_BASE_URL = "https://webexapis.com/v1"
OUTPUT_DIR = "output"
DEFAULT_BATCH_SIZE = 5
DEFAULT_DELAY = 0.2

def get_api_token() -> str:
    """
    Get the Webex API token from environment variables.
    
    Returns:
        str: The API token
        
    Raises:
        EnvironmentError: If the API token is not found
    """
    token = os.getenv("WEBEX_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError(
            "WEBEX_ACCESS_TOKEN not found in environment variables. "
            "Please create a .env file with your API token."
        )
    
    # Remove surrounding quotes if present (common in .env files)
    token = token.strip('"\'')
    
    return token

def get_headers() -> Dict[str, str]:
    """
    Get the headers for API requests.
    
    Returns:
        Dict[str, str]: Headers including authorization token
    """
    return {
        "Authorization": f"Bearer {get_api_token()}",
        "Content-Type": "application/json"
    }

def validate_api_token() -> bool:
    """
    Validate the API token by making a simple API call.
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        # Test with a simple API call to get user info
        url = f"{API_BASE_URL}/people/me"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        print("✓ API token validation successful")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ API token validation failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Status code: {e.response.status_code}")
            print(f"  Response: {e.response.text}")
        return False

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Update wholesale customer external IDs from CSV export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python scripts/update_wholesale_customer_external_ids.py --dry-run --input input/customers.csv
  
  # Execute updates for all customers
  python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv
  
  # Execute updates for specific organizations
  python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --org-names "Velvet Lab,Acme Corp"
  
  # Execute updates excluding certain organizations
  python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --exclude-orgs "Test Corp"
  
  # Execute with custom batch size and delay
  python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --batch-size 3 --delay 0.5
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--input", 
        required=True, 
        help="Path to the CSV file containing customer data"
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Preview changes without making API calls"
    )
    mode_group.add_argument(
        "--execute", 
        action="store_true", 
        help="Execute actual API updates"
    )
    
    # Organization filtering options
    filter_group = parser.add_argument_group("Organization Filtering")
    filter_group.add_argument(
        "--org-names", 
        help="Comma-separated list of exact organization names to include"
    )
    filter_group.add_argument(
        "--org-pattern", 
        help="Regex pattern to match organization names"
    )
    filter_group.add_argument(
        "--org-contains", 
        help="Include organizations containing this text (case-insensitive)"
    )
    filter_group.add_argument(
        "--exclude-orgs", 
        help="Comma-separated list of organization names to exclude"
    )
    
    # Processing options
    processing_group = parser.add_argument_group("Processing Options")
    processing_group.add_argument(
        "--batch-size", 
        type=int, 
        default=DEFAULT_BATCH_SIZE, 
        help=f"Number of customers to process in parallel (default: {DEFAULT_BATCH_SIZE})"
    )
    processing_group.add_argument(
        "--delay", 
        type=float, 
        default=DEFAULT_DELAY, 
        help=f"Delay between API calls in seconds (default: {DEFAULT_DELAY})"
    )
    processing_group.add_argument(
        "--output-dir", 
        default=OUTPUT_DIR, 
        help=f"Directory for output reports (default: {OUTPUT_DIR})"
    )
    
    # Additional options
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--resume-from", 
        help="Resume processing from this customer ID"
    )
    
    return parser.parse_args()

def load_csv_data(file_path: str) -> List[Dict[str, str]]:
    """
    Load customer data from CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        List[Dict[str, str]]: List of customer records
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV file is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    customers = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                # Skip empty rows (all values are empty or whitespace)
                if not any(value.strip() for value in row.values()):
                    continue
                
                # Validate required fields
                if not row.get('id') or not row.get('customerId'):
                    if any(value.strip() for value in row.values()):  # Only warn if row has some data
                        print(f"Warning: Skipping row {row_num} - missing required fields (id or customerId)")
                    continue
                
                customers.append(row)
        
        print(f"Loaded {len(customers)} valid customer records from {file_path}")
        return customers
        
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

def apply_organization_filters(customers: List[Dict[str, str]], args: argparse.Namespace) -> List[Dict[str, str]]:
    """
    Apply organization filtering based on command line arguments.
    
    Args:
        customers (List[Dict[str, str]]): List of customer records
        args (argparse.Namespace): Command line arguments
        
    Returns:
        List[Dict[str, str]]: Filtered list of customers
    """
    filtered_customers = customers.copy()
    original_count = len(filtered_customers)
    
    # Apply inclusion filters
    if args.org_names:
        org_names = [name.strip() for name in args.org_names.split(',')]
        filtered_customers = [
            customer for customer in filtered_customers
            if customer.get('org_details_displayName', '').strip() in org_names
        ]
        print(f"Filtered by organization names: {len(filtered_customers)} customers match")
    
    elif args.org_pattern:
        try:
            pattern = re.compile(args.org_pattern, re.IGNORECASE)
            filtered_customers = [
                customer for customer in filtered_customers
                if pattern.search(customer.get('org_details_displayName', ''))
            ]
            print(f"Filtered by pattern '{args.org_pattern}': {len(filtered_customers)} customers match")
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{args.org_pattern}': {e}")
    
    elif args.org_contains:
        search_text = args.org_contains.lower()
        filtered_customers = [
            customer for customer in filtered_customers
            if search_text in customer.get('org_details_displayName', '').lower()
        ]
        print(f"Filtered by contains '{args.org_contains}': {len(filtered_customers)} customers match")
    
    # Apply exclusion filter
    if args.exclude_orgs:
        exclude_names = [name.strip() for name in args.exclude_orgs.split(',')]
        before_exclude = len(filtered_customers)
        filtered_customers = [
            customer for customer in filtered_customers
            if customer.get('org_details_displayName', '').strip() not in exclude_names
        ]
        excluded_count = before_exclude - len(filtered_customers)
        print(f"Excluded {excluded_count} customers from specified organizations")
    
    if len(filtered_customers) != original_count:
        print(f"Organization filtering: {original_count} → {len(filtered_customers)} customers")
    
    return filtered_customers

def parse_packages(packages_str: str) -> List[str]:
    """
    Parse package string into a list of package names.
    
    Args:
        packages_str (str): Comma-separated package names
        
    Returns:
        List[str]: List of package names
    """
    if not packages_str:
        return []
    
    # Split by comma and clean up whitespace
    packages = [pkg.strip() for pkg in packages_str.split(',')]
    return [pkg for pkg in packages if pkg]  # Remove empty strings

def build_update_request(customer: Dict[str, str]) -> Dict[str, Any]:
    """
    Build the simplified API request body for updating a customer.
    
    Args:
        customer (Dict[str, str]): Customer record from CSV
        
    Returns:
        Dict[str, Any]: Simplified API request body
    """
    # Use customerId as the new externalId
    new_external_id = customer['customerId']
    
    # Parse packages
    packages = parse_packages(customer.get('packages', ''))
    
    # Build simplified request body - no address or provisioning parameters needed
    request_body = {
        "externalId": new_external_id,
        "packages": packages
    }
    
    return request_body

def validate_customer_data(customer: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that customer has required data for update.
    
    Args:
        customer (Dict[str, str]): Customer record from CSV
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields for simplified API
    if not customer.get('id'):
        errors.append("Missing customer ID")
    
    if not customer.get('customerId'):
        errors.append("Missing customerId")
    
    if not customer.get('packages'):
        errors.append("Missing packages")
    
    # Note: Address fields are no longer required for the simplified API
    
    return len(errors) == 0, errors

def update_wholesale_customer(customer_id: str, request_body: Dict[str, Any], delay: float = 0.2) -> Tuple[bool, Dict[str, Any]]:
    """
    Call the Update Wholesale Customer API with retry logic for 429 errors.
    
    Args:
        customer_id (str): The customer ID for the API endpoint
        request_body (Dict[str, Any]): The request body
        delay (float): Delay after API call for rate limiting
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (success, response_data)
    """
    url = f"{API_BASE_URL}/wholesale/customers/{customer_id}"
    max_retries = 3
    retry_delays = [5, 10, 30]  # Exponential backoff delays in seconds
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.put(url, headers=get_headers(), json=request_body)
            
            # Handle different response codes
            if response.status_code == 200:
                # Success
                time.sleep(delay)  # Rate limiting delay
                try:
                    return True, response.json()
                except json.JSONDecodeError:
                    return True, {"status": "success", "statusUrl": f"{API_BASE_URL}/wholesale/customers/{customer_id}"}
            
            elif response.status_code == 429:
                # Rate limited - retry with exponential backoff
                if attempt < max_retries:
                    retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    print(f"    Rate limited (429), retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Max retries exceeded
                    error_data = {
                        "error": f"429 Too Many Requests (max retries exceeded after {max_retries} attempts)",
                        "status_code": 429,
                        "response_body": response.text
                    }
                    return False, error_data
            
            else:
                # Other HTTP errors (409, 400, etc.) - don't retry
                try:
                    response_json = response.json()
                    error_message = response_json.get('message', f'HTTP {response.status_code} error')
                except json.JSONDecodeError:
                    error_message = f'HTTP {response.status_code} error'
                
                error_data = {
                    "error": error_message,
                    "status_code": response.status_code,
                    "response_body": response.text
                }
                return False, error_data
                
        except requests.exceptions.RequestException as e:
            # Network/connection errors - retry
            if attempt < max_retries:
                retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                print(f"    Request failed, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                error_data = {
                    "error": f"Request failed: {str(e)}",
                    "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                    "response_body": getattr(e.response, 'text', None) if hasattr(e, 'response') else None
                }
                return False, error_data
    
    # This should never be reached, but just in case
    error_data = {
        "error": "Unexpected error in retry logic",
        "status_code": None,
        "response_body": None
    }
    return False, error_data

def process_customer_update(customer: Dict[str, str], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Process a single customer update.
    
    Args:
        customer (Dict[str, str]): Customer record
        args (argparse.Namespace): Command line arguments
        
    Returns:
        Dict[str, Any]: Processing result
    """
    customer_id = customer['id']
    customer_name = customer.get('org_details_displayName', 'Unknown')
    current_external_id = customer.get('externalId', 'Unknown')
    new_external_id = customer['customerId']
    
    result = {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'current_external_id': current_external_id,
        'new_external_id': new_external_id,
        'success': False,
        'error': None,
        'api_response': None
    }
    
    # Validate customer data
    is_valid, errors = validate_customer_data(customer)
    if not is_valid:
        result['error'] = f"Validation failed: {'; '.join(errors)}"
        return result
    
    # Build request
    try:
        request_body = build_update_request(customer)
        result['request_body'] = request_body
    except Exception as e:
        result['error'] = f"Failed to build request: {e}"
        return result
    
    # Execute update if not dry run
    if args.execute:
        success, api_response = update_wholesale_customer(customer_id, request_body, args.delay)
        result['success'] = success
        result['api_response'] = api_response
        
        if not success:
            result['error'] = api_response.get('error', 'Unknown API error')
    else:
        # Dry run - mark as successful
        result['success'] = True
    
    return result

def generate_report(results: List[Dict[str, Any]], args: argparse.Namespace) -> str:
    """
    Generate a detailed report of the processing results.
    
    Args:
        results (List[Dict[str, Any]]): List of processing results
        args (argparse.Namespace): Command line arguments
        
    Returns:
        str: Path to the generated report file
    """
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate filename
    mode = "dry_run" if args.dry_run else "execution"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wholesale_customer_external_id_update_{mode}_{timestamp}.txt"
    filepath = os.path.join(args.output_dir, filename)
    
    # Calculate statistics
    total_customers = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total_customers - successful
    
    # Calculate error type statistics
    rate_limit_errors = 0
    conflict_errors = 0
    validation_errors = 0
    other_errors = 0
    
    for result in results:
        if not result['success'] and result.get('api_response'):
            status_code = result['api_response'].get('status_code')
            if status_code == 429:
                rate_limit_errors += 1
            elif status_code == 409:
                conflict_errors += 1
            elif status_code == 400:
                validation_errors += 1
            else:
                other_errors += 1
        elif not result['success']:
            other_errors += 1
    
    # Generate report content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Wholesale Customer External ID Update - {'Dry Run' if args.dry_run else 'Execution'} Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input File: {args.input}\n")
        f.write(f"Mode: {'Dry Run (Preview Only)' if args.dry_run else 'Execute Updates'}\n")
        f.write(f"Batch Size: {args.batch_size}\n")
        f.write(f"Delay Between Requests: {args.delay} seconds\n")
        f.write("\n")
        
        # Filters applied
        if any([args.org_names, args.org_pattern, args.org_contains, args.exclude_orgs]):
            f.write("Filters Applied:\n")
            if args.org_names:
                f.write(f"- Organization names: {args.org_names}\n")
            if args.org_pattern:
                f.write(f"- Organization pattern: {args.org_pattern}\n")
            if args.org_contains:
                f.write(f"- Organization contains: {args.org_contains}\n")
            if args.exclude_orgs:
                f.write(f"- Excluded organizations: {args.exclude_orgs}\n")
            f.write("\n")
        
        # Summary statistics
        f.write("Summary:\n")
        f.write(f"- Total customers processed: {total_customers}\n")
        f.write(f"- Successful updates: {successful}\n")
        f.write(f"- Failed updates: {failed}\n")
        if failed > 0:
            f.write(f"  - Rate limit errors (429): {rate_limit_errors}\n")
            f.write(f"  - Conflict errors (409): {conflict_errors}\n")
            f.write(f"  - Validation errors (400): {validation_errors}\n")
            f.write(f"  - Other errors: {other_errors}\n")
        f.write("\n")
        
        # Detailed results
        f.write("Detailed Results:\n")
        f.write("-" * 40 + "\n")
        
        for i, result in enumerate(results, 1):
            status = "✓" if result['success'] else "✗"
            f.write(f"{i}. {status} {result['customer_name']} (ID: {result['customer_id']})\n")
            f.write(f"   Current External ID: {result['current_external_id']}\n")
            f.write(f"   New External ID: {result['new_external_id']}\n")
            
            if result['error']:
                f.write(f"   Error: {result['error']}\n")
            elif args.execute and result['api_response']:
                f.write(f"   API Response: {result['api_response'].get('status', 'Success')}\n")
                # Check for status URL in various possible keys
                status_url = result['api_response'].get('statusUrl') or result['api_response'].get('url')
                if status_url:
                    f.write(f"   Status URL: {status_url}\n")
            
            f.write("\n")
        
        # Failed updates section
        if failed > 0:
            f.write("Failed Updates Details:\n")
            f.write("-" * 40 + "\n")
            for result in results:
                if not result['success']:
                    f.write(f"Customer: {result['customer_name']} (ID: {result['customer_id']})\n")
                    f.write(f"Error: {result['error']}\n")
                    if result.get('api_response') and isinstance(result['api_response'], dict):
                        if result['api_response'].get('status_code'):
                            f.write(f"HTTP Status: {result['api_response']['status_code']}\n")
                        if result['api_response'].get('response_body'):
                            f.write(f"Response: {result['api_response']['response_body']}\n")
                    f.write("\n")
    
    return filepath

def main():
    """
    Main function to run the script.
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        print("Webex Wholesale Customer External ID Batch Update")
        print("=" * 55)
        print(f"Mode: {'Dry Run (Preview Only)' if args.dry_run else 'Execute Updates'}")
        print(f"Input file: {args.input}")
        
        if args.dry_run:
            print("⚠️  DRY RUN MODE - No actual API calls will be made")
        else:
            # Validate API token before proceeding with execution
            print("Validating API token...")
            if not validate_api_token():
                print("❌ API token validation failed. Please check your .env file and token permissions.")
                return 1
        
        print()
        
        # Load CSV data
        print("Loading customer data from CSV...")
        customers = load_csv_data(args.input)
        
        if not customers:
            print("No valid customers found in CSV file.")
            return
        
        # Apply organization filters
        if any([args.org_names, args.org_pattern, args.org_contains, args.exclude_orgs]):
            print("Applying organization filters...")
            customers = apply_organization_filters(customers, args)
            
            if not customers:
                print("No customers match the specified filters.")
                return
        
        print(f"Processing {len(customers)} customers...")
        print()
        
        # Process customers
        results = []
        
        if args.batch_size == 1 or args.dry_run:
            # Sequential processing for dry run or batch size 1
            for i, customer in enumerate(customers, 1):
                print(f"Processing customer {i}/{len(customers)}: {customer.get('org_details_displayName', 'Unknown')}")
                result = process_customer_update(customer, args)
                results.append(result)
                
                if args.verbose:
                    status = "✓" if result['success'] else "✗"
                    print(f"  {status} {result['customer_name']} - External ID: {result['current_external_id']} → {result['new_external_id']}")
                    if result['error']:
                        print(f"    Error: {result['error']}")
        else:
            # Parallel processing for execute mode
            print(f"Processing customers in parallel (batch size: {args.batch_size})...")
            
            with ThreadPoolExecutor(max_workers=args.batch_size) as executor:
                # Submit all tasks
                future_to_customer = {
                    executor.submit(process_customer_update, customer, args): customer 
                    for customer in customers
                }
                
                # Process completed tasks
                completed = 0
                for future in as_completed(future_to_customer):
                    customer = future_to_customer[future]
                    completed += 1
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        status = "✓" if result['success'] else "✗"
                        print(f"  {status} ({completed}/{len(customers)}) {result['customer_name']}")
                        
                        if args.verbose and result['error']:
                            print(f"    Error: {result['error']}")
                            
                    except Exception as e:
                        print(f"  ✗ ({completed}/{len(customers)}) {customer.get('org_details_displayName', 'Unknown')} - Exception: {e}")
                        results.append({
                            'customer_id': customer.get('id', 'Unknown'),
                            'customer_name': customer.get('org_details_displayName', 'Unknown'),
                            'current_external_id': customer.get('externalId', 'Unknown'),
                            'new_external_id': customer.get('customerId', 'Unknown'),
                            'success': False,
                            'error': f"Processing exception: {e}",
                            'api_response': None
                        })
        
        # Generate report
        print("\nGenerating report...")
        report_path = generate_report(results, args)
        
        # Display summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"\n{'Dry Run' if args.dry_run else 'Update'} completed!")
        print(f"Report saved to: {report_path}")
        print(f"Total customers: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print(f"\n⚠️  {failed} customers failed to update. Check the report for details.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())