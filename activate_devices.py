## This doesn't work right now
#
# import os
import csv
import time
import logging
from dotenv import load_dotenv
import wxcadm

# Set up logging for troubleshooting
logging.basicConfig(level=logging.INFO,
                    filename="./device_activation.log",
                    format='%(asctime)s %(levelname)s: %(message)s')

# Load the Webex API Access Token from environment variables
load_dotenv()
ACCESS_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERROR: WEBEX_ACCESS_TOKEN not found in the environment. Exiting.")
    exit(1)


def initialize_webex(org_id=None):
    """
    Initialize the Webex API client and return the target organization based on the provided Org ID.
    :param org_id: The Org ID to use for activation.
    """
    try:
        webex = wxcadm.Webex(ACCESS_TOKEN, get_locations=False)

        # Display available organizations if org_id is not provided
        if not org_id:
            print("Available Organizations:")
            for org in webex.orgs:
                print(f"Name: {org.name}, ID: {org.id}")
            org_id = input("\nEnter the Org ID to use: ").strip()

        # Find the target organization by ID
        target_org = next((org for org in webex.orgs if org.id == org_id), None)
        if not target_org:
            raise Exception(f"Organization with ID '{org_id}' not found.")

        print(f"Using organization: {target_org.name} (ID: {target_org.id})")
        return webex, target_org

    except wxcadm.TokenError as e:
        logging.error("Invalid or expired access token.")
        raise Exception("Invalid or expired Webex API Access Token.") from e


def generate_device_activation_code(target_org, email):
    """
    Generate an activation code for a Webex device associated with a user.
    """
    try:
        # Retrieve the user by email within the target organization
        user = target_org.people.get_by_email(email)
        if not user:
            logging.warning(f"No user found with email: {email}")
            return None

        # Generate activation code via devices API
        activation_code = target_org.devices.create_activation_code(user_id=user.id)
        return activation_code
    except Exception as e:
        logging.error(f"Failed to generate activation code for {email}: {e}")
        return None


def activate_devices_from_csv(input_csv, output_csv):
    """
    Read email addresses from input CSV, generate activation codes, and save to output CSV.
    """
    try:
        # Prompt user to select an Org ID
        webex, target_org = initialize_webex()
        print("Webex API Initialized. Generating activation codes...")
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

    with open(input_csv, mode='r') as infile, open(output_csv, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['email', 'activationCode']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            email = row.get('email', '').strip()
            if not email:
                logging.warning("Skipping row with missing email.")
                continue

            print(f"Generating activation code for {email}...")
            activation_code = generate_device_activation_code(target_org, email)
            if activation_code:
                writer.writerow({'email': email, 'activationCode': activation_code})
                print(f"Activation code for {email}: {activation_code}")
            else:
                print(f"Failed to generate activation code for {email}")


if __name__ == "__main__":
    INPUT_CSV = "people_list.csv"  # Input file with user emails
    OUTPUT_CSV = "activation_codes.csv"  # Output file to save activation codes

    print("Starting Device Activation Script...")
    start_time = time.time()
    activate_devices_from_csv(INPUT_CSV, OUTPUT_CSV)
    print("Script complete.")
    print(f"Total Execution Time: {round(time.time() - start_time, 2)} seconds.")