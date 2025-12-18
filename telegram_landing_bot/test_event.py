
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:50
# Last Updated: 2025-12-18T12:12:50
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test event tracking to Supreme server
"""

import requests
import json

def test_event_tracking():
    """Test event tracking to the Supreme server"""

    url = 'https://gladsomely-unvitriolized-trudie.ngrok-free.dev/events/track'

    payload = {
        "event_type": "click",
        "event_name": "campaign_click",
        "click_id": "123e4567-e89b-12d3-a456-426614174000",
        "campaign_id": "9061"
    }

    print(f"Testing event tracking to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(url, json=payload, timeout=10)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("✅ SUCCESS: Event tracked successfully!")
                print(f"Event ID: {result.get('event_id')}")
            else:
                print("❌ FAILED: Event tracking returned error")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_event_tracking()
