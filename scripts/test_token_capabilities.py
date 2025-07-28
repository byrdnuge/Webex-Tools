#!/usr/bin/env python3
"""
Webex API Token Capability Testing Script

This script tests your Webex API token to determine:
1. If the token is valid and working
2. What APIs and scopes the token has access to
3. Specific issues with Broadworks/Wholesale API access
4. Recommendations for resolving authentication issues

Usage:
    python scripts/test_token_capabilities.py
"""

import os
import json
import requests
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WebexTokenTester:
    """Test Webex API token capabilities"""
    
    def __init__(self):
        self.token = self._get_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://webexapis.com/v1"
        self.results = {}
    
    def _get_token(self) -> str:
        """Get and validate token from environment"""
        token = os.getenv("WEBEX_ACCESS_TOKEN")
        if not token:
            raise EnvironmentError(
                "WEBEX_ACCESS_TOKEN not found in environment variables. "
                "Please check your .env file."
            )
        
        # Remove surrounding quotes if present
        token = token.strip('"\'')
        return token
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make API request and return structured result"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                response = requests.request(method, url, headers=self.headers, json=data, timeout=10)
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.json() if response.content else {},
                "error": None
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                "response": {},
                "error": str(e)
            }
    
    def test_basic_authentication(self) -> Dict[str, Any]:
        """Test basic API authentication with /people/me"""
        print("🔍 Testing basic authentication...")
        
        result = self._make_request("/people/me")
        
        if result["success"]:
            user_data = result["response"]
            print(f"✅ Basic authentication successful!")
            print(f"   User: {user_data.get('displayName', 'Unknown')}")
            print(f"   Email: {user_data.get('emails', ['Unknown'])[0] if user_data.get('emails') else 'Unknown'}")
            print(f"   User ID: {user_data.get('id', 'Unknown')}")
        else:
            print(f"❌ Basic authentication failed!")
            print(f"   Status Code: {result['status_code']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
        
        return result
    
    def test_organizations_access(self) -> Dict[str, Any]:
        """Test access to organizations API"""
        print("\n🏢 Testing organizations access...")
        
        result = self._make_request("/organizations")
        
        if result["success"]:
            orgs = result["response"].get("items", [])
            print(f"✅ Organizations access successful!")
            print(f"   Found {len(orgs)} organization(s)")
            for org in orgs[:3]:  # Show first 3
                print(f"   - {org.get('displayName', 'Unknown')} (ID: {org.get('id', 'Unknown')})")
        else:
            print(f"❌ Organizations access failed!")
            print(f"   Status Code: {result['status_code']}")
            if result["status_code"] == 403:
                print("   This suggests your token lacks admin privileges")
        
        return result
    
    def test_broadworks_access(self) -> Dict[str, Any]:
        """Test access to Broadworks enterprises API"""
        print("\n🏭 Testing Broadworks enterprises access...")
        
        result = self._make_request("/broadworks/enterprises?max=1")
        
        if result["success"]:
            enterprises = result["response"].get("items", [])
            print(f"✅ Broadworks access successful!")
            print(f"   Found {len(enterprises)} enterprise(s) in test query")
        else:
            print(f"❌ Broadworks access failed!")
            print(f"   Status Code: {result['status_code']}")
            if result["status_code"] == 401:
                print("   This indicates insufficient scopes for Broadworks API")
            elif result["status_code"] == 403:
                print("   This indicates your token lacks Broadworks permissions")
        
        return result
    
    def test_wholesale_access(self) -> Dict[str, Any]:
        """Test access to wholesale customers API"""
        print("\n🛒 Testing wholesale customers access...")
        
        result = self._make_request("/wholesale/customers?max=1")
        
        if result["success"]:
            customers = result["response"].get("items", [])
            print(f"✅ Wholesale access successful!")
            print(f"   Found {len(customers)} customer(s) in test query")
        else:
            print(f"❌ Wholesale access failed!")
            print(f"   Status Code: {result['status_code']}")
            if result["status_code"] == 401:
                print("   This indicates insufficient scopes for Wholesale API")
            elif result["status_code"] == 403:
                print("   This indicates your token lacks Wholesale permissions")
        
        return result
    
    def analyze_token_format(self) -> Dict[str, Any]:
        """Analyze token format and structure"""
        print("\n🔍 Analyzing token format...")
        
        analysis = {
            "length": len(self.token),
            "starts_with": self.token[:10],
            "ends_with": self.token[-10:],
            "contains_underscores": "_" in self.token,
            "contains_hyphens": "-" in self.token,
            "is_jwt_format": False,
            "token_type": "Unknown"
        }
        
        # Check if it looks like a JWT (has 3 parts separated by dots)
        if self.token.count('.') == 2:
            analysis["is_jwt_format"] = True
            analysis["token_type"] = "JWT (JSON Web Token)"
            
            try:
                # Try to decode JWT header (first part)
                header_b64 = self.token.split('.')[0]
                # Add padding if needed
                header_b64 += '=' * (4 - len(header_b64) % 4)
                header = json.loads(base64.b64decode(header_b64))
                analysis["jwt_header"] = header
            except Exception:
                analysis["jwt_decode_error"] = "Could not decode JWT header"
        
        elif self.token.startswith(('MWU', 'MGI', 'MjU')):
            analysis["token_type"] = "Webex Personal Access Token"
        
        print(f"   Token Length: {analysis['length']} characters")
        print(f"   Token Type: {analysis['token_type']}")
        print(f"   Format: {'JWT' if analysis['is_jwt_format'] else 'Base64-encoded'}")
        
        return analysis
    
    def test_admin_apis(self) -> Dict[str, Any]:
        """Test various admin-level APIs to determine scope"""
        print("\n👑 Testing admin-level API access...")
        
        admin_tests = {}
        
        # Test admin APIs
        admin_endpoints = [
            ("/admin/people", "People Admin"),
            ("/licenses", "Licenses"),
            ("/telephony/config/locations", "Telephony Locations"),
            ("/workspaces", "Workspaces"),
        ]
        
        for endpoint, name in admin_endpoints:
            result = self._make_request(endpoint)
            admin_tests[name] = result
            
            if result["success"]:
                print(f"   ✅ {name}: Access granted")
            else:
                print(f"   ❌ {name}: Access denied (Status: {result['status_code']})")
        
        return admin_tests
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check basic auth
        if not self.results.get("basic_auth", {}).get("success"):
            recommendations.append(
                "🚨 CRITICAL: Basic authentication failed. Your token may be expired or invalid. "
                "Generate a new token from developer.webex.com"
            )
            return recommendations
        
        # Check broadworks access
        if not self.results.get("broadworks", {}).get("success"):
            broadworks_status = self.results.get("broadworks", {}).get("status_code")
            if broadworks_status == 401:
                recommendations.append(
                    "🔑 SCOPE ISSUE: Your token lacks Broadworks API scopes. "
                    "You need 'spark-admin:broadworks_enterprises_read' scope."
                )
            elif broadworks_status == 403:
                recommendations.append(
                    "🚫 PERMISSION ISSUE: Your account lacks Broadworks permissions. "
                    "Contact your Webex administrator or Cisco partner support."
                )
        
        # Check wholesale access
        if not self.results.get("wholesale", {}).get("success"):
            wholesale_status = self.results.get("wholesale", {}).get("status_code")
            if wholesale_status == 401:
                recommendations.append(
                    "🔑 SCOPE ISSUE: Your token lacks Wholesale API scopes. "
                    "You need 'spark-admin:wholesale_customers_read' and 'spark-admin:wholesale_customers_write' scopes."
                )
            elif wholesale_status == 403:
                recommendations.append(
                    "🚫 PERMISSION ISSUE: Your account lacks Wholesale permissions. "
                    "This requires partner-level access or special wholesale privileges."
                )
        
        # Check organizations access
        if not self.results.get("organizations", {}).get("success"):
            recommendations.append(
                "👑 ADMIN ISSUE: Your token lacks organization admin privileges. "
                "Broadworks/Wholesale APIs typically require admin-level access."
            )
        
        # Token type recommendations
        token_analysis = self.results.get("token_analysis", {})
        if token_analysis.get("token_type") == "Webex Personal Access Token":
            recommendations.append(
                "🔄 TOKEN TYPE: You're using a Personal Access Token. "
                "Consider creating a Service App Integration with proper scopes for production use."
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append(
                "✅ Your token appears to have the necessary access! "
                "If you're still getting 401 errors, check for network issues or API endpoint changes."
            )
        else:
            recommendations.append(
                "📋 NEXT STEPS: Review the troubleshooting guide in scripts/TROUBLESHOOTING_401_UNAUTHORIZED.md "
                "for detailed solutions to resolve these issues."
            )
        
        return recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        print("=" * 60)
        print("🧪 WEBEX API TOKEN CAPABILITY TEST")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing token: {self.token[:10]}...{self.token[-10:]}")
        print()
        
        # Run all tests
        self.results["token_analysis"] = self.analyze_token_format()
        self.results["basic_auth"] = self.test_basic_authentication()
        self.results["organizations"] = self.test_organizations_access()
        self.results["broadworks"] = self.test_broadworks_access()
        self.results["wholesale"] = self.test_wholesale_access()
        self.results["admin_apis"] = self.test_admin_apis()
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        test_summary = [
            ("Basic Authentication", self.results["basic_auth"]["success"]),
            ("Organizations Access", self.results["organizations"]["success"]),
            ("Broadworks Access", self.results["broadworks"]["success"]),
            ("Wholesale Access", self.results["wholesale"]["success"]),
        ]
        
        for test_name, success in test_summary:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:.<30} {status}")
        
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        print("\n" + "=" * 60)
        print("🔗 USEFUL LINKS")
        print("=" * 60)
        print("• Webex Developer Portal: https://developer.webex.com/")
        print("• Create Integration: https://developer.webex.com/my-apps/new/integration")
        print("• API Documentation: https://developer.webex.com/docs/api/v1/broadworks-enterprises")
        print("• Partner Support: partner-support@cisco.com")
        
        return self.results

def main():
    """Main function to run the token capability tests"""
    try:
        tester = WebexTokenTester()
        results = tester.run_all_tests()
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"output/token_test_results_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error running token tests: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())