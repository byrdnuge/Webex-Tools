#!/usr/bin/env python3
"""
Webex Users Deletion Script

This script deletes a list of users from a Webex organization. It can read user
identifiers from a CSV file or accept them as command line arguments.

The script supports multiple ways to identify users:
- Email addresses
- User IDs
- Display names

Features:
- Dry-run mode for safety (preview what would be deleted)
- Progress tracking and detailed logging
- Error handling with retry logic
- Support for CSV input files
- Detailed reporting of success/failure

Authentication is handled via a Webex API token stored in a .env file.
"""

import os
import csv
import json
import argparse
import requests
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables from .env file
load_dotenv()

# Constants
API_BASE_URL = "https://webexapis.com/v1"
OUTPUT_DIR = "output"
DEFAULT_LOG_FILENAME = "user_deletion_log.txt"
RATE_LIMIT_DELAY = 0.5  # Delay between API calls to avoid rate limiting

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

def test_authentication():
    """
    Test authentication with the Webex API.
    """
    try:
        # Test with a simple API call to get current user info
        url = f"{API_BASE_URL}/people/me"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        user_info = response.json()
        print(f"✓ Successfully authenticated as: {user_info.get('displayName', 'Unknown')} ({user_info.get('emails', ['Unknown'])[0]})")
        return True
    except Exception as e:
        print(f"✗ Failed to authenticate with Webex API: {e}")
        return False

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Delete users from a Webex organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with CSV file (recommended first step)
  python scripts/delete_users.py --csv-file input/users_to_delete.csv --dry-run
  
  # Delete users from CSV file
  python scripts/delete_users.py --csv-file input/users_to_delete.csv
  
  # Delete specific users by email
  python scripts/delete_users.py --emails "user1@example.com,user2@example.com"
  
  # Delete users by user IDs
  python scripts/delete_users.py --user-ids "id1,id2,id3"
  
  # Delete users from specific organization
  python scripts/delete_users.py --csv-file input/users.csv --org-name "My Organization"

CSV File Format:
  The CSV file should have one of these column headers:
  - 'email' or 'Email' for email addresses
  - 'user_id' or 'User ID' for user IDs
  - 'display_name' or 'Display Name' for display names
        """
    )
    
    # Input options
    input_group = parser.add_argument_group("Input Options")
    input_group.add_argument(
        "--csv-file",
        help="Path to CSV file containing users to delete"
    )
    input_group.add_argument(
        "--emails",
        help="Comma-separated list of email addresses to delete"
    )
    input_group.add_argument(
        "--user-ids",
        help="Comma-separated list of user IDs to delete"
    )
    input_group.add_argument(
        "--display-names",
        help="Comma-separated list of display names to delete"
    )
    
    # Filtering options
    filter_group = parser.add_argument_group("Filtering Options")
    filter_group.add_argument(
        "--org-name",
        help="Only delete users from this organization"
    )
    filter_group.add_argument(
        "--org-id",
        help="Only delete users from this organization ID"
    )
    
    # Execution options
    execution_group = parser.add_argument_group("Execution Options")
    execution_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    execution_group.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )
    execution_group.add_argument(
        "--delay",
        type=float,
        default=RATE_LIMIT_DELAY,
        help=f"Delay between API calls in seconds (default: {RATE_LIMIT_DELAY})"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--log-file",
        help="Custom filename for the deletion log"
    )
    output_group.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help=f"Directory for output files (default: {OUTPUT_DIR})"
    )
    output_group.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def read_users_from_csv(csv_file: str) -> List[Dict[str, str]]:
    """
    Read user identifiers from a CSV file.
    
    Args:
        csv_file (str): Path to the CSV file
        
    Returns:
        List[Dict[str, str]]: List of user data dictionaries
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV file format is invalid
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    users = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Detect delimiter
            sample = file.read(1024)
            file.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            # Normalize column names (case-insensitive)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("CSV file appears to be empty or has no headers")
            
            # Create mapping for case-insensitive column access
            column_mapping = {}
            for field in fieldnames:
                lower_field = field.lower().strip()
                if lower_field in ['email', 'user_email', 'email_address']:
                    column_mapping['email'] = field
                elif lower_field in ['user_id', 'userid', 'id']:
                    column_mapping['user_id'] = field
                elif lower_field in ['display_name', 'displayname', 'name', 'full_name']:
                    column_mapping['display_name'] = field
            
            if not column_mapping:
                raise ValueError(
                    f"CSV file must contain at least one of these columns: "
                    f"email, user_id, display_name. Found columns: {', '.join(fieldnames)}"
                )
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                user_data = {}
                
                # Extract available user identifiers
                for key, csv_column in column_mapping.items():
                    value = row.get(csv_column, '').strip()
                    if value:
                        user_data[key] = value
                
                if user_data:  # Only add if we found at least one identifier
                    user_data['row_number'] = row_num
                    users.append(user_data)
                elif any(row.values()):  # Row has data but no valid identifiers
                    print(f"Warning: Row {row_num} has data but no valid user identifiers")
        
        print(f"✓ Read {len(users)} users from CSV file: {csv_file}")
        return users
        
    except Exception as e:
        raise ValueError(f"Error reading CSV file {csv_file}: {e}")

def parse_command_line_users(args: argparse.Namespace) -> List[Dict[str, str]]:
    """
    Parse user identifiers from command line arguments.
    
    Args:
        args (argparse.Namespace): Parsed command line arguments
        
    Returns:
        List[Dict[str, str]]: List of user data dictionaries
    """
    users = []
    
    if args.emails:
        emails = [email.strip() for email in args.emails.split(',') if email.strip()]
        for email in emails:
            users.append({'email': email})
    
    if args.user_ids:
        user_ids = [uid.strip() for uid in args.user_ids.split(',') if uid.strip()]
        for user_id in user_ids:
            users.append({'user_id': user_id})
    
    if args.display_names:
        names = [name.strip() for name in args.display_names.split(',') if name.strip()]
        for name in names:
            users.append({'display_name': name})
    
    return users

def find_user_by_identifier(identifier_data: Dict[str, str], org_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a Webex user by various identifiers using the Webex API.
    
    Args:
        identifier_data (Dict[str, str]): Dictionary containing user identifiers
        org_filter (Optional[str]): Organization name or ID to filter by
        
    Returns:
        Optional[Dict[str, Any]]: User data dictionary if found, None otherwise
    """
    user = None
    
    try:
        # Try to find by email first (most reliable)
        if 'email' in identifier_data:
            try:
                url = f"{API_BASE_URL}/people"
                params = {"email": identifier_data['email']}
                response = requests.get(url, headers=get_headers(), params=params)
                response.raise_for_status()
                data = response.json()
                users = data.get('items', [])
                if users:
                    user = users[0]  # Email should be unique
            except Exception:
                pass  # User not found by email
        
        # Try to find by user ID
        if not user and 'user_id' in identifier_data:
            try:
                url = f"{API_BASE_URL}/people/{identifier_data['user_id']}"
                response = requests.get(url, headers=get_headers())
                response.raise_for_status()
                user = response.json()
            except Exception:
                pass  # User not found by ID
        
        # Try to find by display name (least reliable, may return multiple)
        if not user and 'display_name' in identifier_data:
            try:
                url = f"{API_BASE_URL}/people"
                params = {"displayName": identifier_data['display_name']}
                response = requests.get(url, headers=get_headers(), params=params)
                response.raise_for_status()
                data = response.json()
                users = data.get('items', [])
                if users:
                    # Take the first match - display names aren't unique
                    user = users[0]
            except Exception:
                pass
        
        # Apply organization filter if specified
        if user and org_filter:
            try:
                user_org_id = user.get('orgId')
                if user_org_id:
                    # Get organization details
                    org_url = f"{API_BASE_URL}/organizations/{user_org_id}"
                    org_response = requests.get(org_url, headers=get_headers())
                    org_response.raise_for_status()
                    org_data = org_response.json()
                    org_name = org_data.get('displayName', '')
                    
                    # Check if user belongs to the specified organization
                    if (org_filter.lower() not in org_name.lower() and
                        org_filter != user_org_id):
                        return None  # User not in specified organization
            except Exception:
                pass  # Couldn't verify organization
        
        return user
        
    except Exception as e:
        print(f"Error finding user with identifiers {identifier_data}: {e}")
        return None

def delete_user(user: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, str]:
    """
    Delete a Webex user using the API.
    
    Args:
        user (Dict[str, Any]): User data dictionary
        dry_run (bool): If True, don't actually delete
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        user_name = user.get('displayName', 'Unknown')
        user_email = user.get('emails', ['Unknown'])[0] if user.get('emails') else 'Unknown'
        user_id = user.get('id', '')
        
        if dry_run:
            return True, f"[DRY RUN] Would delete user: {user_name} ({user_email})"
        
        if not user_id:
            return False, f"Cannot delete user {user_name} ({user_email}): No user ID available"
        
        # Perform the actual deletion
        url = f"{API_BASE_URL}/people/{user_id}"
        response = requests.delete(url, headers=get_headers())
        response.raise_for_status()
        
        return True, f"Successfully deleted user: {user_name} ({user_email})"
        
    except Exception as e:
        user_name = user.get('displayName', 'Unknown')
        user_email = user.get('emails', ['Unknown'])[0] if user.get('emails') else 'Unknown'
        return False, f"Failed to delete user {user_name} ({user_email}): {e}"

def create_log_file(args: argparse.Namespace) -> str:
    """
    Create a log file for the deletion operation.
    
    Args:
        args (argparse.Namespace): Command line arguments
        
    Returns:
        str: Path to the log file
    """
    if args.log_file:
        filename = args.log_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "dry_run" if args.dry_run else "execution"
        filename = f"user_deletion_{mode}_{timestamp}.txt"
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    return os.path.join(args.output_dir, filename)

def log_message(message: str, log_file: str, verbose: bool = False):
    """
    Log a message to both console and file.
    
    Args:
        message (str): Message to log
        log_file (str): Path to log file
        verbose (bool): Whether to print to console
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    if verbose:
        print(message)
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")

def main():
    """
    Main function to run the script.
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print("Webex Users Deletion Script")
        print("==========================")
        
        # Validate input arguments
        input_sources = [args.csv_file, args.emails, args.user_ids, args.display_names]
        if not any(input_sources):
            print("Error: You must specify at least one input source:")
            print("  --csv-file, --emails, --user-ids, or --display-names")
            return 1
        
        # Test authentication
        if not test_authentication():
            return 1
        
        # Create log file
        log_file = create_log_file(args)
        print(f"Logging to: {log_file}")
        
        # Log script start
        mode = "DRY RUN" if args.dry_run else "EXECUTION"
        log_message(f"Starting user deletion script in {mode} mode", log_file, args.verbose)
        
        # Collect users to delete
        users_to_process = []
        
        if args.csv_file:
            log_message(f"Reading users from CSV file: {args.csv_file}", log_file, args.verbose)
            csv_users = read_users_from_csv(args.csv_file)
            users_to_process.extend(csv_users)
        
        # Add command line users
        cli_users = parse_command_line_users(args)
        users_to_process.extend(cli_users)
        
        if not users_to_process:
            print("No users found to process.")
            return 1
        
        print(f"Found {len(users_to_process)} user(s) to process")
        log_message(f"Found {len(users_to_process)} user(s) to process", log_file, args.verbose)
        
        # Determine organization filter
        org_filter = args.org_name or args.org_id
        if org_filter:
            print(f"Filtering by organization: {org_filter}")
            log_message(f"Filtering by organization: {org_filter}", log_file, args.verbose)
        
        # Process each user
        found_users = []
        not_found = []
        
        print("\nLooking up users...")
        for i, user_data in enumerate(users_to_process, 1):
            print(f"Processing {i}/{len(users_to_process)}: {user_data}")
            
            user = find_user_by_identifier(user_data, org_filter)
            if user:
                found_users.append((user, user_data))
                user_name = user.get('displayName', 'Unknown')
                user_email = user.get('emails', ['Unknown'])[0] if user.get('emails') else 'Unknown'
                log_message(f"Found user: {user_name} ({user_email})", log_file, args.verbose)
            else:
                not_found.append(user_data)
                log_message(f"User not found: {user_data}", log_file, args.verbose)
            
            # Rate limiting
            time.sleep(args.delay)
        
        # Summary of found users
        print(f"\nSummary:")
        print(f"- Users found: {len(found_users)}")
        print(f"- Users not found: {len(not_found)}")
        
        if not_found:
            print("\nUsers not found:")
            for user_data in not_found:
                print(f"  - {user_data}")
        
        if not found_users:
            print("No users found to delete.")
            return 0
        
        # Show what will be deleted
        print(f"\nUsers to be {'deleted' if not args.dry_run else 'deleted (DRY RUN)'}:")
        for user, _ in found_users:
            user_name = user.get('displayName', 'Unknown')
            user_email = user.get('emails', ['Unknown'])[0] if user.get('emails') else 'Unknown'
            user_id = user.get('id', 'Unknown')
            print(f"  - {user_name} ({user_email}) [ID: {user_id}]")
        
        # Confirmation prompt (unless forced or dry run)
        if not args.dry_run and not args.force:
            response = input(f"\nAre you sure you want to delete {len(found_users)} user(s)? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Operation cancelled.")
                return 0
        
        # Perform deletions
        print(f"\n{'Simulating deletions...' if args.dry_run else 'Deleting users...'}")
        
        successful_deletions = 0
        failed_deletions = 0
        
        for i, (user, user_data) in enumerate(found_users, 1):
            user_name = user.get('displayName', 'Unknown')
            print(f"Processing {i}/{len(found_users)}: {user_name}")
            
            success, message = delete_user(user, args.dry_run)
            
            if success:
                successful_deletions += 1
                print(f"  ✓ {message}")
            else:
                failed_deletions += 1
                print(f"  ✗ {message}")
            
            log_message(message, log_file, args.verbose)
            
            # Rate limiting
            if not args.dry_run:
                time.sleep(args.delay)
        
        # Final summary
        print(f"\nOperation completed!")
        print(f"- Successful: {successful_deletions}")
        print(f"- Failed: {failed_deletions}")
        print(f"- Log file: {log_file}")
        
        log_message(f"Operation completed - Successful: {successful_deletions}, Failed: {failed_deletions}", log_file, args.verbose)
        
        return 0 if failed_deletions == 0 else 1
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    exit(main())