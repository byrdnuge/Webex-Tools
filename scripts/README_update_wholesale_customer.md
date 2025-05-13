# Webex Wholesale Customer Update Tool

A Python script for updating Webex Calling packages for wholesale customers.

## Overview

This tool allows you to:
- Search for Broadworks enterprises by name
- Select the correct customer from search results
- Update the customer's Webex Calling packages
- Configure address and provisioning parameters

The script uses two main API endpoints:
- List Broadworks Enterprises API: `https://webexapis.com/v1/broadworks/enterprises`
- Update Wholesale Customer API: `https://webexapis.com/v1/wholesale/customers/{customerId}`

## Installation

### Prerequisites
- Python 3.6+
- pip

### Setup
1. Install required dependencies:
   ```
   pip install requests python-dotenv
   ```

2. Create a `.env` file in the same directory as the script with your Webex API token:
   ```
   WEBEX_ACCESS_TOKEN=your_webex_api_token_here
   ```

## Usage

Run the script:
```
python update_wholesale_customer.py
```

### Interactive Workflow

The script will guide you through the following steps:

1. **Enter Broadworks Customer Name**
   - Enter the name of the Broadworks customer you want to update
   - The script will search for matching enterprises

2. **Select/Confirm Customer**
   - If multiple customers are found, you'll be presented with a numbered list to select from
   - If a single customer is found, you'll be asked to confirm it's the correct one
   - If no customers are found, you'll be prompted to try again

3. **Select Packages**
   - Choose from the available Webex Calling packages
   - You can enter package names or numbers (comma-separated)
   - Available packages:
     1. common_area_calling
     2. webex_calling
     3. webex_meetings
     4. webex_suite
     5. webex_voice
     6. cx_essentials
     7. webex_calling_standard
     8. cisco_calling_plan
     9. attendant_console

4. **Enter Address Details**
   - Address Line 1 (required)
   - Address Line 2 (optional)
   - City (required)
   - State/Province
   - ZIP/Postal Code
   - Country (2-letter code, required)

5. **Enter Additional Parameters**
   - Location Name (default: "Head Office")
   - Timezone (default: "America/Chicago")
   - Language (default: "en_us")
   - Emergency Location Identifier (optional)
   - External ID (UUID format, generated automatically if not provided)

6. **Verify and Confirm**
   - Review the complete request body
   - Confirm to proceed with the update or go back to make changes

7. **View Results**
   - The script will display the API response
   - The script will automatically check the status of the update
   - The full status details will be displayed

## Improved Search Functionality

The script uses a two-step approach to find Broadworks enterprises:

1. First, it tries an exact match using the full enterprise name
2. If no results are found, it falls back to a partial match using just the first word

This approach:
- Maximizes the chance of finding the correct customer
- Handles misspellings and partial matches gracefully
- Avoids API errors from conflicting query parameters

## Example Session

```
Webex Wholesale Customer Update Script
=====================================
Enter the name of the Broadworks customer: Acme

Searching for Broadworks enterprise: Acme
Trying exact match with enterprise name: Acme

Found the following customers:
1. spEnterpriseId: Reseller1+acme
   ID: Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvOTZhYmMyYWEtM2RjYy0xMWU1LWExNTItZmUzNDgxOWNkYzlh
   Org ID: Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi85NmFiYzJhYS0zZGNjLTExZTUtYTE1Mi1mZTM0ODE5Y2RjOWE

Is this the correct customer? (y/n): y

Selected customer: Reseller1+acme
Customer ID: Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvOTZhYmMyYWEtM2RjYy0xMWU1LWExNTItZmUzNDgxOWNkYzlh
Org ID: Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi85NmFiYzJhYS0zZGNjLTExZTUtYTE1Mi1mZTM0ODE5Y2RjOWE

Available packages:
1. common_area_calling
2. webex_calling
3. webex_meetings
4. webex_suite
5. webex_voice
6. cx_essentials
7. webex_calling_standard
8. cisco_calling_plan
9. attendant_console

Enter the packages to add (comma-separated list or numbers): 1,2,4,5

Selected packages:
- common_area_calling
- webex_calling
- webex_suite
- webex_voice

Is this correct? (y/n): y

Enter address details:
Address Line 1: 123 Main Street
Address Line 2 (optional): Suite 100
City: San Francisco
State/Province: CA
ZIP/Postal Code: 94105
Country (2-letter code, e.g., US): US

Enter additional parameters:
Location Name (default: Head Office): Headquarters
Timezone (default: America/Chicago): America/Los_Angeles
Language (default: en_us): 
Emergency Location Identifier (optional): 12345

The external ID must be in UUID format (e.g., f5b36187-c8dd-4727-8b2f-f9c447f29046)
External ID (press Enter to use generated UUID): 
Using generated UUID: f5b36187-c8dd-4727-8b2f-f9c447f29046

Request body:
{
  "externalId": "f5b36187-c8dd-4727-8b2f-f9c447f29046",
  "packages": [
    "common_area_calling",
    "webex_calling",
    "webex_suite",
    "webex_voice"
  ],
  "address": {
    "addressLine1": "123 Main Street",
    "addressLine2": "Suite 100",
    "city": "San Francisco",
    "stateOrProvince": "CA",
    "zipOrPostalCode": "94105",
    "country": "US"
  },
  "provisioningParameters": {
    "calling": {
      "location": {
        "name": "Headquarters",
        "address": {
          "addressLine1": "123 Main Street",
          "addressLine2": "Suite 100",
          "city": "San Francisco",
          "stateOrProvince": "CA",
          "zipOrPostalCode": "94105",
          "country": "US"
        },
        "timezone": "America/Los_Angeles",
        "language": "en_us",
        "emergencyLocationIdentifier": "12345"
      }
    }
  }
}

Is this correct? Do you want to proceed with the update? (y/n): y

Sending update request...

Update request sent successfully!
Response: {
  "url": "https://webexapis.com/v1/wholesale/customers/Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvOTZhYmMyYWEtM2RjYy0xMWU1LWExNTItZmUzNDgxOWNkYzlh"
}

Checking status at: https://webexapis.com/v1/wholesale/customers/Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvOTZhYmMyYWEtM2RjYy0xMWU1LWExNTItZmUzNDgxOWNkYzlh

Current status:
{
  "id": "Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvOTZhYmMyYWEtM2RjYy0xMWU1LWExNTItZmUzNDgxOWNkYzlh",
  "externalId": "f5b36187-c8dd-4727-8b2f-f9c447f29046",
  "status": "COMPLETED",
  "packages": [
    "common_area_calling",
    "webex_calling",
    "webex_suite",
    "webex_voice"
  ],
  "address": {
    "addressLine1": "123 Main Street",
    "addressLine2": "Suite 100",
    "city": "San Francisco",
    "stateOrProvince": "CA",
    "zipOrPostalCode": "94105",
    "country": "US"
  },
  "provisioningParameters": {
    "calling": {
      "location": {
        "name": "Headquarters",
        "address": {
          "addressLine1": "123 Main Street",
          "addressLine2": "Suite 100",
          "city": "San Francisco",
          "stateOrProvince": "CA",
          "zipOrPostalCode": "94105",
          "country": "US"
        },
        "timezone": "America/Los_Angeles",
        "language": "en_us",
        "emergencyLocationIdentifier": "12345"
      }
    }
  }
}
```

## External ID Handling

The script handles the `externalId` field in the following way:

1. The user is prompted to enter an external ID in UUID format
2. If the user doesn't provide one, a random UUID is generated automatically
3. If the user provides an invalid UUID, the script warns them and uses a generated UUID instead

This approach ensures that the `externalId` is always in the correct format (UUID) as required by the API, while giving users the flexibility to specify their own ID if needed.

## Troubleshooting

### Common Issues

#### Authentication Errors
- **Error**: "WEBEX_ACCESS_TOKEN not found in environment variables"
  - **Solution**: Create a `.env` file with your API token or set the environment variable manually

- **Error**: "401 Unauthorized"
  - **Solution**: Check that your API token is valid and has the necessary permissions

#### API Errors
- **Error**: "No customers found"
  - **Solution**: Verify the customer name and try again with different search terms. The script will automatically try a partial match if an exact match fails.

- **Error**: "400 Bad Request"
  - **Solution**: Check the request body for any formatting issues or missing required fields

#### Input Validation
- **Error**: "No valid packages selected"
  - **Solution**: Ensure you're entering valid package names or numbers

- **Error**: "Country is required and must be a 2-letter code"
  - **Solution**: Enter a valid 2-letter country code (e.g., US, CA, UK)

## API Reference

### List Broadworks Enterprises API
- **Endpoint**: `GET https://webexapis.com/v1/broadworks/enterprises`
- **Query Parameters**:
  - `spEnterpriseId`: The name of the Broadworks enterprise
  - `startsWith`: Search for enterprises starting with this string
  - `max`: Maximum number of results to return

### Update Wholesale Customer API
- **Endpoint**: `PUT https://webexapis.com/v1/wholesale/customers/{customerId}`
- **Path Parameters**:
  - `customerId`: The ID of the customer to update
- **Request Body**:
  - `externalId`: External ID of the Wholesale customer
  - `packages`: List of Webex Wholesale packages
  - `address`: Billing address of the customer
  - `provisioningParameters`: Parameters for provisioning

For more information, see the [Webex API documentation](https://developer.webex.com/docs/api/v1/wholesale-provisioning/update-a-wholesale-customer).
