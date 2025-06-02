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

def get_wholesale_customers() -> List[Dict[str, Any]]:
    """
    Retrieve all wholesale customers from the Webex API with proper offset-based pagination.
    
    Returns:
        List[Dict[str, Any]]: List of wholesale customers
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    all_customers = []
    offset = 0
    
    try:
        print("Fetching wholesale customers with offset-based pagination...")
        
        while True:
            # Build URL with pagination parameters using offset
            url = f"{API_BASE_URL}/wholesale/customers"
            params = {
                "max": BATCH_SIZE,
                "offset": offset
            }
            
            print(f"Fetching customers with offset {offset} (max {BATCH_SIZE})...")
            
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
            if len(customers) < BATCH_SIZE:
                print("Reached last page of results.")
                break
            
            # Update offset for next page
            offset += len(customers)
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
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

def export_to_csv(customers_data: List[Dict[str, Any]], filename: str = None) -> str:
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
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
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
    print("Webex Wholesale Customers Export Script")
    print("=======================================")
    
    try:
        # Step 1: Get all wholesale customers
        customers = get_wholesale_customers()
        
        if not customers:
            print("No wholesale customers found.")
            return
        
        # Step 2: Enrich customer data with organization details using parallel processing
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
        
        # Step 3: Export to CSV
        print("\nExporting data to CSV...")
        csv_path = export_to_csv(enriched_customers)
        
        print(f"\nExport completed successfully!")
        print(f"CSV file created: {csv_path}")
        print(f"Total customers exported: {len(enriched_customers)}")
        
        # Step 4: Display summary
        print("\nSummary:")
        customers_with_org_names = sum(1 for c in enriched_customers 
                                     if c.get('org_displayName') and 
                                     c['org_displayName'] not in ['Unable to retrieve', 'No orgId available'])
        print(f"- Customers with organization names: {customers_with_org_names}")
        print(f"- Customers without organization names: {len(enriched_customers) - customers_with_org_names}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()