# Webex Wholesale Customers Export Script

This script retrieves all wholesale customers from the Webex API and exports their information to a CSV spreadsheet. For each customer, it also fetches the organization details to get the human-readable display name.

## Overview

The script performs the following operations:
1. Fetches all wholesale customers using the Webex API with offset-based pagination
2. Retrieves organization details in parallel for all unique organization IDs
3. Enriches customer data with human-readable organization display names
4. Exports all data to a CSV file with timestamp
5. Provides a summary of the export operation

## Prerequisites

1. **Python Environment**: Python 3.6 or higher
2. **Dependencies**: Install required packages:
   ```bash
   pip install requests python-dotenv
   ```
3. **API Token**: A valid Webex API token with appropriate permissions

## Setup

1. **Environment Variables**: Create a `.env` file in the project root with your Webex API token:
   ```
   WEBEX_ACCESS_TOKEN=your_webex_api_token_here
   ```

2. **Permissions**: Ensure your API token has the following scopes:
   - `spark-admin:wholesale_customers_read` (for wholesale customers)
   - `spark-admin:organizations_read` (for organization details)

## Usage

Run the script from the project root directory:

```bash
python scripts/export_wholesale_customers.py
```

## Output

The script creates a CSV file in the `output/` directory with the following naming convention:
```
wholesale_customers_export_YYYYMMDD_HHMMSS.csv
```

### CSV Structure

The CSV includes all available fields from the wholesale customers API response, plus additional organization details:

- **Customer Fields**: All fields returned by the wholesale customers API (flattened)
- **Organization Fields**: 
  - `org_displayName`: Human-readable organization name
  - `org_details_*`: Additional organization details (flattened)

### Sample Output Columns

Common columns you can expect in the CSV:
- `id`: Customer ID
- `orgId`: Organization ID
- `externalId`: External customer identifier
- `status`: Customer status
- `packages`: Webex packages (comma-separated)
- `org_displayName`: Human-readable organization name
- `createdAt`: Customer creation timestamp
- `updatedAt`: Last update timestamp

## API Endpoints Used

1. **List Wholesale Customers**: `GET https://webexapis.com/v1/wholesale/customers`
   - Retrieves all wholesale customers
   - Handles pagination automatically

2. **Get Organization Details**: `GET https://webexapis.com/v1/organizations/{orgId}`
   - Retrieves organization details for each customer
   - Provides human-readable display names

## Features

### Offset-Based Pagination
The script uses proper offset-based pagination as specified in the Webex API documentation:
- Fetches customers in configurable batches (default: 100 per request)
- Uses `offset` parameter to navigate through pages
- Automatically detects when all customers have been retrieved

### Parallel Processing
Organization details are retrieved using parallel processing for maximum efficiency:
- Uses ThreadPoolExecutor with configurable worker threads (default: 10)
- Processes unique organization IDs only (eliminates duplicates)
- Includes rate limiting to respect API limits
- Real-time progress tracking with success/failure indicators

### Error Handling
- Graceful handling of API errors with detailed error messages
- Continues processing if individual organization details cannot be retrieved
- Provides warnings for failed organization lookups
- Comprehensive exception handling for network issues

### Data Flattening
Complex nested JSON structures are flattened for CSV compatibility:
- Nested objects become separate columns with underscore notation
- Arrays are converted to comma-separated strings

### Progress Tracking
The script provides real-time progress updates:
- Customer retrieval progress with offset tracking
- Parallel organization details lookup with completion counters
- Export summary with detailed statistics

### Performance Optimizations
- Configurable batch sizes for pagination
- Rate limiting to prevent API throttling
- Parallel processing for organization details
- Efficient memory usage with streaming processing

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   ```
   WEBEX_ACCESS_TOKEN not found in environment variables
   ```
   - Ensure your `.env` file exists and contains the correct token

2. **Permission Denied**:
   ```
   Response status code: 403
   ```
   - Verify your API token has the required scopes
   - Check if your token has wholesale customer access permissions

3. **Rate Limiting**:
   ```
   Response status code: 429
   ```
   - The script may need to be modified to include rate limiting delays
   - Consider running during off-peak hours

### Debug Information

The script provides detailed error information including:
- HTTP status codes
- Response body content
- Specific API endpoints that failed

## Example Output

```
Webex Wholesale Customers Export Script
=======================================
Fetching wholesale customers with offset-based pagination...
Fetching customers with offset 0 (max 100)...
Retrieved 100 customers (total: 100)
Fetching customers with offset 100 (max 100)...
Retrieved 50 customers (total: 150)
Reached last page of results.
Total wholesale customers retrieved: 150

Fetching organization details using parallel processing...
Fetching organization details for 45 unique organizations using 10 parallel workers...
✓ Retrieved org details for org-12345 (1/45)
✓ Retrieved org details for org-67890 (2/45)
✗ Failed to retrieve org details for org-99999 (3/45)
...
Successfully retrieved organization details for 43/45 organizations

Enriching customer data with organization details...
Processing customer 150/150

Exporting data to CSV...
Successfully exported 150 customers to: output/wholesale_customers_export_20250602_124500.csv

Export completed successfully!
CSV file created: output/wholesale_customers_export_20250602_124500.csv
Total customers exported: 150

Summary:
- Customers with organization names: 145
- Customers without organization names: 5
```

## Configuration

You can modify the following constants in the script to adjust performance:

```python
MAX_WORKERS = 10          # Number of parallel threads for org details
BATCH_SIZE = 100          # Number of customers to process per page
RATE_LIMIT_DELAY = 0.1    # Delay between requests (seconds)
```

## Notes

- The script creates the `output/` directory automatically if it doesn't exist
- Large customer lists may take several minutes to process due to individual organization API calls
- The CSV file uses UTF-8 encoding to support international characters
- Empty or missing fields are represented as empty strings in the CSV

## Related Scripts

- [`update_wholesale_customer.py`](update_wholesale_customer.py): Update wholesale customer configurations
- Other Webex API scripts in the `scripts/` directory