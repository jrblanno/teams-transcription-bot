#!/usr/bin/env python3
"""Simple POC test for bot authentication."""
import os
import requests
from src.auth.msal_client import MSALAuthClient


def test_auth():
    """Test if our bot can authenticate and call Graph API."""
    try:
        # Test authentication
        print("🔐 Testing authentication...")
        client = MSALAuthClient()
        token = client.get_token()
        print(f"✅ Got token: {token[:20]}...")

        # Test Graph API call
        print("\n📊 Testing Graph API call...")
        headers = client.get_headers()

        # Simple Graph API call to get service principal info
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '{client.client_id}'",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('value'):
                sp = data['value'][0]
                print(f"✅ Found service principal: {sp.get('displayName')}")
                print(f"   App ID: {sp.get('appId')}")
                print(f"   Object ID: {sp.get('id')}")

                # Check app roles (permissions)
                app_roles = sp.get('appRoles', [])
                print(f"   App Roles: {len(app_roles)} configured")

                return True
            else:
                print("❌ Service principal not found")
                return False
        else:
            print(f"❌ Graph API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Teams Bot Authentication POC\n")

    # Check environment variables
    required_vars = ["BOT_APP_ID", "BOT_APP_PASSWORD", "AZURE_TENANT_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        exit(1)

    print(f"Environment variables found:")
    print(f"  BOT_APP_ID: {os.getenv('BOT_APP_ID')}")
    print(f"  AZURE_TENANT_ID: {os.getenv('AZURE_TENANT_ID')}")
    print(f"  BOT_APP_PASSWORD: {'*' * len(os.getenv('BOT_APP_PASSWORD', ''))}")
    print()

    success = test_auth()

    if success:
        print("\n🎉 Authentication POC successful!")
        print("The bot can authenticate and call Graph API.")
    else:
        print("\n💥 Authentication POC failed!")
        exit(1)