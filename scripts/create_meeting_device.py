import csv
import requests
import pandas as pd
from dotenv import load_dotenv
import os
import json

# Load environment variables from a .env file
load_dotenv()

# Fetch the Webex API access token from the .env file
ACCESS_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")
WEBEX_BASE_URL = "https://webexapis.com/v1"

if not ACCESS_TOKEN:
    raise ValueError("WEBEX_ACCESS_TOKEN is not set in the .env file.")


def create_workspace(display_name, org_id, capacity, type_, calling, calendar, hotdesking_status, device_hosted_meetings, workspace_location_id):
    """Create a workspace in Webex."""
    url = f"{WEBEX_BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "displayName": display_name,
        "orgId": org_id,
        "capacity": capacity,
        "type": type_,
        "calling": calling,
        "calendar": calendar,
        "hotdeskingStatus": hotdesking_status,
        "deviceHostedMeetings": device_hosted_meetings,
        "workspaceLocationId": workspace_location_id
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

    if response.status_code == 200:
        response_data = response.json()
        return response_data.get("code"), response_data.get("expiryTime")  # Return activation code and expiry time
    else:
        print(f"Error assigning device to workspace '{workspace_id}'. Status Code: {response.status_code} - {response.json()}")
        return None, None


def process_csv(input_csv, output_csv):
    """Process input CSV to create workspaces and assign devices, saving the results in output CSV."""
    data = pd.read_csv(input_csv)
    results = []

    for _, row in data.iterrows():
        display_name = row["displayName"]
        org_id = row["orgId"]
        location_id = row["LocationID"]
        capacity = row["capacity"]
        type_ = row["type"]
        calling = json.loads(row["calling"]) if pd.notna(row["calling"]) else None
        calendar = json.loads(row["calendar"]) if pd.notna(row["calendar"]) else None
        hotdesking_status = row["hotdeskingStatus"]
        device_hosted_meetings = json.loads(row["deviceHostedMeetings"]) if pd.notna(row["deviceHostedMeetings"]) else None

        try:
            workspace_id = create_workspace(display_name, org_id, capacity, type_, calling, calendar, hotdesking_status, device_hosted_meetings, location_id)
            if workspace_id:
                activation_code, expiry_time = assign_device_to_workspace(workspace_id, org_id)
                results.append({
                    "displayName": display_name,
                    "workspaceId": workspace_id,
                    "activationCode": activation_code,
                    "expiryTime": expiry_time
                })
            else:
                print(f"Failed to create workspace for '{display_name}'")
        except Exception as e:
            print(f"Failed to process row for '{display_name}': {e}")

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    input_csv = "/Users/jbergoon/PycharmProjects/WebexTools/input/deviceinputmeet.csv"
    output_csv = "/Users/jbergoon/PycharmProjects/WebexTools/output/meeting_activation_results.csv"
    process_csv(input_csv, output_csv)
