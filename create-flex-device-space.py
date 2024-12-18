import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Webex API access token
ACCESS_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")
if not ACCESS_TOKEN:
    raise ValueError("Webex API access token is not found in the .env file.")

# Webex API base URL
WEBEX_BASE_URL = "https://webexapis.com/v1"


def create_workspace(display_name, org_id, location_id, type_, calling, calendar, hotdesking_status):
    """Create a workspace via the Webex API."""
    # Validate calendar and hotdesking status
    if hotdesking_status == "on" and calendar.get("type") != "none":
        print(
            f"Invalid request: 'hotdeskingStatus' and 'calendar' are both active for '{display_name}'. Adjusting 'calendar'...")
        calendar = {"type": "none"}  # Ensure calendar is disabled when hotdesking is on.

    url = f"{WEBEX_BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "displayName": display_name,
        "orgId": org_id,
        "workspaceLocationId": location_id,
        "type": type_,
        "capacity": "1",  # Assuming capacity is always 1 unless otherwise specified
        "calling": calling,
        "calendar": calendar,
        "hotdeskingStatus": hotdesking_status,
        "deviceHostedMeetings": {"enabled": "false"}
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()["id"]  # Return the workspace ID
    else:
        print(f"Error creating workspace '{display_name}'. Status Code: {response.status_code} - {response.json()}")
        response.raise_for_status()


def assign_device_to_workspace(workspace_id, org_id):
    """Assign a device to the workspace and create an activation code."""
    url = f"{WEBEX_BASE_URL}/devices/activationCode?orgId={org_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"workspaceId": workspace_id}

    response = requests.post(url, headers=headers, json=payload)

    # Status code 200 indicates success
    if response.status_code == 200:
        response_data = response.json()
        return response_data.get("code"), response_data.get("expiryTime")  # Return activation code and expiry time
    else:
        # If the response code is anything other than 200, log the issue
        print(f"Error assigning device to workspace '{workspace_id}'. "
              f"Status Code: {response.status_code} - {response.json()}")
        return None, None


def process_csv(input_csv, output_csv):
    """Process input CSV to create workspaces and assign devices, saving the results in output CSV."""
    # Read input CSV
    data = pd.read_csv(input_csv)

    # Prepare results list
    results = []

    # Process each row in the CSV
    for _, row in data.iterrows():
        display_name = row["displayName"]
        org_id = row["orgId"]
        location_id = row["LocationID"]
        type_ = row["type"]

        # Parse nested JSON fields for "calling" and "calendar"
        calling = eval(row["calling"]) if pd.notna(row["calling"]) else None  # Parse calling configuration
        calendar = eval(row["calendar"]) if pd.notna(row["calendar"]) else None  # Parse calendar configuration

        hotdesking_status = row["hotdeskingStatus"]

        try:
            # Step 1: Create the workspace
            print(f"Creating workspace '{display_name}'...")
            workspace_id = create_workspace(display_name, org_id, location_id, type_, calling, calendar,
                                            hotdesking_status)
            print(f"Workspace '{display_name}' created with ID: {workspace_id}")

            # Step 2: Assign a device and get activation code
            print(f"Assigning device to workspace '{display_name}'...")
            activation_code, expiry_time = assign_device_to_workspace(workspace_id, org_id)

            # Step 3: Append result to results list
            if activation_code and expiry_time:
                print(
                    f"Device assigned to workspace '{display_name}'. Activation Code: {activation_code}, Expiry Time: {expiry_time}"
                )
                results.append({
                    "displayName": display_name,
                    "workspaceId": workspace_id,
                    "activationCode": activation_code,
                    "expiryTime": expiry_time
                })
            else:
                print(f"Failed to assign device to workspace '{display_name}'.")

        except Exception as e:
            print(f"Error processing workspace '{display_name}': {e}")

    # Save results to output CSV
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv, index=False)
        print(f"Results written to {output_csv}")
    else:
        print("No results to write. Check errors above.")


# Main execution
if __name__ == "__main__":
    # Define input and output CSV file paths
    input_csv = "deviceinput.csv"  # Example input CSV
    output_csv = "output.csv"  # Output file to store results

    # Execute processing
    process_csv(input_csv, output_csv)
