import os
import requests
# import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Webex Staging Token from the .env file
ACCESS_TOKEN = os.getenv("WEBEX_STAGING_TOKEN")


# Function to retrieve all organizations with IDs and names
def get_all_organizations():
    url = "https://webexapis.com/v1/organizations"
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        orgs = response.json().get("items", [])
        return [{"id": org["id"], "displayName": org["displayName"]} for org in orgs]
    else:
        print(f"Error fetching organizations: {response.status_code}")
        print(response.text)
        return []


# Function to search for a specific phone number in an organization
def get_numbers_in_org(phone_number, org):
    org_id = org["id"]
    org_name = org["displayName"]

    url = "https://webexapis.com/v1/telephony/config/numbers"
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    params = {
        'orgId': org_id
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        phone_numbers = result.get("phoneNumbers", [])

        # Filter results to match the specific phone number, if it exists
        filtered_numbers = [
            {**num, "organizationName": org_name, "organizationId": org_id}  # Add orgName and orgId
            for num in phone_numbers if
            num.get("phoneNumber") == phone_number or phone_number in (num.get("extension", ""))
        ]
        return filtered_numbers
    else:
        print(f"Error searching in organization {org_name}: {response.status_code}")
        return []


# Search for the phone number across all organizations in parallel
def search_number_across_orgs(phone_number):
    organizations = get_all_organizations()
    if not organizations:
        print("No organizations found or an error occurred.")
        return []

    all_results = []

    with ThreadPoolExecutor() as executor:  # Uses default number of threads
       # print(f"Active threads count before starting: {threading.active_count()}")
        # Submit calls for all organizations
        future_to_org = {
            executor.submit(get_numbers_in_org, phone_number, org): org
            for org in organizations
        }

        # Process results as API calls complete
        for future in as_completed(future_to_org):
            # COMMENTED OUT: Dynamic thread debug monitoring for cleaner output
            # Uncomment the next line to enable thread monitoring during debugging
            # print(f"\r[Thread Monitor] Active threads: {threading.active_count()}", end='')
            try:
                org_results = future.result()

                # Aggregate results
                if org_results:
                    all_results.extend(org_results)
            except Exception as e:
                print(f"Error occurred: {e}")

   # print(f"\nActive threads count after execution: {threading.active_count()}")
    return all_results


# Function to display detailed results, excluding counts
def display_results(matching_numbers):
    if matching_numbers:
        for match in matching_numbers:
            print(f"Organization Name: {match.get('organizationName')}")
            print(f"Organization ID: {match.get('organizationId')}")
            print(f"Phone Number: {match.get('phoneNumber', 'N/A')}")
            print(f"Extension: {match.get('extension', 'N/A')}")
            print(f"Routing Prefix: {match.get('routingPrefix', 'N/A')}")
            print(f"ESN: {match.get('esn', 'N/A')}")
            print(f"Mobile Network: {match.get('mobileNetwork', 'N/A')}")
            print(f"Routing Profile: {match.get('routingProfile', 'N/A')}")
            print(f"State: {match.get('state', 'N/A')}")
            print(f"Phone Number Type: {match.get('phoneNumberType', 'N/A')}")
            print(f"Main Number: {match.get('mainNumber', 'N/A')}")
            print(f"Included Telephony Types: {match.get('includedTelephonyTypes', 'N/A')}")
            print(f"Toll-Free Number: {match.get('tollFreeNumber', 'N/A')}")
            print(f"Is Service Number: {match.get('isServiceNumber', 'N/A')}")
            # Location details
            location = match.get("location", {})
            print(f"Location ID: {location.get('id', 'N/A')}")
            print(f"Location Name: {location.get('name', 'N/A')}")
            # Owner details
            owner = match.get("owner", {})
            print(f"Owner ID: {owner.get('id', 'N/A')}")
            print(f"Owner First Name: {owner.get('firstName', 'N/A')}")
            print(f"Owner Last Name: {owner.get('lastName', 'N/A')}")
            print(f"Owner Type: {owner.get('type', 'N/A')}")
            print("---")
    else:
        print("No matching numbers found.")


# Main function
if __name__ == "__main__":
    phone_number_to_search = input(
        "Enter the phone number or extension to search (e.g., +12056350001 or 568): ").strip()
    matching_results = search_number_across_orgs(phone_number_to_search)

    print(f"\nResults for phone number/extension: {phone_number_to_search}")
    display_results(matching_results)
