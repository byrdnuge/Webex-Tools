#!/usr/bin/env python3
"""
Wholesale Customer Status Checker

This script checks the status of wholesale customer update operations using the status URLs
from the execution report. It includes proper authentication headers for the Webex API.

Usage:
    python check_wholesale_customer_status.py [status_url]
    
    If no URL is provided, it will prompt for input or read from a file.
"""

import requests
import json
import os
import sys
from dotenv import load_dotenv
import time
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def get_api_token():
    """Get the Webex API token from environment variables."""
    token = os.getenv('WEBEX_ACCESS_TOKEN') or os.getenv('WEBEX_API_TOKEN')
    if not token:
        raise ValueError("WEBEX_ACCESS_TOKEN or WEBEX_API_TOKEN not found in environment variables")
    
    # Strip quotes if present
    return token.strip('"\'')

def check_status_url(status_url, token):
    """Check the status of a wholesale customer operation."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"Checking status: {status_url}")
        response = requests.get(status_url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Response:")
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                print("Response (text):")
                print(response.text)
        else:
            print(f"Error: {response.status_code}")
            print("Response:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def extract_status_urls_from_report(report_file):
    """Extract status URLs from an execution report file."""
    status_urls = []
    
    try:
        with open(report_file, 'r') as f:
            for line in f:
                if 'Status URL:' in line:
                    url = line.split('Status URL: ')[1].strip()
                    status_urls.append(url)
    except FileNotFoundError:
        print(f"Report file not found: {report_file}")
        return []
    
    return status_urls

def main():
    try:
        token = get_api_token()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    if len(sys.argv) > 1:
        # Status URL provided as argument
        status_url = sys.argv[1]
        check_status_url(status_url, token)
    else:
        # Interactive mode
        print("Wholesale Customer Status Checker")
        print("=" * 40)
        print("Options:")
        print("1. Check a single status URL")
        print("2. Check all status URLs from execution report")
        print("3. Check only successful status URLs from execution report")
        print("4. Check only failed/error status URLs from execution report")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            status_url = input("Enter status URL: ").strip()
            if status_url:
                check_status_url(status_url, token)
        
        elif choice == "2":
            report_file = input("Enter execution report file path (or press Enter for latest): ").strip()
            if not report_file:
                # Find the latest execution report
                import glob
                reports = glob.glob("output/wholesale_customer_external_id_update_execution_*.txt")
                if reports:
                    report_file = max(reports)
                    print(f"Using latest report: {report_file}")
                else:
                    print("No execution reports found in output/ directory")
                    return 1
            
            status_urls = extract_status_urls_from_report(report_file)
            print(f"Found {len(status_urls)} status URLs")
            
            for i, url in enumerate(status_urls, 1):
                print(f"\n--- Checking {i}/{len(status_urls)} ---")
                check_status_url(url, token)
                if i < len(status_urls):
                    time.sleep(1)  # Rate limiting
        
        elif choice == "3":
            report_file = input("Enter execution report file path (or press Enter for latest): ").strip()
            if not report_file:
                # Find the latest execution report
                import glob
                reports = glob.glob("output/wholesale_customer_external_id_update_execution_*.txt")
                if reports:
                    report_file = max(reports)
                    print(f"Using latest report: {report_file}")
                else:
                    print("No execution reports found in output/ directory")
                    return 1
            
            # Extract only successful status URLs
            successful_urls = []
            try:
                with open(report_file, 'r') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if '✓' in line and 'API Response: Success' in line:
                            # Look for the status URL in the next few lines
                            for j in range(i+1, min(i+5, len(lines))):
                                if 'Status URL:' in lines[j]:
                                    url = lines[j].split('Status URL: ')[1].strip()
                                    successful_urls.append(url)
                                    break
            except FileNotFoundError:
                print(f"Report file not found: {report_file}")
                return 1
            
            print(f"Found {len(successful_urls)} successful status URLs")
            
            for i, url in enumerate(successful_urls, 1):
                print(f"\n--- Checking successful operation {i}/{len(successful_urls)} ---")
                check_status_url(url, token)
                if i < len(successful_urls):
                    time.sleep(1)  # Rate limiting
        
        elif choice == "4":
            report_file = input("Enter execution report file path (or press Enter for latest): ").strip()
            if not report_file:
                # Find the latest execution report
                import glob
                reports = glob.glob("output/wholesale_customer_external_id_update_execution_*.txt")
                if reports:
                    report_file = max(reports)
                    print(f"Using latest report: {report_file}")
                else:
                    print("No execution reports found in output/ directory")
                    return 1
            
            # Extract only failed status URLs
            failed_urls = []
            try:
                with open(report_file, 'r') as f:
                    lines = f.readlines()
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        # Look for failed entries (marked with ✗)
                        if '✗' in line and '(ID:' in line:
                            customer_info = line
                            # Look for the status URL in the next few lines
                            for j in range(i+1, min(i+10, len(lines))):
                                if 'Status URL:' in lines[j]:
                                    url = lines[j].split('Status URL:')[1].strip()
                                    failed_urls.append({
                                        'url': url,
                                        'customer': customer_info
                                    })
                                    break
                                elif lines[j].strip() and (lines[j].strip()[0].isdigit() and '.' in lines[j].strip()[:5]):
                                    # Next customer entry
                                    break
                        i += 1
            except FileNotFoundError:
                print(f"Report file not found: {report_file}")
                return 1
            
            print(f"Found {len(failed_urls)} failed status URLs")
            
            for i, entry in enumerate(failed_urls, 1):
                print(f"\n--- Checking failed operation {i}/{len(failed_urls)} ---")
                print(f"Customer: {entry['customer']}")
                check_status_url(entry['url'], token)
                if i < len(failed_urls):
                    time.sleep(1)  # Rate limiting
        
        else:
            print("Invalid choice")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())