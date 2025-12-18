# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:53
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Script to create campaign in local API for Supreme Company bot
"""

import requests
import json


def create_campaign():
    """Create campaign ID 123 for Supreme Company"""

    url = 'http://localhost:5000/v1/campaigns'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test_jwt_token_12345'
    }

    campaign_data = {
        "name": "Supreme Company Campaign",
        "description": "Premium landing page campaign for Supreme Company",
        "costModel": "CPC",
        "payout": {"amount": 2.5, "currency": "USD"},
        "dailyBudget": {"amount": 100, "currency": "USD"},
        "totalBudget": {"amount": 5000, "currency": "USD"},
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2025-12-31T23:59:59Z",
        "whiteUrl": "https://gladsomely-unvitriolized-trudie.ngrok-free.dev/safe-page",
        "blackUrl": "https://gladsomely-unvitriolized-trudie.ngrok-free.dev/offer"
    }

    try:
        print(f"Creating campaign at {url}")
        print(f"Data: {json.dumps(campaign_data, indent=2)}")

        response = requests.post(url, headers=headers, json=campaign_data, timeout=10)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 201:
            print("✅ Campaign created successfully!")
        elif response.status_code == 200:
            print("✅ Campaign created/updated successfully!")
        else:
            print(f"❌ Failed to create campaign. Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print("Make sure your API server is running on http://localhost:5000")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    create_campaign()
