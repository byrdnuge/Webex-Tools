# Token Capability Testing Script

## Overview

The `test_token_capabilities.py` script is a comprehensive diagnostic tool that tests your Webex API token to determine what APIs and scopes it has access to. This is particularly useful for troubleshooting 401 Unauthorized errors with Broadworks and Wholesale APIs.

## What It Tests

### 🔍 Basic Authentication
- Tests if your token is valid and working
- Retrieves your user information from `/people/me`
- Confirms the token is properly formatted and not expired

### 🏢 Organizations Access
- Tests access to organization-level APIs
- Indicates if you have admin privileges
- Required for most enterprise-level operations

### 🏭 Broadworks Enterprises API
- Tests the specific API that's failing in your script
- Checks for `spark-admin:broadworks_enterprises_read` scope
- Identifies scope vs. permission issues

### 🛒 Wholesale Customers API
- Tests access to wholesale customer management
- Checks for wholesale-specific scopes
- Determines if you have partner-level access

### 👑 Admin-Level APIs
- Tests various admin APIs to determine scope level
- Helps identify what permissions your token has
- Useful for understanding token capabilities

### 🔍 Token Analysis
- Analyzes token format and structure
- Identifies token type (Personal vs. Integration)
- Attempts to decode JWT tokens if applicable

## Usage

### Prerequisites
Make sure you have your `.env` file configured with your token:
```bash
WEBEX_ACCESS_TOKEN="your_token_here"
```

### Running the Script
```bash
# From the project root directory
python scripts/test_token_capabilities.py

# Or make it executable and run directly
chmod +x scripts/test_token_capabilities.py
./scripts/test_token_capabilities.py
```

### Expected Output
The script will provide:
1. **Real-time test results** as each API is tested
2. **Detailed analysis** of your token format and capabilities
3. **Summary table** showing pass/fail status for each test
4. **Specific recommendations** based on the test results
5. **Useful links** for resolving identified issues

### Sample Output
```
============================================================
🧪 WEBEX API TOKEN CAPABILITY TEST
============================================================
Timestamp: 2025-01-22 14:52:00
Testing token: MWU4OTkwZm...968227ca3d8

🔍 Analyzing token format...
   Token Length: 108 characters
   Token Type: Webex Personal Access Token
   Format: Base64-encoded

🔍 Testing basic authentication...
✅ Basic authentication successful!
   User: John Doe
   Email: john.doe@example.com
   User ID: Y2lzY29zcGFyazovL3VzL1BFT1BMRS8...

🏢 Testing organizations access...
❌ Organizations access failed!
   Status Code: 403
   This suggests your token lacks admin privileges

🏭 Testing Broadworks enterprises access...
❌ Broadworks access failed!
   Status Code: 401
   This indicates insufficient scopes for Broadworks API

🛒 Testing wholesale customers access...
❌ Wholesale access failed!
   Status Code: 401
   This indicates insufficient scopes for Wholesale API

============================================================
📊 TEST SUMMARY
============================================================
Basic Authentication.............. ✅ PASS
Organizations Access.............. ❌ FAIL
Broadworks Access................. ❌ FAIL
Wholesale Access.................. ❌ FAIL

============================================================
💡 RECOMMENDATIONS
============================================================
1. 🔑 SCOPE ISSUE: Your token lacks Broadworks API scopes. You need 'spark-admin:broadworks_enterprises_read' scope.
2. 🔑 SCOPE ISSUE: Your token lacks Wholesale API scopes. You need 'spark-admin:wholesale_customers_read' and 'spark-admin:wholesale_customers_write' scopes.
3. 👑 ADMIN ISSUE: Your token lacks organization admin privileges. Broadworks/Wholesale APIs typically require admin-level access.
4. 🔄 TOKEN TYPE: You're using a Personal Access Token. Consider creating a Service App Integration with proper scopes for production use.
5. 📋 NEXT STEPS: Review the troubleshooting guide in scripts/TROUBLESHOOTING_401_UNAUTHORIZED.md for detailed solutions to resolve these issues.
```

## Output Files

The script automatically saves detailed test results to:
```
output/token_test_results_YYYYMMDD_HHMMSS.json
```

This JSON file contains all the raw API responses and can be useful for:
- Sharing with support teams
- Detailed analysis of API responses
- Tracking changes over time

## Common Test Results

### ✅ All Tests Pass
Your token has full access to Broadworks/Wholesale APIs. If you're still getting 401 errors, check for:
- Network connectivity issues
- API endpoint changes
- Rate limiting

### ❌ Basic Auth Fails
Your token is invalid, expired, or malformed:
- Generate a new token from developer.webex.com
- Check for typos in your `.env` file
- Ensure no extra spaces or quotes

### ❌ Broadworks/Wholesale Fail (401)
Scope issues - your token lacks required permissions:
- Create a Service App Integration with admin scopes
- Request partner-level access from Cisco
- Use an organization admin token

### ❌ Broadworks/Wholesale Fail (403)
Permission issues - your account lacks access:
- Contact your Webex administrator
- Request partner program enrollment
- Verify your organization has wholesale features

## Troubleshooting

### Script Won't Run
```bash
# Install required dependencies
pip install requests python-dotenv

# Check Python version (requires 3.6+)
python --version

# Verify .env file exists and has correct format
cat .env
```

### No Token Found
```bash
# Check if .env file exists
ls -la .env

# Verify token variable name
grep WEBEX_ACCESS_TOKEN .env
```

### Network Issues
- Check internet connectivity
- Verify firewall settings
- Try running from a different network

## Related Files

- [`scripts/update_wholesale_customer.py`](update_wholesale_customer.py) - The original script that's failing
- [`scripts/TROUBLESHOOTING_401_UNAUTHORIZED.md`](TROUBLESHOOTING_401_UNAUTHORIZED.md) - Detailed troubleshooting guide
- [`.env`](../.env) - Environment variables file with your token

## Support

If the script identifies issues with your token:

1. **For scope issues**: Follow the Integration creation guide in the troubleshooting document
2. **For permission issues**: Contact partner-support@cisco.com
3. **For technical issues**: Visit https://developer.webex.com/support

## Security Note

This script only reads your token and makes read-only API calls (except for the wholesale test which is also read-only). It does not modify any data or expose your token in the output beyond showing the first/last 10 characters for identification.