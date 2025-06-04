#!/usr/bin/env python3
"""
Webex Wholesale Customer Update Script

This script allows you to update a wholesale customer with Webex Calling packages.
It provides an interactive interface to:
1. Search for a Broadworks enterprise by name
2. Select the correct customer from search results
3. Update the customer's Webex Calling packages
4. Configure address and provisioning parameters

The script uses two main API endpoints:
- List Broadworks Enterprises API: https://webexapis.com/v1/broadworks/enterprises
- Update Wholesale Customer API: https://webexapis.com/v1/wholesale/customers/{customerId}

Authentication is handled via a Webex API token stored in a .env file.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
API_BASE_URL = "https://webexapis.com/v1"
DEFAULT_TIMEZONE = "America/Chicago"
DEFAULT_LANGUAGE = "en_us"
AVAILABLE_PACKAGES = [
    "common_area_calling",
    "webex_calling",
    "webex_meetings",
    "webex_suite",
    "webex_voice",
    "cx_essentials",
    "webex_calling_standard",
    "cisco_calling_plan",
    "attendant_console"
]

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

def list_broadworks_enterprises(customer_name: str) -> Dict[str, Any]:
    """
    Call the List Broadworks Enterprises API to find enterprises by name.
    
    This function uses a two-step approach:
    1. First tries to find an exact match using the full enterprise name
    2. If no results are found, falls back to a partial match using the first word
    
    Args:
        customer_name (str): The name of the Broadworks customer to search for
        
    Returns:
        Dict[str, Any]: The API response
        
    Raises:
        requests.exceptions.RequestException: If both API requests fail
    """
    import urllib.parse
    
    # URL encode the customer name
    encoded_customer_name = urllib.parse.quote(customer_name)
    first_word = customer_name.split()[0] if customer_name else ""
    encoded_first_word = urllib.parse.quote(first_word)
    
    url = f"{API_BASE_URL}/broadworks/enterprises"
    
    # Step 1: Try with exact enterprise name first
    try:
        print(f"Trying exact match with enterprise name: {customer_name}")
        exact_match_url = f"{url}?spEnterpriseId={encoded_customer_name}&max=10"
        response = requests.get(exact_match_url, headers=get_headers())
        response.raise_for_status()
        result = response.json()
        
        # If we found results, return them
        if result.get("items", []):
            return result
            
        print("No exact matches found. Trying partial match...")
        
    except requests.exceptions.RequestException as e:
        print(f"Exact match query failed: {e}")
        print("Falling back to partial match...")
    
    # Step 2: If no results or error, try with startsWith parameter
    try:
        print(f"Trying partial match with first word: {first_word}")
        partial_match_url = f"{url}?startsWith={encoded_first_word}&max=10"
        response = requests.get(partial_match_url, headers=get_headers())
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling List Broadworks Enterprises API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise

def update_wholesale_customer(customer_id: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the Update Wholesale Customer API to update a customer.
    
    Args:
        customer_id (str): The ID of the customer to update
        request_body (Dict[str, Any]): The request body
        
    Returns:
        Dict[str, Any]: The API response
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    url = f"{API_BASE_URL}/wholesale/customers/{customer_id}"
    
    try:
        response = requests.put(url, headers=get_headers(), json=request_body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Update Wholesale Customer API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise

def get_customer_name() -> str:
    """
    Get the name of the Broadworks customer from user input.
    
    Returns:
        str: The customer name
    """
    while True:
        customer_name = input("Enter the name of the Broadworks customer: ").strip()
        if customer_name:
            return customer_name
        print("Customer name cannot be empty. Please try again.")

def select_customer(customers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Display a list of customers and let the user select one.
    
    Args:
        customers (List[Dict[str, Any]]): List of customers from the API response
        
    Returns:
        Optional[Dict[str, Any]]: The selected customer or None if selection failed
    """
    if not customers:
        print("No customers found.")
        return None
    
    print("\nFound the following customers:")
    for i, customer in enumerate(customers, 1):
        print(f"{i}. spEnterpriseId: {customer.get('spEnterpriseId', 'N/A')}")
        print(f"   ID: {customer.get('id', 'N/A')}")
        print(f"   Org ID: {customer.get('orgId', 'N/A')}")
        print()
    
    if len(customers) == 1:
        while True:
            confirm = input("Is this the correct customer? (y/n): ").strip().lower()
            if confirm == 'y':
                return customers[0]
            elif confirm == 'n':
                return None
            else:
                print("Please enter 'y' or 'n'.")
    else:
        while True:
            try:
                selection = int(input(f"Select a customer (1-{len(customers)}) or 0 to cancel: "))
                if selection == 0:
                    return None
                if 1 <= selection <= len(customers):
                    return customers[selection - 1]
                print(f"Please enter a number between 1 and {len(customers)} or 0 to cancel.")
            except ValueError:
                print("Please enter a valid number.")

def get_packages() -> List[str]:
    """
    Get the packages to add from user input.
    
    Returns:
        List[str]: List of package names
    """
    print("\nAvailable packages:")
    for i, package in enumerate(AVAILABLE_PACKAGES, 1):
        print(f"{i}. {package}")
    
    while True:
        packages_input = input("\nEnter the packages to add (comma-separated list or numbers): ").strip()
        if not packages_input:
            print("Package list cannot be empty. Please try again.")
            continue
        
        # Check if input contains numbers
        if all(part.strip().isdigit() for part in packages_input.split(',')):
            try:
                selected_indices = [int(part.strip()) for part in packages_input.split(',')]
                selected_packages = [AVAILABLE_PACKAGES[i-1] for i in selected_indices if 1 <= i <= len(AVAILABLE_PACKAGES)]
                
                if not selected_packages:
                    print("No valid packages selected. Please try again.")
                    continue
                
                print("\nSelected packages:")
                for package in selected_packages:
                    print(f"- {package}")
                
                confirm = input("\nIs this correct? (y/n): ").strip().lower()
                if confirm == 'y':
                    return selected_packages
                elif confirm == 'n':
                    continue
                else:
                    print("Please enter 'y' or 'n'.")
            except (ValueError, IndexError):
                print("Invalid package numbers. Please try again.")
        else:
            # Process as package names
            selected_packages = [pkg.strip() for pkg in packages_input.split(',')]
            valid_packages = [pkg for pkg in selected_packages if pkg in AVAILABLE_PACKAGES]
            invalid_packages = [pkg for pkg in selected_packages if pkg not in AVAILABLE_PACKAGES]
            
            if invalid_packages:
                print(f"Warning: The following packages are not recognized: {', '.join(invalid_packages)}")
            
            if not valid_packages:
                print("No valid packages selected. Please try again.")
                continue
            
            print("\nSelected packages:")
            for package in valid_packages:
                print(f"- {package}")
            
            confirm = input("\nIs this correct? (y/n): ").strip().lower()
            if confirm == 'y':
                return valid_packages
            elif confirm == 'n':
                continue
            else:
                print("Please enter 'y' or 'n'.")

def get_address_details() -> Dict[str, str]:
    """
    Get address details from user input.
    
    Returns:
        Dict[str, str]: Address details
    """
    print("\nEnter address details:")
    address = {}
    
    address["addressLine1"] = input("Address Line 1: ").strip()
    while not address["addressLine1"]:
        print("Address Line 1 is required.")
        address["addressLine1"] = input("Address Line 1: ").strip()
    
    address["addressLine2"] = input("Address Line 2 (optional): ").strip()
    if not address["addressLine2"]:
        del address["addressLine2"]
    
    address["city"] = input("City: ").strip()
    while not address["city"]:
        print("City is required.")
        address["city"] = input("City: ").strip()
    
    address["stateOrProvince"] = input("State/Province: ").strip()
    if not address["stateOrProvince"]:
        del address["stateOrProvince"]
    
    address["zipOrPostalCode"] = input("ZIP/Postal Code: ").strip()
    if not address["zipOrPostalCode"]:
        del address["zipOrPostalCode"]
    
    address["country"] = input("Country (2-letter code, e.g., US): ").strip()
    while not address["country"] or len(address["country"]) != 2:
        print("Country is required and must be a 2-letter code (e.g., US).")
        address["country"] = input("Country (2-letter code, e.g., US): ").strip()
    
    # No need to add extra quotes, the JSON serialization will handle this
    
    return address

def get_additional_parameters() -> Dict[str, str]:
    """
    Get additional parameters from user input.
    
    Returns:
        Dict[str, str]: Additional parameters
    """
    print("\nEnter additional parameters:")
    params = {}
    
    params["location_name"] = input(f"Location Name (default: Head Office): ").strip()
    if not params["location_name"]:
        params["location_name"] = "Head Office"
    
    params["timezone"] = input(f"Timezone (default: {DEFAULT_TIMEZONE}): ").strip()
    if not params["timezone"]:
        params["timezone"] = DEFAULT_TIMEZONE
    
    params["language"] = input(f"Language (default: {DEFAULT_LANGUAGE}): ").strip()
    if not params["language"]:
        params["language"] = DEFAULT_LANGUAGE
    
    emergency_location = input("Emergency Location Identifier (optional): ").strip()
    if emergency_location:
        params["emergency_location_identifier"] = emergency_location
    
    # Ask for external ID
    default_external_id = str(uuid.uuid4())
    print(f"\nThe external ID must be in UUID format (e.g., {default_external_id})")
    external_id = input(f"External ID (press Enter to use generated UUID): ").strip()
    if not external_id:
        external_id = default_external_id
        print(f"Using generated UUID: {external_id}")
    
    # Validate UUID format
    try:
        uuid.UUID(external_id)
        params["external_id"] = external_id
    except ValueError:
        print(f"Warning: The provided external ID is not a valid UUID. Using generated UUID: {default_external_id}")
        params["external_id"] = default_external_id
    
    return params

import uuid

def build_request_body(
    customer_data: Dict[str, Any],
    packages: List[str],
    address: Dict[str, str],
    additional_params: Dict[str, str]
) -> Dict[str, Any]:
    """
    Build the request body for the Update Wholesale Customer API.
    
    Args:
        customer_data (Dict[str, Any]): Customer data from the List Broadworks Enterprises API
        packages (List[str]): List of packages to add
        address (Dict[str, str]): Address details
        additional_params (Dict[str, str]): Additional parameters
        
    Returns:
        Dict[str, Any]: The request body
    """
    # Use the external ID provided by the user or generated in get_additional_parameters
    external_id = additional_params.get("external_id")
    
    print(f"Using external ID: {external_id}")
    
    # Build the request body
    request_body = {
        "externalId": external_id,
        "packages": packages,
        "address": address,
        "provisioningParameters": {
            "calling": {
                "location": {
                    "name": additional_params.get("location_name", "Head Office"),
                    "address": address,  # Reuse the same address
                    "timezone": additional_params.get("timezone", DEFAULT_TIMEZONE),
                    "language": additional_params.get("language", DEFAULT_LANGUAGE)
                }
            }
        }
    }
    
    # Add emergency location identifier if provided
    if "emergency_location_identifier" in additional_params:
        request_body["provisioningParameters"]["calling"]["location"]["emergencyLocationIdentifier"] = additional_params["emergency_location_identifier"]
    
    return request_body

def verify_request_body(request_body: Dict[str, Any]) -> bool:
    """
    Display the request body and ask the user to verify it.
    
    Args:
        request_body (Dict[str, Any]): The request body
        
    Returns:
        bool: True if verified, False otherwise
    """
    print("\nRequest body:")
    print(json.dumps(request_body, indent=2))
    
    while True:
        confirm = input("\nIs this correct? Do you want to proceed with the update? (y/n): ").strip().lower()
        if confirm == 'y':
            return True
        elif confirm == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'.")

def main():
    """
    Main function to run the script.
    """
    print("Webex Wholesale Customer Update Script")
    print("=====================================")
    
    try:
        # Step 1: Get customer name
        customer_name = get_customer_name()
        
        # Step 2: Call List Broadworks Enterprises API
        print(f"\nSearching for Broadworks enterprise: {customer_name}")
        response = list_broadworks_enterprises(customer_name)
        
        # Step 3: Select customer
        customers = response.get("items", [])
        customer = select_customer(customers)
        if not customer:
            print("Customer selection cancelled or no matching customer found.")
            return
        
        # Step 4: Extract customer ID
        customer_id = customer.get("id")
        if not customer_id:
            print("Error: Customer ID not found in the selected customer data.")
            return
        
        print(f"\nSelected customer: {customer.get('spEnterpriseId', 'Unknown')}")
        print(f"Customer ID: {customer_id}")
        print(f"Org ID: {customer.get('orgId', 'Unknown')}")
        
        # Step 5: Get packages
        packages = get_packages()
        
        # Step 6: Get address details
        address = get_address_details()
        
        # Step 7: Get additional parameters
        additional_params = get_additional_parameters()
        
        # Step 8: Build request body
        request_body = build_request_body(customer, packages, address, additional_params)
        
        # Step 9: Verify request body
        if not verify_request_body(request_body):
            print("Update cancelled.")
            return
        
        # Step 10: Send update request
        print("\nSending update request...")
        response = update_wholesale_customer(customer_id, request_body)
        
        print("\nUpdate request sent successfully!")
        print(f"Response: {json.dumps(response, indent=2)}")
        
        # Step 11: Check the status of the update
        status_url = response.get('url')
        if status_url:
            print(f"\nChecking status at: {status_url}")
            try:
                status_response = requests.get(status_url, headers=get_headers())
                status_response.raise_for_status()
                status_data = status_response.json()
                print("\nCurrent status:")
                print(json.dumps(status_data, indent=2))
            except requests.exceptions.RequestException as e:
                print(f"Error checking status: {e}")
                print(f"You can manually check the status at: {status_url}")
        else:
            print("\nNo status URL returned in the response.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
