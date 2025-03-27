import wxcadm
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Fetch the Webex API access token from the .env file
access_token = os.getenv("WEBEX_ACCESS_TOKEN")
if not access_token:
    raise ValueError("WEBEX_ACCESS_TOKEN is not set in the .env file.")

# Set the access token for wxcadm
wxcadm.set_access_token(access_token)

def get_users_by_org_name(org_name):
    try:
        org = wxcadm.get_organization_by_name(org_name)
        users = wxcadm.get_users_by_organization(org.id)
        return users
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_users_by_email(email):
    try:
        user = wxcadm.get_user_by_email(email)
        org = wxcadm.get_organization_by_id(user.organization_id)
        users = wxcadm.get_users_by_organization(org.id)
        return users
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    org_name = input("Enter the organization name: ")
    email = input("Enter the email address: ")

    if org_name:
        users = get_users_by_org_name(org_name)
        if users:
            print(f"Users in organization '{org_name}':")
            for user in users:
                print(f"- {user.name} ({user.email})")
        else:
            print(f"No users found for organization '{org_name}'.")

    if email:
        users = get_users_by_email(email)
        if users:
            print(f"Users in the same organization as '{email}':")
            for user in users:
                print(f"- {user.name} ({user.email})")
        else:
            print(f"No users found for email '{email}'.")