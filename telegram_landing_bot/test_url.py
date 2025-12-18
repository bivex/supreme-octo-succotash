# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:47
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test the corrected tracking URL
"""

import requests


def test_tracking_url():
    """Test the tracking URL with correct cid parameter"""

    test_url = 'https://gladsomely-unvitriolized-trudie.ngrok-free.dev/v1/click?click_id=test123&source=telegram_bot&cid=camp_7192&sub1=telegram_bot&sub2=telegram&sub3=callback_offer&sub4=test_user&sub5=premium_offer'

    print(f'Testing URL: {test_url}')
    print()

    try:
        response = requests.get(test_url, timeout=10, allow_redirects=False)
        print(f'Status Code: {response.status_code}')

        if response.status_code == 302:
            print(f'✅ SUCCESS: Campaign found!')
            print(f'Redirect Location: {response.headers.get("Location")}')
        elif response.status_code == 404:
            print(f'❌ FAILED: Campaign not found')
            print(f'Response: {response.text}')
        else:
            print(f'Response: {response.text}')

    except Exception as e:
        print(f'❌ Error: {e}')


if __name__ == "__main__":
    test_tracking_url()
