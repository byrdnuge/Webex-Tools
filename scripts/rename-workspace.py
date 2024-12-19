import csv
import requests
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Fetch the Webex API access token from the .env file
access_token = os.getenv("WEBEX_ACCESS_TOKEN")
if not access_token:
    raise ValueError("WEBEX_ACCESS_TOKEN is not set in the .env file.")

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

def rename_workspace(old_name, new_name):
    # Get the workspace ID by old name
    response = requests.get(f'https://webexapis.com/v1/workspaces?displayName={old_name}', headers=headers)
    if response.status_code == 200:
        workspaces = response.json().get('items', [])
        if workspaces:
            workspace_id = workspaces[0]['id']
            # Rename the workspace
            rename_response = requests.put(f'https://webexapis.com/v1/workspaces/{workspace_id}', headers=headers, json={'displayName': new_name})
            if rename_response.status_code == 200:
                print(f'Successfully renamed workspace from {old_name} to {new_name}')
            else:
                print(f'Failed to rename workspace {old_name}: {rename_response.text}')
        else:
            print(f'Workspace with name {old_name} not found')
    else:
        print(f'Failed to get workspace {old_name}: {response.text}')

def main():
    csv_file = '/Users/jbergoon/PycharmProjects/WebexTools/input/workspaces.csv'  # Use the absolute path
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            old_name, new_name = row
            rename_workspace(old_name, new_name)

if __name__ == "__main__":
    main()