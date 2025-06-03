# Webex Wholesale Customers Export Script

This script retrieves all wholesale customers from the Webex API and exports their information to a CSV spreadsheet. For each customer, it also fetches the organization details to get the human-readable display name.

## Overview

The script performs the following operations:
1. Applies API-level filtering for maximum efficiency (orgId, externalId, status)
2. Fetches filtered wholesale customers using offset-based pagination
3. Retrieves organization details in parallel for unique organization IDs
4. Applies additional display name-based filtering if specified
5. Enriches customer data with human-readable organization display names
6. Exports filtered data to a CSV file with custom or timestamped filename
7. Provides detailed summary with filtering statistics

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

### Basic Usage

```bash
# Export all customers
python scripts/export_wholesale_customers.py
```

### API-Level Filtering (Most Efficient)

```bash
# Export single organization by ID (ultra-fast)
python scripts/export_wholesale_customers.py --org-ids "Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8zZTE5OGUzZC0zNzY1LTQ3YjAtYmYwZi0yNzQ5OTc4ZTUyNmM"

# Export by external ID
python scripts/export_wholesale_customers.py --external-ids "1037704546"

# Export by customer status
python scripts/export_wholesale_customers.py --status "provisioned"

# Export multiple organizations (API + local filtering)
python scripts/export_wholesale_customers.py --org-ids "org1,org2,org3"
```

### Display Name-Based Filtering

```bash
# Export organizations by exact names
python scripts/export_wholesale_customers.py --org-names "Velvet Lab,Acme Corp"

# Export organizations matching pattern
python scripts/export_wholesale_customers.py --org-pattern ".*Lab.*"

# Export organizations containing text
python scripts/export_wholesale_customers.py --org-contains "velvet"

# Exclude specific organizations
python scripts/export_wholesale_customers.py --exclude-orgs "Test Corp,Demo Inc"
```

### Custom Output Options

```bash
# Custom filename and directory
python scripts/export_wholesale_customers.py --output "my_export.csv" --output-dir "reports/"

# Performance tuning
python scripts/export_wholesale_customers.py --batch-size 50 --max-workers 5 --delay 0.2
```

### Command Line Options

```bash
python scripts/export_wholesale_customers.py --help
```

**Organization Filtering:**
- `--org-ids`: Organization IDs (API-level filtering for single ID)
- `--external-ids`: External IDs (API-level filtering for single ID)
- `--status`: Customer status - provisioning, provisioned, error
- `--org-names`: Exact organization display names
- `--org-pattern`: Regex pattern for organization names
- `--org-contains`: Substring search in organization names
- `--exclude-orgs`: Organizations to exclude

**Output Options:**
- `--output`: Custom filename
- `--output-dir`: Output directory (default: output/)

**Performance Options:**
- `--batch-size`: Customers per API request (default: 100)
- `--max-workers`: Parallel threads for org details (default: 10)
- `--delay`: Rate limiting delay in seconds (default: 0.1)
- `--verbose`: Detailed logging

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
   - **Query Parameters**: `orgId`, `externalId`, `status`, `max`, `offset`
   - **API-Level Filtering**: Supports direct filtering by organization ID, external ID, and status
   - **Pagination**: Offset-based pagination with configurable batch sizes
   - **Performance**: Dramatically reduces data transfer when filtering is applied

2. **Get Organization Details**: `GET https://webexapis.com/v1/organizations/{orgId}`
   - **Purpose**: Retrieves organization details for human-readable display names
   - **Optimization**: Only called for unique organization IDs
   - **Parallel Processing**: Multiple requests processed concurrently

## Features

### 🚀 **API-Level Filtering (Maximum Performance)**
Revolutionary performance improvement using Webex API query parameters:
- **Organization ID**: Direct API filtering by `orgId` parameter
- **External ID**: Direct API filtering by `externalId` parameter
- **Status**: Direct API filtering by customer status
- **Performance Impact**: Instead of downloading 2,654 customers and filtering locally, directly retrieves only matching customers
- **Example**: Single organization query retrieves 1 customer instead of 2,654

### 🎯 **Smart Two-Stage Filtering**
Intelligent filtering strategy for maximum efficiency:
1. **API-Level**: Applied at Webex API (orgId, externalId, status)
2. **Post-Processing**: Applied after org details (display name filters)

### 🔍 **Advanced Organization Filtering**
Comprehensive filtering options for precise customer selection:
- **Exact Names**: `--org-names` for specific organization matches
- **Pattern Matching**: `--org-pattern` with full regex support
- **Substring Search**: `--org-contains` for case-insensitive text matching
- **Exclusion**: `--exclude-orgs` to filter out unwanted organizations

### ⚡ **High-Performance Architecture**
- **Offset-Based Pagination**: Proper API pagination with configurable batch sizes
- **Parallel Processing**: ThreadPoolExecutor for organization details (10 workers default)
- **Rate Limiting**: Configurable delays to respect API limits
- **Memory Efficient**: Streaming processing for large datasets

### 🛡️ **Robust Error Handling**
- **Token Validation**: Automatic quote stripping and validation
- **Graceful Failures**: Continues processing after individual errors
- **Detailed Logging**: Comprehensive error messages with HTTP status codes
- **Network Resilience**: Timeout and retry logic for API calls

### 📊 **Flexible Output Options**
- **Custom Filenames**: User-defined output filenames
- **Directory Control**: Configurable output directories
- **Data Flattening**: Nested JSON structures flattened for CSV compatibility
- **UTF-8 Support**: International character support

### 🔧 **Performance Tuning**
- **Configurable Batch Sizes**: Optimize API request sizes
- **Worker Thread Control**: Adjust parallel processing capacity
- **Rate Limit Tuning**: Fine-tune API call delays
- **Progress Tracking**: Real-time status with ✓/✗ indicators

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

### API-Level Filtering (Single Organization)
```
Webex Wholesale Customers Export Script
=======================================
Filtering options:
- Organization IDs: Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8zZTE5OGUzZC0zNzY1LTQ3YjAtYmYwZi0yNzQ5OTc4ZTUyNmM

Using API filter: orgId = Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8zZTE5OGUzZC0zNzY1LTQ3YjAtYmYwZi0yNzQ5OTc4ZTUyNmM
Fetching customers for orgId Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8zZTE5OGUzZC0zNzY1LTQ3YjAtYmYwZi0yNzQ5OTc4ZTUyNmM with offset-based pagination...
Fetching customers with offset 0 (max 100)...
Retrieved 1 customers (total: 1)
Reached last page of results.
Total wholesale customers retrieved: 1

Fetching organization details using parallel processing...
Fetching organization details for 1 unique organizations using 10 parallel workers...
✓ Retrieved org details for Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8zZTE5OGUzZC0zNzY1LTQ3YjAtYmYwZi0yNzQ5OTc4ZTUyNmM (1/1)
Successfully retrieved organization details for 1/1 organizations

Enriching customer data with organization details...
Processing customer 1/1

Exporting data to CSV...
Successfully exported 1 customers to: output/velvet_lab_export.csv

Export completed successfully!
CSV file created: output/velvet_lab_export.csv
Total customers exported: 1

Summary:
- Customers with organization names: 1
- Customers without organization names: 0
```

### All Customers Export
```
Webex Wholesale Customers Export Script
=======================================
Fetching all customers with offset-based pagination...
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
Successfully exported 150 customers to: output/wholesale_customers_export_20250603_164500.csv

Export completed successfully!
CSV file created: output/wholesale_customers_export_20250603_164500.csv
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

- [`update_wholesale_customer_external_ids.py`](update_wholesale_customer_external_ids.py): Batch update external IDs from CSV export
- [`update_wholesale_customer.py`](update_wholesale_customer.py): Interactive single customer updates
- Other Webex API scripts in the `scripts/` directory

## Performance Comparison

### Before API-Level Filtering
```
Total API Calls: 2,654 (customer list) + 45 (org details) = 2,699 calls
Data Transfer: ~2,654 customer records
Processing Time: ~5-10 minutes
```

### After API-Level Filtering (Single Organization)
```
Total API Calls: 1 (filtered customer list) + 1 (org details) = 2 calls
Data Transfer: ~1 customer record
Processing Time: ~5-10 seconds
```

**Performance Improvement: 99.9% reduction in API calls and processing time!**