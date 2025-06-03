# Webex Wholesale Customer External ID Batch Update Script

This script updates external IDs for wholesale customers by reading from a CSV export and using the Update Wholesale Customer API. It replaces the existing `externalId` with the `customerId` value for each customer while preserving all other customer data.

## Overview

The script performs the following operations:
1. Loads customer data from a CSV export file
2. Applies optional organization filtering
3. Validates customer data for required fields
4. Updates external IDs using the Webex Update Wholesale Customer API
5. Generates detailed reports of the results

## Features

### **🔄 Dual Operation Modes**
- **Dry Run Mode** (`--dry-run`): Preview changes without making API calls
- **Execute Mode** (`--execute`): Perform actual API updates with validation

### **🎯 Advanced Organization Filtering**
- **Exact Name Matching**: `--org-names "Org1,Org2"`
- **Pattern Matching**: `--org-pattern ".*Lab.*"` (full regex support)
- **Substring Matching**: `--org-contains "velvet"` (case-insensitive)
- **Exclusion Filtering**: `--exclude-orgs "Test Corp,Demo Inc"`

### **⚡ High-Performance Batch Processing**
- **Parallel Processing**: Configurable worker threads with `--batch-size`
- **Rate Limiting**: Smart delays with `--delay` to respect API limits
- **Progress Tracking**: Real-time status with ✓/✗ indicators
- **Resume Capability**: Continue from specific customer with `--resume-from`

### **🛡️ Enhanced Security & Validation**
- **Token Validation**: Pre-flight API token verification
- **Data Validation**: Comprehensive CSV field validation
- **Error Recovery**: Graceful handling of individual failures
- **Authentication Fix**: Automatic quote stripping from .env tokens

### **📊 Comprehensive Reporting**
- **Timestamped Reports**: Detailed success/failure logs
- **Statistics**: Complete processing metrics
- **Error Details**: Specific troubleshooting information
- **Preview Reports**: Dry-run change summaries

## Prerequisites

1. **Python Environment**: Python 3.6 or higher
2. **Dependencies**: All required packages are already in [`requirements.txt`](../requirements.txt)
3. **API Token**: Valid Webex API token with wholesale customer permissions

## Setup

1. **Environment Variables**: Ensure your `.env` file contains:
   ```
   WEBEX_ACCESS_TOKEN=your_webex_api_token_here
   ```

2. **Permissions**: Your API token must have these scopes:
   - `spark-admin:wholesale_customers_write` (for updating customers)
   - `spark-admin:wholesale_customers_read` (for validation)

## Usage

### Basic Commands

```bash
# Dry run to preview all changes
python scripts/update_wholesale_customer_external_ids.py --dry-run --input input/customers.csv

# Execute updates for all customers
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv
```

### Organization Filtering

```bash
# Update specific organizations by exact name
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --org-names "Velvet Lab,Acme Corp"

# Update organizations matching a pattern
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --org-pattern ".*Lab.*"

# Update organizations containing specific text
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --org-contains "velvet"

# Update all except specific organizations
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --exclude-orgs "Test Corp,Demo Inc"
```

### Performance Tuning

```bash
# Custom batch size and delay for rate limiting
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --batch-size 3 --delay 0.5

# Verbose logging for detailed output
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --verbose

# Custom output directory for reports
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --output-dir reports/
```

## Command Line Options

### Required Arguments
- `--input PATH`: Path to the CSV file containing customer data
- `--dry-run` OR `--execute`: Operation mode (mutually exclusive)

### Organization Filtering
- `--org-names NAMES`: Comma-separated exact organization names
- `--org-pattern REGEX`: Regex pattern for organization names
- `--org-contains TEXT`: Organizations containing this text (case-insensitive)
- `--exclude-orgs NAMES`: Organizations to exclude

### Processing Options
- `--batch-size N`: Parallel processing batch size (default: 5)
- `--delay SECONDS`: Delay between API calls (default: 0.2)
- `--output-dir PATH`: Report output directory (default: output/)

### Additional Options
- `--verbose`: Enable detailed logging
- `--resume-from ID`: Resume from specific customer ID

## CSV File Format

The script expects a CSV file with the following columns (as exported by [`export_wholesale_customers.py`](export_wholesale_customers.py)):

### Required Columns
- `id`: Webex customer ID for API calls
- `customerId`: Value to use as new external ID
- `org_details_displayName`: Organization display name
- `packages`: Comma-separated package names
- `address_addressLine1`: Primary address line
- `address_city`: City
- `address_country`: Country code (e.g., "US")

### Optional Columns
- `externalId`: Current external ID (for reporting)
- `address_addressLine2`: Secondary address line
- `address_stateOrProvince`: State or province
- `address_zipOrPostalCode`: ZIP or postal code

## API Endpoint Used

**Update Wholesale Customer**: `PUT https://webexapis.com/v1/wholesale/customers/{customerId}`

The script constructs complete API requests including:
- New external ID (from `customerId` column)
- All existing packages
- Complete address information
- Provisioning parameters with default location settings

## Output Reports

### Dry Run Report Example
```
Wholesale Customer External ID Update - Dry Run Report
====================================================
Generated: 2025-06-03 15:45:00
Input File: input/accountNums_need_updatetest.csv
Mode: Dry Run (Preview Only)

Summary:
- Total customers processed: 1
- Successful updates: 1
- Failed updates: 0

Detailed Results:
----------------------------------------
1. ✓ Velvet Lab (ID: Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvNmRjNjFiYzgtYWNiOC00ZjVkLWEyZmItNmNmMzgwZWZiY2Q2)
   Current External ID: 3000698295
   New External ID: 1037704546
```

### Execution Report Example
```
Wholesale Customer External ID Update - Execution Report
=======================================================
Generated: 2025-06-03 15:50:00
Input File: input/accountNums_need_updatetest.csv
Mode: Execute Updates

Summary:
- Total customers processed: 1
- Successful updates: 1
- Failed updates: 0

Detailed Results:
----------------------------------------
1. ✓ Velvet Lab (ID: Y2lzY29zcGFyazovL3VzL0VOVEVSUFJJU0UvNmRjNjFiYzgtYWNiOC00ZjVkLWEyZmItNmNmMzgwZWZiY2Q2)
   Current External ID: 3000698295
   New External ID: 1037704546
   API Response: Success
   Status URL: https://webexapis.com/v1/wholesale/customers/status/abc123
```

## Error Handling

### Data Validation
The script validates each customer record for:
- Required fields (id, customerId, packages)
- Address completeness (addressLine1, city, country)
- Package format validation

### API Error Handling
- Graceful handling of HTTP errors with detailed logging
- Rate limiting to prevent API throttling
- Continuation of processing after individual failures
- Comprehensive error reporting in output files

### Common Issues and Solutions

1. **Authentication Issues**:
   ```
   Error: 401 Unauthorized
   ```
   **Solutions**:
   - Verify `WEBEX_ACCESS_TOKEN` in `.env` file exists
   - Remove quotes around token in `.env` file (script handles this automatically)
   - Check if environment variable is overriding `.env` file: `unset WEBEX_ACCESS_TOKEN`
   - Verify token permissions and expiration
   - Use `--verbose` flag to see token validation details

2. **Missing Required Fields**:
   ```
   Error: Validation failed: Missing customerId
   ```
   **Solutions**:
   - Ensure CSV has all required columns (`id`, `customerId`, `packages`)
   - Check for empty rows or missing data
   - Verify CSV was exported correctly from export script

3. **Rate Limiting**:
   ```
   Error: 429 Too Many Requests
   ```
   **Solutions**:
   - Increase `--delay` parameter (try 0.5 or 1.0 seconds)
   - Reduce `--batch-size` parameter (try 2-3 workers)
   - Run during off-peak hours

4. **Invalid Organization Filter**:
   ```
   Error: Invalid regex pattern
   ```
   **Solutions**:
   - Check regex syntax in `--org-pattern`
   - Use `--org-contains` for simple text matching
   - Test regex pattern online before using

5. **CSV Format Issues**:
   ```
   Error: No valid customers found
   ```
   **Solutions**:
   - Ensure CSV was generated by the export script
   - Check CSV encoding (should be UTF-8)
   - Verify column headers match expected format

## Performance Considerations

### Batch Size Guidelines
- **Small datasets (< 50 customers)**: Use default batch size (5)
- **Medium datasets (50-200 customers)**: Consider batch size 3-5
- **Large datasets (> 200 customers)**: Use batch size 2-3 with increased delay

### Rate Limiting
- Default delay (0.2 seconds) works for most scenarios
- Increase to 0.5-1.0 seconds if encountering rate limits
- Monitor API response times and adjust accordingly

## Examples

### Complete Workflow Example

```bash
# 1. First, run a dry run to preview changes
python scripts/update_wholesale_customer_external_ids.py \
  --dry-run \
  --input input/accountNums_need_updatetest.csv \
  --org-contains "lab"

# 2. Review the dry run report in output/

# 3. Execute the actual updates
python scripts/update_wholesale_customer_external_ids.py \
  --execute \
  --input input/accountNums_need_updatetest.csv \
  --org-contains "lab" \
  --batch-size 3 \
  --delay 0.3 \
  --verbose

# 4. Review the execution report for results
```

### Filtering Examples

```bash
# Update only customers with "Lab" in organization name
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --org-contains "lab"

# Update customers matching regex pattern (case-insensitive)
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --org-pattern "^(Acme|Velvet).*"

# Update all customers except test organizations
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --exclude-orgs "Test Corp,Demo Inc,Sandbox Ltd"
```

## Related Scripts

- [`export_wholesale_customers.py`](export_wholesale_customers.py): Export customer data to CSV
- [`update_wholesale_customer.py`](update_wholesale_customer.py): Interactive single customer updates

## Complete Workflow

### 1. Export Customer Data
```bash
# Export all customers or filter by organization
python scripts/export_wholesale_customers.py --org-contains "lab" --output "customers_to_update.csv"
```

### 2. Preview Updates
```bash
# Dry run to see what will be changed
python scripts/update_wholesale_customer_external_ids.py --dry-run --input output/customers_to_update.csv
```

### 3. Execute Updates
```bash
# Perform actual updates with monitoring
python scripts/update_wholesale_customer_external_ids.py --execute --input output/customers_to_update.csv --verbose
```

### 4. Verify Results
```bash
# Export updated data to verify changes
python scripts/export_wholesale_customers.py --org-contains "lab" --output "customers_updated.csv"
```

This workflow provides a complete solution for bulk external ID management with full audit trails and verification capabilities.

## Troubleshooting

### Debug Mode
Run with `--verbose` flag for detailed logging:
```bash
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --verbose
```

### Resume Processing
If processing is interrupted, use `--resume-from` to continue:
```bash
python scripts/update_wholesale_customer_external_ids.py --execute --input input/customers.csv --resume-from "customer_id_here"
```

### Validate CSV Format
Run a dry run on a small subset to validate CSV format:
```bash
python scripts/update_wholesale_customer_external_ids.py --dry-run --input input/customers.csv --org-names "Single Org Name"
```

## Notes

- The script preserves all existing customer data (packages, address, etc.)
- Only the `externalId` field is updated to match the `customerId` value
- Reports are automatically timestamped and saved to the output directory
- The script creates the output directory if it doesn't exist
- Processing can be safely interrupted and resumed using customer IDs