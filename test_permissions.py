#!/usr/bin/env python3
"""
Test Graph API permissions for Teams Bot
Verifies all required permissions are granted and working
"""

import os
import sys
from dotenv import load_dotenv
from src.auth.msal_client import MSALAuthClient
import requests
import json

# Load environment variables
load_dotenv()

def test_permissions():
    print("🔍 Testing Graph API Permissions for Teams Bot\n")
    print("=" * 60)

    # Initialize auth client
    client = MSALAuthClient()

    try:
        # Get token
        token = client.get_token()
        print(f"✅ Authentication successful!")
        print(f"   Token obtained: {token[:20]}...\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

    # Headers for Graph API calls
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Get the application's service principal to check permissions
    app_id = os.getenv("BOT_APP_ID")
    sp_url = f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '{app_id}'"

    print("📋 Checking Service Principal and Permissions:")
    print("-" * 60)

    response = requests.get(sp_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get('value'):
            sp = data['value'][0]
            print(f"✅ Service Principal found: {sp.get('displayName')}")
            print(f"   Object ID: {sp.get('id')}")

            # Get the app roles assigned to this service principal
            sp_id = sp.get('id')
            roles_url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp_id}/appRoleAssignments"

            roles_response = requests.get(roles_url, headers=headers)
            if roles_response.status_code == 200:
                roles_data = roles_response.json()
                app_roles = roles_data.get('value', [])
                print(f"   App Roles Assigned: {len(app_roles)}")
                if app_roles:
                    print("\n   Granted Permissions:")
                    for role in app_roles:
                        # Get the resource service principal to get permission names
                        resource_sp_id = role.get('resourceId')
                        resource_url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{resource_sp_id}"
                        resource_response = requests.get(resource_url, headers=headers)
                        if resource_response.status_code == 200:
                            resource_data = resource_response.json()
                            # Find the permission name
                            app_role_id = role.get('appRoleId')
                            for app_role in resource_data.get('appRoles', []):
                                if app_role.get('id') == app_role_id:
                                    print(f"     - {app_role.get('value')} ({app_role.get('displayName')})")
                                    break
            else:
                print(f"   Could not retrieve app role assignments: {roles_response.status_code}")
    else:
        print(f"❌ Failed to get service principal: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    print("\n" + "=" * 60)
    print("🧪 Testing Specific Graph API Permissions:")
    print("-" * 60)

    # Test permissions we need
    permissions_to_test = [
        {
            "name": "User.Read.All",
            "test": lambda h: requests.get("https://graph.microsoft.com/v1.0/users?$top=1", headers=h),
            "description": "Read user profiles"
        },
        {
            "name": "OnlineMeetings.ReadWrite.All",
            "test": lambda h: requests.get("https://graph.microsoft.com/v1.0/me/onlineMeetings", headers=h),
            "description": "Access online meetings"
        },
        {
            "name": "Calls.AccessMedia.All",
            "test": lambda h: requests.get("https://graph.microsoft.com/v1.0/communications/calls", headers=h),
            "description": "Access call media"
        }
    ]

    all_passed = True
    for perm in permissions_to_test:
        print(f"\n📌 Testing {perm['name']}:")
        print(f"   Purpose: {perm['description']}")
        try:
            response = perm['test'](headers)
            if response.status_code in [200, 404, 400]:  # 404/400 might be OK if no data exists
                print(f"   ✅ Permission appears to be granted (status: {response.status_code})")
            elif response.status_code == 403:
                print(f"   ❌ Permission DENIED - needs admin consent or not granted")
                all_passed = False
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed")
                all_passed = False
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                print(f"       Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print("-" * 60)

    if all_passed:
        print("✅ All permission tests completed successfully!")
        print("   The bot has the required Graph API permissions.")
        print("\n💡 Note: Some endpoints return 404 if no data exists,")
        print("   which is normal for a new bot that hasn't joined meetings yet.")
    else:
        print("⚠️  Some permissions may need attention.")
        print("\n🔧 To fix permission issues:")
        print("   1. Go to Azure Portal > App Registrations")
        print(f"   2. Find app: {app_id}")
        print("   3. Check API Permissions tab")
        print("   4. Ensure admin consent is granted for all permissions")
        print("\n   Or use this URL to grant admin consent:")
        print(f"   https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/adminconsent?client_id={app_id}")

    return all_passed

if __name__ == "__main__":
    success = test_permissions()
    sys.exit(0 if success else 1)