#!/usr/bin/env python3
"""
Debug script to understand environment variable loading issues
"""

import os
from dotenv import load_dotenv

print("=== Environment Variable Loading Debug ===")

# Check environment before loading .env
print("\n1. Environment variables BEFORE loading .env:")
webex_token_before = os.getenv("WEBEX_ACCESS_TOKEN")
if webex_token_before:
    print(f"   WEBEX_ACCESS_TOKEN found: {webex_token_before[:10]}...{webex_token_before[-10:]}")
    print(f"   Length: {len(webex_token_before)}")
else:
    print("   WEBEX_ACCESS_TOKEN: Not found")

# Load .env file
print("\n2. Loading .env file...")
load_dotenv()

# Check environment after loading .env
print("\n3. Environment variables AFTER loading .env:")
webex_token_after = os.getenv("WEBEX_ACCESS_TOKEN")
if webex_token_after:
    print(f"   WEBEX_ACCESS_TOKEN found: {webex_token_after[:10]}...{webex_token_after[-10:]}")
    print(f"   Length: {len(webex_token_after)}")
    
    # Remove quotes if present
    clean_token = webex_token_after.strip('"\'')
    if clean_token != webex_token_after:
        print(f"   After removing quotes: {clean_token[:10]}...{clean_token[-10:]}")
        print(f"   Clean length: {len(clean_token)}")
    else:
        print("   No quotes found to remove")
else:
    print("   WEBEX_ACCESS_TOKEN: Not found")

# Check if tokens changed
print("\n4. Comparison:")
if webex_token_before and webex_token_after:
    if webex_token_before == webex_token_after:
        print("   ✅ Token unchanged by .env loading")
    else:
        print("   ⚠️  Token CHANGED by .env loading")
        print(f"   Before: {webex_token_before[:10]}...{webex_token_before[-10:]}")
        print(f"   After:  {webex_token_after[:10]}...{webex_token_after[-10:]}")
elif webex_token_before and not webex_token_after:
    print("   ❌ Token was removed by .env loading")
elif not webex_token_before and webex_token_after:
    print("   ✅ Token was added by .env loading")
else:
    print("   ❌ No token found before or after")

# Check .env file content directly
print("\n5. Reading .env file directly:")
try:
    with open('.env', 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
        for line in lines:
            if 'WEBEX_ACCESS_TOKEN' in line:
                print(f"   Found line: {line}")
                # Extract token value
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    print(f"   Extracted value: {value[:10]}...{value[-10:]}")
                    print(f"   Extracted length: {len(value)}")
except FileNotFoundError:
    print("   ❌ .env file not found")
except Exception as e:
    print(f"   ❌ Error reading .env file: {e}")

# Test what the original script would get
print("\n6. Simulating original script token retrieval:")
def get_api_token():
    token = os.getenv("WEBEX_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("WEBEX_ACCESS_TOKEN not found")
    
    # Remove surrounding quotes if present
    token = token.strip('"\'')
    return token

try:
    final_token = get_api_token()
    print(f"   Final token: {final_token[:10]}...{final_token[-10:]}")
    print(f"   Final length: {len(final_token)}")
except Exception as e:
    print(f"   ❌ Error getting token: {e}")