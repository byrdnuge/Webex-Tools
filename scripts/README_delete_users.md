# Webex Users Deletion Script

This script allows you to delete a list of users from a Webex organization. It provides multiple input methods, safety features, and comprehensive logging.

## Features

- **Multiple Input Methods**: CSV files, command-line arguments, or individual user identifiers
- **Safety First**: Dry-run mode to preview deletions before execution
- **Flexible User Identification**: Support for email addresses, user IDs, and display names
- **Organization Filtering**: Restrict deletions to specific organizations
- **Comprehensive Logging**: Detailed logs with timestamps for audit trails
- **Error Handling**: Robust error handling with retry logic and detailed error messages
- **Rate Limiting**: Built-in delays to respect API rate limits

## Prerequisites

1. **Environment Setup**: Ensure you have a `.env` file with your Webex API token:
   ```
   WEBEX_ACCESS_TOKEN=your_webex_api_token_here
   ```

2. **Required Packages**: Install dependencies from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

3. **API Permissions**: Your Webex API token must have the following scopes:
   - `spark:people_read` - To look up users
   - `spark:people_write` - To delete users
   - `spark:organizations_read` - To verify organization membership

## Usage

### Basic Usage

```bash
# Always start with a dry run to preview what will be deleted
python scripts/delete_users.py --csv-file input/users_to_delete.csv --dry-run

# After reviewing the dry run results, execute the actual deletion
python scripts/delete_users.py --csv-file input/users_to_delete.csv
```

### Command Line Options

#### Input Methods

```bash
# Delete users from CSV file
python scripts/delete_users.py --csv-file input/users_to_delete.csv

# Delete specific users by email
python scripts/delete_users.py --emails "user1@example.com,user2@example.com"

# Delete users by user IDs
python scripts/delete_users.py --user-ids "id1,id2,id3"

# Delete users by display names
python scripts/delete_users.py --display-names "John Doe,Jane Smith"
```

#### Organization Filtering

```bash
# Only delete users from a specific organization
python scripts/delete_users.py --csv-file input/users.csv --org-name "My Organization"

# Filter by organization ID
python scripts/delete_users.py --csv-file input/users.csv --org-id "Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVElPTi8..."
```

#### Safety and Execution Options

```bash
# Dry run (preview only, no actual deletions)
python scripts/delete_users.py --csv-file input/users.csv --dry-run

# Skip confirmation prompts
python scripts/delete_users.py --csv-file input/users.csv --force

# Custom delay between API calls (default: 0.5 seconds)
python scripts/delete_users.py --csv-file input/users.csv --delay 1.0
```

#### Output and Logging

```bash
# Custom log file name
python scripts/delete_users.py --csv-file input/users.csv --log-file "my_deletion_log.txt"

# Custom output directory
python scripts/delete_users.py --csv-file input/users.csv --output-dir "logs"

# Verbose output
python scripts/delete_users.py --csv-file input/users.csv --verbose
```

## CSV File Format

The script supports CSV files with flexible column headers. Include at least one of these columns:

### Supported Column Headers (case-insensitive)

| User Identifier | Accepted Column Names |
|----------------|----------------------|
| Email Address | `email`, `user_email`, `Email`, `Email Address` |
| User ID | `user_id`, `userid`, `id`, `User ID` |
| Display Name | `display_name`, `displayname`, `name`, `full_name`, `Display Name` |

### Example CSV Files

**Simple email list:**
```csv
email
user1@example.com
user2@example.com
user3@example.com
```

**Multiple identifiers:**
```csv
Email,User ID,Display Name
user1@example.com,Y2lzY29zcGFyazovL3VzL1BFT1BMRS8xMjM0,John Doe
user2@example.com,,Jane Smith
,Y2lzY29zcGFyazovL3VzL1BFT1BMRS81Njc4,
```

**Export from another system:**
```csv
Full Name,Email Address,Department
John Doe,john.doe@company.com,Engineering
Jane Smith,jane.smith@company.com,Marketing
```

## Output and Logging

### Log Files

The script creates detailed log files in the `output/` directory (or custom directory):

- **Dry Run**: `user_deletion_dry_run_YYYYMMDD_HHMMSS.txt`
- **Execution**: `user_deletion_execution_YYYYMMDD_HHMMSS.txt`
- **Custom**: Use `--log-file` to specify a custom name

### Log Content

Each log entry includes:
- Timestamp
- Operation performed
- User details (name, email, ID)
- Success/failure status
- Error messages (if any)

### Example Log Output

```
[2025-01-28 15:30:15] Starting user deletion script in DRY RUN mode
[2025-01-28 15:30:16] Reading users from CSV file: input/users_to_delete.csv
[2025-01-28 15:30:16] Found 3 user(s) to process
[2025-01-28 15:30:17] Found user: John Doe (john.doe@company.com)
[2025-01-28 15:30:18] Found user: Jane Smith (jane.smith@company.com)
[2025-01-28 15:30:19] User not found: {'email': 'nonexistent@company.com'}
[2025-01-28 15:30:20] [DRY RUN] Would delete user: John Doe (john.doe@company.com)
[2025-01-28 15:30:21] [DRY RUN] Would delete user: Jane Smith (jane.smith@company.com)
[2025-01-28 15:30:22] Operation completed - Successful: 2, Failed: 0
```

## Safety Features

### 1. Dry Run Mode

**Always use dry run first** to preview what will be deleted:

```bash
python scripts/delete_users.py --csv-file input/users.csv --dry-run
```

This will:
- Look up all users
- Show exactly which users would be deleted
- Create a log file with "dry_run" in the name
- Not perform any actual deletions

### 2. Confirmation Prompts

Unless using `--force`, the script will ask for confirmation before deleting users:

```
Users to be deleted:
  - John Doe (john.doe@company.com) [ID: Y2lzY29zcGFyazovL3VzL1BFT1BMRS8xMjM0]
  - Jane Smith (jane.smith@company.com) [ID: Y2lzY29zcGFyazovL3VzL1BFT1BMRS81Njc4]

Are you sure you want to delete 2 user(s)? (yes/no):
```

### 3. Organization Filtering

Prevent accidental deletions across organizations:

```bash
# Only delete users from "My Company"
python scripts/delete_users.py --csv-file input/users.csv --org-name "My Company"
```

### 4. Detailed Logging

Every operation is logged with timestamps for audit purposes.

## Error Handling

The script handles various error scenarios:

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `WEBEX_ACCESS_TOKEN not found` | Missing or invalid .env file | Create `.env` file with valid token |
| `User not found` | Invalid email/ID or user doesn't exist | Verify user identifiers in CSV |
| `403 Forbidden` | Insufficient API permissions | Ensure token has required scopes |
| `429 Too Many Requests` | Rate limiting | Increase `--delay` parameter |
| `CSV file not found` | Invalid file path | Check file path and permissions |

### Rate Limiting

The script includes built-in rate limiting:
- Default delay: 0.5 seconds between API calls
- Adjustable with `--delay` parameter
- Automatic handling of rate limit responses

## Examples

### Example 1: Safe Deletion Process

```bash
# Step 1: Dry run to preview
python scripts/delete_users.py --csv-file input/users_to_delete.csv --dry-run

# Step 2: Review the dry run log file
cat output/user_deletion_dry_run_20250128_153015.txt

# Step 3: Execute if everything looks correct
python scripts/delete_users.py --csv-file input/users_to_delete.csv
```

### Example 2: Organization-Specific Deletion

```bash
# Delete users only from "Acme Corp" organization
python scripts/delete_users.py \
  --csv-file input/acme_users.csv \
  --org-name "Acme Corp" \
  --dry-run
```

### Example 3: Command Line Deletion

```bash
# Delete specific users by email
python scripts/delete_users.py \
  --emails "user1@company.com,user2@company.com" \
  --dry-run
```

### Example 4: Bulk Deletion with Custom Settings

```bash
# Large deletion with custom settings
python scripts/delete_users.py \
  --csv-file input/large_user_list.csv \
  --delay 1.0 \
  --output-dir "deletion_logs" \
  --log-file "bulk_deletion_$(date +%Y%m%d).txt" \
  --verbose
```

## Best Practices

### 1. Always Start with Dry Run
Never skip the dry run step, especially for large deletions.

### 2. Backup User Data
Before deletion, consider exporting user data for backup:
```bash
# Use the export script first if available
python scripts/export_users.py --org-name "My Company"
```

### 3. Verify Organization Scope
Use organization filtering to prevent accidental cross-org deletions.

### 4. Monitor Rate Limits
For large deletions, increase the delay to avoid rate limiting:
```bash
python scripts/delete_users.py --csv-file input/users.csv --delay 1.0
```

### 5. Keep Logs
Retain deletion logs for audit and compliance purposes.

### 6. Test with Small Batches
For large deletions, test with a small subset first.

## Troubleshooting

### Authentication Issues

```bash
# Test your token
python scripts/test_token_capabilities.py
```

### CSV Format Issues

```bash
# Check CSV format
head -5 input/users_to_delete.csv
```

### User Lookup Issues

Common reasons users might not be found:
- User has already been deleted
- Email address has changed
- User is in a different organization
- Typos in user identifiers

### API Rate Limiting

If you encounter rate limiting:
```bash
# Increase delay between requests
python scripts/delete_users.py --csv-file input/users.csv --delay 2.0
```

## Security Considerations

1. **Token Security**: Keep your API token secure and never commit it to version control
2. **Audit Logs**: Retain deletion logs for compliance and audit purposes
3. **Least Privilege**: Use API tokens with minimal required permissions
4. **Confirmation**: Always use dry run mode first
5. **Organization Scope**: Use organization filtering to limit scope

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the log files for detailed error messages
3. Verify your API token permissions
4. Test with a small subset of users first

## Related Scripts

- [`user_lookup.py`](user_lookup.py) - Look up users in an organization
- [`test_token_capabilities.py`](test_token_capabilities.py) - Test API token permissions
- [`export_wholesale_customers.py`](export_wholesale_customers.py) - Export organization data