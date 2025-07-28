# Troubleshooting 401 Unauthorized Error - Webex Broadworks/Wholesale APIs

## Root Cause Identified

The 401 Unauthorized error occurs because **Personal Access Tokens from developer.webex.com do NOT have access to Broadworks/Wholesale APIs**. These are enterprise/partner-level APIs that require special permissions.

## Why Personal Access Tokens Don't Work

1. **Limited Scope**: Personal Access Tokens only provide access to standard Webex APIs (messaging, meetings, spaces, etc.)
2. **Enterprise APIs Restricted**: Broadworks/Wholesale APIs are designed for:
   - Webex Partners
   - Service Providers  
   - Enterprise Administrators with special wholesale privileges
3. **Different Authentication Model**: These APIs require organization-level or partner-level authentication

## Solutions to Fix the 401 Error

### Option 1: Create a Service App Integration (Recommended)

1. **Go to Webex Developer Portal**: https://developer.webex.com/
2. **Create New Integration**:
   - Click "Start Building Apps" → "Create a New App" → "Integration"
   - Name: "Wholesale Customer Management"
   - Description: "Integration for managing wholesale customers"
   - Redirect URI: `http://localhost:3000/auth` (or your preferred callback)

3. **Request Required Scopes**:
   ```
   spark-admin:broadworks_enterprises_read
   spark-admin:wholesale_customers_read
   spark-admin:wholesale_customers_write
   spark-admin:organizations_read
   ```

4. **Complete OAuth Flow**:
   - Use the Integration's Client ID and Client Secret
   - Implement OAuth 2.0 authorization code flow
   - Exchange authorization code for access token

### Option 2: Request Partner/Wholesale Access

1. **Contact Webex Partner Support**:
   - Email: partner-support@cisco.com
   - Explain your use case for wholesale customer management
   - Request access to Broadworks/Wholesale APIs

2. **Provide Business Justification**:
   - Company information
   - Use case description
   - Expected volume of API calls
   - Technical contact information

### Option 3: Use Organization Admin Token (If Available)

If you're an organization administrator with wholesale privileges:

1. **Check Organization Permissions**:
   - Log into Webex Control Hub
   - Verify you have wholesale/partner permissions
   - Generate token from admin account

2. **Generate Admin Token**:
   - Go to developer.webex.com while logged in as org admin
   - Generate Personal Access Token
   - This token should inherit admin privileges

## Immediate Testing Steps

### Step 1: Verify Current Token Capabilities

Create a test script to check what your current token can access:

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("WEBEX_ACCESS_TOKEN").strip('"\'')
headers = {"Authorization": f"Bearer {token}"}

# Test basic access
response = requests.get("https://webexapis.com/v1/people/me", headers=headers)
print(f"Basic API access: {response.status_code}")

# Test organizations access
response = requests.get("https://webexapis.com/v1/organizations", headers=headers)
print(f"Organizations access: {response.status_code}")

# Test broadworks access
response = requests.get("https://webexapis.com/v1/broadworks/enterprises?max=1", headers=headers)
print(f"Broadworks access: {response.status_code}")
```

### Step 2: Check Token Scopes

Decode your token to see available scopes:

```python
import base64
import json

token = "YOUR_TOKEN_HERE"
# Webex tokens are typically JWT format
# You can decode the payload to see scopes (if not encrypted)
```

## Required API Scopes for Your Script

Your script needs these specific scopes:

| API Endpoint | Required Scope |
|--------------|----------------|
| `/v1/broadworks/enterprises` | `spark-admin:broadworks_enterprises_read` |
| `/v1/wholesale/customers/{id}` | `spark-admin:wholesale_customers_write` |
| General organization access | `spark-admin:organizations_read` |

## Alternative Approaches

### Option A: Use Webex Control Hub UI
- Manually manage wholesale customers through the web interface
- Export/import customer data as needed

### Option B: Contact Your Webex Account Team
- Request API access through your Cisco account representative
- They can enable wholesale API access for your organization

### Option C: Partner Program Enrollment
- Enroll in Webex Partner Program
- Gain access to partner-level APIs and tools

## Next Steps

1. **Immediate**: Test current token capabilities with the diagnostic script above
2. **Short-term**: Create a Service App Integration with proper scopes
3. **Long-term**: Consider partner program enrollment if doing this at scale

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Insufficient scopes | Use integration with proper scopes |
| 403 Forbidden | No wholesale access | Request partner/admin access |
| 404 Not Found | Wrong API endpoint | Verify endpoint URLs |
| 429 Rate Limited | Too many requests | Implement rate limiting |

## Contact Information

- **Webex Developer Support**: https://developer.webex.com/support
- **Partner Support**: partner-support@cisco.com
- **Documentation**: https://developer.webex.com/docs/api/v1/broadworks-enterprises

---

**Note**: The Broadworks and Wholesale APIs are specialized enterprise features. Standard personal access tokens are intentionally restricted from these APIs for security and business reasons.