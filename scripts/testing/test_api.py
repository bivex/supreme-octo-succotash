
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Test API endpoints."""

import requests
import time

def test_api():
    """Test API endpoints."""
    headers = {'Authorization': 'Bearer test_jwt_token_12345', 'Content-Type': 'application/json'}

    print("Waiting for app to start...")
    time.sleep(5)

    try:
        # Test campaigns list
        print("Testing campaigns list...")
        response = requests.get('http://localhost:5000/v1/campaigns', headers=headers, timeout=10)
        print(f"Campaigns status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Found {len(data.get('campaigns', []))} campaigns")
            except Exception as json_error:
                print(f"JSON parsing error: {json_error}")

        # Test specific campaign
        print("\nTesting specific campaign...")
        response = requests.get('http://localhost:5000/v1/campaigns/camp_4133', headers=headers, timeout=10)
        print(f"Campaign detail status: {response.status_code}")

        # Test analytics (this should work now with Decimal fix)
        print("\nTesting analytics...")
        response = requests.get('http://localhost:5000/v1/campaigns/camp_4133/analytics', headers=headers, timeout=10)
        print(f"Analytics status: {response.status_code}")
        if response.status_code == 200:
            print("Analytics endpoint works!")
        else:
            print(f"Analytics error: {response.text[:200]}")

    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    test_api()
