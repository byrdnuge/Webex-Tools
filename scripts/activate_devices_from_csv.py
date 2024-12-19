import os
import csv
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Fetch the Webex API access token from the .env file
ACCESS_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")
WEBEX_API_BASE_URL = "https://webexapis.com/v1"

if not ACCESS_TOKEN:
    raise ValueError("WEBEX_ACCESS_TOKEN is not set in the .env file.")


def get_person_id(email):
    """
    Fetch the personId for a specific email from the Webex API.
    """
    try:
        url = f"{WEBEX_API_BASE_URL}/people"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        params = {"email": email}

        # Make the GET request to fetch person details
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for non-2xx status codes

        person_details = response.json().get("items", [])
        if len(person_details) == 0:
            raise ValueError(f"No person found with email: {email}")

        # Return the personId of the first match
        return person_details[0].get("id")

    except Exception as e:
        print(f"Error fetching personId for {email}: {e}")
        return None


def activate_device(person_id):
    """
    Generate an activation code for a Webex device using the person's personId.
    """
    try:
        url = f"{WEBEX_API_BASE_URL}/devices/activationCode"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {"personId": person_id}

        # Make the POST request to create an activation code
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx status codes

        # Parse and return the activation code and expiry time from the response
        response_json = response.json()
        activation_code = response_json.get("code")
        expiry_time = response_json.get("expiryTime")

        if not activation_code or not expiry_time:
            raise ValueError(f"Failed to get activation code or expiry time for personId: {person_id}")

        return activation_code, expiry_time, None  # Always return three values

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err.response.text}"
        print(error_message)
        return None, None, error_message
    except Exception as e:
        error_message = f"Error activating device for personId {person_id}: {e}"
        print(error_message)
        return None, None, error_message


def activate_devices_from_csv(input_csv, output_csv):
    """
    Activate devices for users listed in the input CSV file and save results to an output CSV file.
    Include error reporting for emails where activation fails.
    """
    with open(input_csv, mode='r') as infile, open(output_csv, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['email', 'activation_code', 'expiry_time', 'error']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            email = row['email']
            print(f"Processing email: {email}...")

            # Step 1: Retrieve the personId
            person_id = get_person_id(email)
            if not person_id:
                error_message = f"Missing personId for email: {email}"
                print(error_message)
                writer.writerow({
                    'email': email,
                    'activation_code': None,
                    'expiry_time': None,
                    'error': error_message
                })
                continue

            # Step 2: Generate and log the activation code and expiry time
            activation_code, expiry_time, error = activate_device(person_id) if person_id else (None, None, None)
            if activation_code and expiry_time:
                print(f"Activation code for {email}: {activation_code}")
                print(f"Expiry time: {expiry_time}")
                writer.writerow({
                    'email': email,
                    'activation_code': activation_code,
                    'expiry_time': expiry_time,
                    'error': None
                })
            else:
                error_message = error or f"Failed to generate activation code for email: {email}"
                print(error_message)
                writer.writerow({
                    'email': email,
                    'activation_code': None,
                    'expiry_time': None,
                    'error': error_message
                })


if __name__ == "__main__":
    # Input CSV file path (should contain a column named 'email')
    input_csv = "people_list.csv"
    # Output CSV file path
    output_csv = "activation_codes.csv"

    activate_devices_from_csv(input_csv, output_csv)
