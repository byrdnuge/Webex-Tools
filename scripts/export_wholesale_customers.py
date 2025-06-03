#!/usr/bin/env python3
"""
Webex Wholesale Customers Export Script

This script retrieves all wholesale customers from the Webex API and exports
their information to a CSV spreadsheet. For each customer, it also fetches
the organization details to get the human-readable display name.

The script uses two main API endpoints:
- List Wholesale Customers API: https://webexapis.com/v1/wholesale/customers
- Get Organization Details API: https://webexapis.com/v1/organizations/{orgId}

Authentication is handled via a Webex API token stored in a .env file.
Features:
- Proper pagination handling for wholesale customers API
- Parallel processing for organization details retrieval
- Progress tracking and error handling
"""

import os
import csv
import json
import requests
import asyncio
import aiohttp
import argparse
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Load environment variables from .env file
load_dotenv()

# Constants
API_BASE_URL = "https://webexapis.com/v1"
OUTPUT_DIR = "output"
DEFAULT_CSV_FILENAME = "wholesale_customers_export.csv"
MAX_WORKERS = 10  # Number of parallel threads for org details
BATCH_SIZE = 100  # Number of customers to process per page
RATE_LIMIT_DELAY = 0.1  # Delay between requests to avoid rate limiting

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

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Export wholesale customers information to CSV with organization filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all customers
  python scripts/export_wholesale_customers.py
  
  # Export customers for specific organizations by display name
  python scripts/export_wholesale_customers.py --org-names "Velvet Lab,Acme Corp"
  
  # Export customers for specific organization IDs
  python scripts/export_wholesale_customers.py --org-ids "Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8zZTE5OGUzZC0zNzY1LTQ3YjAtYmYwZi0yNzQ5OTc4ZTUyNmM"
  
  # Export customers matching a pattern
  python scripts/export_wholesale_customers.py --org-pattern ".*Lab.*"
  
  # Export customers containing specific text
  python scripts/export_wholesale_customers.py --org-contains "velvet"
  
  # Export with custom filename
  python scripts/export_wholesale_customers.py --output "my_customers.csv"
        """
    )
    
    # Organization filtering options
    filter_group = parser.add_argument_group("Organization Filtering")
    filter_group.add_argument(
        "--org-names",
        help="Comma-separated list of exact organization display names to include"
    )
    filter_group.add_argument(
        "--org-ids",
        help="Comma-separated list of organization IDs to include"
    )
    filter_group.add_argument(
        "--external-ids",
        help="Comma-separated list of external IDs to include"
    )
    filter_group.add_argument(
        "--status",
        choices=["provisioning", "provisioned", "error"],
        help="Filter by customer status"
    )
    filter_group.add_argument(
        "--org-pattern",
        help="Regex pattern to match organization display names"
    )
    filter_group.add_argument(
        "--org-contains",
        help="Include organizations containing this text (case-insensitive)"
    )
    filter_group.add_argument(
        "--exclude-orgs",
        help="Comma-separated list of organization display names to exclude"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output",
        help="Custom filename for the CSV export (default: timestamped filename)"
    )
    output_group.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help=f"Directory for output files (default: {OUTPUT_DIR})"
    )
    
    # Processing options
    processing_group = parser.add_argument_group("Processing Options")
    processing_group.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Number of customers to process per page (default: {BATCH_SIZE})"
    )
    processing_group.add_argument(
        "--max-workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Number of parallel workers for org details (default: {MAX_WORKERS})"
    )
    processing_group.add_argument(
        "--delay",
        type=float,
        default=RATE_LIMIT_DELAY,
        help=f"Delay between API calls in seconds (default: {RATE_LIMIT_DELAY})"
    )
    
    # Additional options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def get_wholesale_customers(args: argparse.Namespace = None) -> List[Dict[str, Any]]:
    """
    Retrieve wholesale customers from the Webex API with proper offset-based pagination and API-level filtering.
    
    Args:
        args (argparse.Namespace, optional): Command line arguments for filtering
    
    Returns:
        List[Dict[str, Any]]: List of wholesale customers
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    all_customers = []
    offset = 0
    
    try:
        # Build base parameters
        base_params = {
            "max": BATCH_SIZE if args is None else args.batch_size,
        }
        
        # Add API-level filters if specified
        if args:
            if args.org_ids:
                # For single orgId, use the orgId parameter
                org_ids = [org_id.strip() for org_id in args.org_ids.split(',')]
                if len(org_ids) == 1:
                    base_params["orgId"] = org_ids[0]
                    print(f"Using API filter: orgId = {org_ids[0]}")
                else:
                    print("Note: Multiple orgIds specified, will fetch all and filter locally")
            
            if args.external_ids:
                # For single externalId, use the externalId parameter
                external_ids = [ext_id.strip() for ext_id in args.external_ids.split(',')]
                if len(external_ids) == 1:
                    base_params["externalId"] = external_ids[0]
                    print(f"Using API filter: externalId = {external_ids[0]}")
                else:
                    print("Note: Multiple externalIds specified, will fetch all and filter locally")
            
            if args.status:
                base_params["status"] = args.status
                print(f"Using API filter: status = {args.status}")
        
        filter_description = "all customers"
        filter_parts = []
        if "orgId" in base_params:
            filter_parts.append(f"orgId {base_params['orgId']}")
        if "externalId" in base_params:
            filter_parts.append(f"externalId {base_params['externalId']}")
        if "status" in base_params:
            filter_parts.append(f"status {base_params['status']}")
        
        if filter_parts:
            filter_description = f"customers with {', '.join(filter_parts)}"
        
        print(f"Fetching {filter_description} with offset-based pagination...")
        
        while True:
            # Build URL with pagination parameters using offset
            url = f"{API_BASE_URL}/wholesale/customers"
            params = base_params.copy()
            params["offset"] = offset
            
            print(f"Fetching customers with offset {offset} (max {params['max']})...")
            
            response = requests.get(url, headers=get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            
            customers = data.get("items", [])
            if not customers:
                print("No more customers found. Pagination complete.")
                break
                
            all_customers.extend(customers)
            print(f"Retrieved {len(customers)} customers (total: {len(all_customers)})")
            
            # Check if we got fewer customers than requested (last page)
            if len(customers) < params["max"]:
                print("Reached last page of results.")
                break
            
            # Update offset for next page
            offset += len(customers)
            
            # Rate limiting
            delay = RATE_LIMIT_DELAY if args is None else args.delay
            time.sleep(delay)
            
        print(f"Total wholesale customers retrieved: {len(all_customers)}")
        return all_customers
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling List Wholesale Customers API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise

def get_organization_details(org_id: str) -> Optional[Dict[str, Any]]:
    """
    Get organization details by org ID to retrieve the display name.
    
    Args:
        org_id (str): The organization ID
        
    Returns:
        Optional[Dict[str, Any]]: Organization details or None if failed
    """
    url = f"{API_BASE_URL}/organizations/{org_id}"
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting for parallel requests
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not retrieve org details for {org_id}: {e}")
        return None

def get_organization_details_parallel(customers: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Get organization details for multiple customers in parallel.
    
    Args:
        customers (List[Dict[str, Any]]): List of customers
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping org_id to org details
    """
    org_details_map = {}
    unique_org_ids = set()
    
    # Collect unique org IDs
    for customer in customers:
        org_id = customer.get('orgId')
        if org_id:
            unique_org_ids.add(org_id)
    
    if not unique_org_ids:
        print("No organization IDs found in customers.")
        return org_details_map
    
    print(f"Fetching organization details for {len(unique_org_ids)} unique organizations using {MAX_WORKERS} parallel workers...")
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_org_id = {
            executor.submit(get_organization_details, org_id): org_id
            for org_id in unique_org_ids
        }
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_org_id):
            org_id = future_to_org_id[future]
            completed += 1
            
            try:
                org_details = future.result()
                if org_details:
                    org_details_map[org_id] = org_details
                    print(f"✓ Retrieved org details for {org_id} ({completed}/{len(unique_org_ids)})")
                else:
                    print(f"✗ Failed to retrieve org details for {org_id} ({completed}/{len(unique_org_ids)})")
                    
            except Exception as e:
                print(f"✗ Exception retrieving org details for {org_id}: {e} ({completed}/{len(unique_org_ids)})")
    
    print(f"Successfully retrieved organization details for {len(org_details_map)}/{len(unique_org_ids)} organizations")
    return org_details_map

def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary for CSV export.
    
    Args:
        data (Dict[str, Any]): The dictionary to flatten
        parent_key (str): The parent key for nested items
        sep (str): Separator for nested keys
        
    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # Convert lists to comma-separated strings
            items.append((new_key, ', '.join(str(item) for item in value)))
        else:
            items.append((new_key, value))
    
    return dict(items)

def apply_early_filters(customers: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Apply filtering that can be done before fetching org details (for multiple values that couldn't be done at API level).
    
    Args:
        customers (List[Dict[str, Any]]): List of customer data
        args (argparse.Namespace): Command line arguments
        
    Returns:
        List[Dict[str, Any]]: Filtered list of customers
    """
    filtered_customers = customers.copy()
    original_count = len(filtered_customers)
    
    # Apply multiple orgId filtering (when API couldn't handle it)
    if args.org_ids and ',' in args.org_ids:
        org_ids = [org_id.strip() for org_id in args.org_ids.split(',')]
        filtered_customers = [
            customer for customer in filtered_customers
            if customer.get('orgId', '').strip() in org_ids
        ]
        print(f"Local filter by organization IDs: {len(filtered_customers)} customers match")
    
    # Apply multiple externalId filtering (when API couldn't handle it)
    if args.external_ids and ',' in args.external_ids:
        external_ids = [ext_id.strip() for ext_id in args.external_ids.split(',')]
        filtered_customers = [
            customer for customer in filtered_customers
            if customer.get('externalId', '').strip() in external_ids
        ]
        print(f"Local filter by external IDs: {len(filtered_customers)} customers match")
    
    if len(filtered_customers) != original_count:
        print(f"Local filtering: {original_count} → {len(filtered_customers)} customers")
    
    return filtered_customers

def apply_post_org_filters(customers_data: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Apply organization filtering that requires org details (display name-based filtering).
    
    Args:
        customers_data (List[Dict[str, Any]]): List of customer data with org details
        args (argparse.Namespace): Command line arguments
        
    Returns:
        List[Dict[str, Any]]: Filtered list of customers
    """
    filtered_customers = customers_data.copy()
    original_count = len(filtered_customers)
    
    # Apply display name-based filters (these require org details to be fetched first)
    if args.org_names:
        org_names = [name.strip() for name in args.org_names.split(',')]
        filtered_customers = [
            customer for customer in filtered_customers
            if customer.get('org_displayName', '').strip() in org_names
        ]
        print(f"Filtered by organization names: {len(filtered_customers)} customers match")
    
    elif args.org_pattern:
        try:
            pattern = re.compile(args.org_pattern, re.IGNORECASE)
            filtered_customers = [
                customer for customer in filtered_customers
                if pattern.search(customer.get('org_displayName', ''))
            ]
            print(f"Filtered by pattern '{args.org_pattern}': {len(filtered_customers)} customers match")
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{args.org_pattern}': {e}")
    
    elif args.org_contains:
        search_text = args.org_contains.lower()
        filtered_customers = [
            customer for customer in filtered_customers
            if search_text in customer.get('org_displayName', '').lower()
        ]
        print(f"Filtered by contains '{args.org_contains}': {len(filtered_customers)} customers match")
    
    # Apply exclusion filter
    if args.exclude_orgs:
        exclude_names = [name.strip() for name in args.exclude_orgs.split(',')]
        before_exclude = len(filtered_customers)
        filtered_customers = [
            customer for customer in filtered_customers
            if customer.get('org_displayName', '').strip() not in exclude_names
        ]
        excluded_count = before_exclude - len(filtered_customers)
        print(f"Excluded {excluded_count} customers from specified organizations")
    
    if len(filtered_customers) != original_count:
        print(f"Post-org-details filtering: {original_count} → {len(filtered_customers)} customers")
    
    return filtered_customers

def export_to_csv(customers_data: List[Dict[str, Any]], filename: str = None, output_dir: str = OUTPUT_DIR) -> str:
    """
    Export customers data to a CSV file.
    
    Args:
        customers_data (List[Dict[str, Any]]): List of customer data with org details
        filename (str, optional): Custom filename for the CSV
        
    Returns:
        str: Path to the created CSV file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wholesale_customers_export_{timestamp}.csv"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    if not customers_data:
        print("No customer data to export.")
        return filepath
    
    # Flatten all customer data and collect all possible field names
    flattened_data = []
    all_fieldnames = set()
    
    for customer in customers_data:
        flattened_customer = flatten_dict(customer)
        flattened_data.append(flattened_customer)
        all_fieldnames.update(flattened_customer.keys())
    
    # Sort fieldnames for consistent column order
    fieldnames = sorted(all_fieldnames)
    
    # Write to CSV
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for customer in flattened_data:
                # Ensure all fields are present (fill missing with empty string)
                row = {field: customer.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"Successfully exported {len(customers_data)} customers to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        raise

def main():
    """
    Main function to run the script.
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print("Webex Wholesale Customers Export Script")
        print("=======================================")
        
        # Display filtering info if any filters are applied
        if any([args.org_names, args.org_ids, args.org_pattern, args.org_contains, args.exclude_orgs]):
            print("Filtering options:")
            if args.org_names:
                print(f"- Organization names: {args.org_names}")
            if args.org_ids:
                print(f"- Organization IDs: {args.org_ids}")
            if args.org_pattern:
                print(f"- Organization pattern: {args.org_pattern}")
            if args.org_contains:
                print(f"- Organization contains: {args.org_contains}")
            if args.exclude_orgs:
                print(f"- Excluded organizations: {args.exclude_orgs}")
            print()
        
        # Step 1: Get wholesale customers (with API-level filtering if applicable)
        customers = get_wholesale_customers(args)
        
        if not customers:
            print("No wholesale customers found.")
            return
        
        # Step 2: Apply any remaining local filters (for multiple values that couldn't be done at API level)
        if (args.org_ids and ',' in args.org_ids) or (args.external_ids and ',' in args.external_ids):
            print("\nApplying additional local filters...")
            customers = apply_early_filters(customers, args)
            
            if not customers:
                print("No customers match the specified filters.")
                return
        
        # Step 3: Enrich customer data with organization details using parallel processing
        print("\nFetching organization details using parallel processing...")
        org_details_map = get_organization_details_parallel(customers)
        
        # Enrich customer data with organization details
        print("\nEnriching customer data with organization details...")
        enriched_customers = []
        
        for i, customer in enumerate(customers, 1):
            if i % 50 == 0 or i == len(customers):
                print(f"Processing customer {i}/{len(customers)}")
            
            # Copy customer data
            enriched_customer = customer.copy()
            
            # Get organization details if orgId is available
            org_id = customer.get('orgId')
            if org_id and org_id in org_details_map:
                org_details = org_details_map[org_id]
                # Add display name and other org details
                enriched_customer['org_displayName'] = org_details.get('displayName', '')
                enriched_customer['org_details'] = org_details
            elif org_id:
                enriched_customer['org_displayName'] = 'Unable to retrieve'
            else:
                enriched_customer['org_displayName'] = 'No orgId available'
            
            enriched_customers.append(enriched_customer)
        
        # Step 4: Apply post-organization filters (display name-based) after fetching org details
        if any([args.org_names, args.org_pattern, args.org_contains, args.exclude_orgs]):
            print("\nApplying organization filters (by display name)...")
            enriched_customers = apply_post_org_filters(enriched_customers, args)
            
            if not enriched_customers:
                print("No customers match the specified filters.")
                return
        
        # Step 5: Export to CSV
        print("\nExporting data to CSV...")
        csv_path = export_to_csv(enriched_customers, args.output, args.output_dir)
        
        print(f"\nExport completed successfully!")
        print(f"CSV file created: {csv_path}")
        print(f"Total customers exported: {len(enriched_customers)}")
        
        # Step 5: Display summary
        print("\nSummary:")
        customers_with_org_names = sum(1 for c in enriched_customers
                                     if c.get('org_displayName') and
                                     c['org_displayName'] not in ['Unable to retrieve', 'No orgId available'])
        print(f"- Customers with organization names: {customers_with_org_names}")
        print(f"- Customers without organization names: {len(enriched_customers) - customers_with_org_names}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())