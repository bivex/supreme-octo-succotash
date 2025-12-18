
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
"""
Comprehensive business logic testing for Campaign API
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5000"
HEADERS = {
    'Authorization': 'Bearer test_jwt_token_12345',
    'Content-Type': 'application/json'
}

class CampaignAPITester:
    """Test class for Campaign API business logic."""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_campaign_id = None

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request and return response data."""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            result = {
                'status_code': response.status_code,
                'success': response.status_code < 400,
                'data': None,
                'error': None,
                'response_text': response.text
            }

            if response.status_code < 400:
                try:
                    result['data'] = response.json()
                except Exception as json_error:
                    result['data'] = response.text
                    result['json_error'] = str(json_error)
            else:
                try:
                    result['data'] = response.json()
                except Exception as json_error:
                    result['error'] = response.text
                    result['json_error'] = str(json_error)

            return result

        except Exception as e:
            return {
                'status_code': 0,
                'success': False,
                'data': None,
                'error': str(e),
                'response_text': None
            }

    def test_health_check(self):
        """Test health check endpoint."""
        self.log("Testing health check...")
        result = self.make_request('GET', '/v1/health')
        if result['success']:
            self.log("[OK] Health check passed")
            return True
        else:
            self.log(f"[FAIL] Health check failed: {result['error']}")
            return False

    def test_list_campaigns(self):
        """Test GET /v1/campaigns."""
        self.log("Testing GET /v1/campaigns...")
        result = self.make_request('GET', '/v1/campaigns')

        if result['success']:
            campaigns = result['data'].get('campaigns', [])
            self.log(f"[OK] Found {len(campaigns)} campaigns")
            if campaigns:
                self.test_campaign_id = campaigns[0]['id']
                self.log(f"Using test campaign ID: {self.test_campaign_id}")
            return True
        else:
            self.log(f"[FAIL] List campaigns failed: {result['error']}")
            return False

    def test_get_campaign_detail(self):
        """Test GET /v1/campaigns/{id}."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for detail test")
            return False

        self.log(f"Testing GET /v1/campaigns/{self.test_campaign_id}...")
        result = self.make_request('GET', f'/v1/campaigns/{self.test_campaign_id}')

        if result['success']:
            campaign = result['data']
            self.log("[OK] Campaign detail retrieved successfully")
            self.log(f"   Name: {campaign.get('name')}")
            self.log(f"   Status: {campaign.get('status')}")
            self.log(f"   Performance data: {'performance' in campaign}")
            self.log(f"   Links: {'_links' in campaign}")
            return True
        else:
            self.log(f"[FAIL] Get campaign detail failed: {result['error']}")
            return False

    def test_create_campaign(self):
        """Test POST /v1/campaigns."""
        self.log("Testing POST /v1/campaigns...")

        campaign_data = {
            "name": "Test Campaign API",
            "description": "Created via API test",
            "costModel": "CPA",
            "payout": {
                "amount": 15.00,
                "currency": "USD"
            },
            "dailyBudget": {
                "amount": 200.00,
                "currency": "USD"
            },
            "totalBudget": {
                "amount": 5000.00,
                "currency": "USD"
            },
            "safePage": "https://example.com/safe",
            "offerPage": "https://example.com/offer"
        }

        result = self.make_request('POST', '/v1/campaigns', campaign_data)

        if result['success']:
            new_campaign = result['data']
            self.log("[OK] Campaign created successfully")
            self.log(f"   New ID: {new_campaign.get('id')}")
            self.log(f"   Name: {new_campaign.get('name')}")
            return True
        else:
            self.log(f"[FAIL] Create campaign failed: {result['error']}")
            return False

    def test_update_campaign(self):
        """Test PUT /v1/campaigns/{id}."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for update test")
            return False

        self.log(f"Testing PUT /v1/campaigns/{self.test_campaign_id}...")

        update_data = {
            "name": "Updated Test Campaign",
            "description": "Updated via API test",
            "costModel": "CPC",
            "payout": {
                "amount": 20.00,
                "currency": "USD"
            }
        }

        result = self.make_request('PUT', f'/v1/campaigns/{self.test_campaign_id}', update_data)

        if result['success']:
            updated_campaign = result['data']
            self.log("[OK] Campaign updated successfully")
            self.log(f"   Updated name: {updated_campaign.get('name')}")
            return True
        else:
            self.log(f"[FAIL] Update campaign failed: {result['error']}")
            return False

    def test_campaign_actions(self):
        """Test pause and resume actions."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for actions test")
            return False

        # Test pause
        self.log(f"Testing POST /v1/campaigns/{self.test_campaign_id}/pause...")
        result = self.make_request('POST', f'/v1/campaigns/{self.test_campaign_id}/pause')

        if result['success']:
            self.log("[OK] Campaign paused successfully")
        else:
            self.log(f"[FAIL] Pause campaign failed: {result['error']}")

        # Test resume
        self.log(f"Testing POST /v1/campaigns/{self.test_campaign_id}/resume...")
        result = self.make_request('POST', f'/v1/campaigns/{self.test_campaign_id}/resume')

        if result['success']:
            self.log("[OK] Campaign resumed successfully")
            return True
        else:
            self.log(f"[FAIL] Resume campaign failed: {result['error']}")
            return False

    def test_analytics(self):
        """Test analytics endpoint."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for analytics test")
            return False

        # Try with the first campaign from the list (should have data)
        campaigns_result = self.make_request('GET', '/v1/campaigns?page=1&pageSize=1')
        if campaigns_result['success']:
            campaigns = campaigns_result['data'].get('campaigns', [])
            if campaigns:
                test_id = campaigns[0]['id']
                self.log(f"Testing analytics with existing campaign: {test_id}")
            else:
                test_id = self.test_campaign_id
        else:
            test_id = self.test_campaign_id

        self.log(f"Testing GET /v1/campaigns/{test_id}/analytics...")
        result = self.make_request('GET', f'/v1/campaigns/{test_id}/analytics')

        if result['success']:
            analytics = result['data']
            self.log("[OK] Analytics retrieved successfully")
            self.log(f"   Campaign ID: {analytics.get('campaignId')}")
            metrics = analytics.get('metrics', {})
            self.log(f"   Clicks: {metrics.get('clicks')}")
            self.log(f"   Conversions: {metrics.get('conversions')}")
            self.log(f"   Revenue: {metrics.get('revenue')}")
            return True
        else:
            self.log(f"[FAIL] Analytics failed: HTTP {result['status_code']}")
            if result['error']:
                self.log(f"   Error: {result['error']}")
            elif result['response_text']:
                self.log(f"   Response: {result['response_text'][:200]}")
            if 'json_error' in result:
                self.log(f"   JSON Error: {result['json_error']}")
            return False

    def test_landing_pages(self):
        """Test landing pages endpoints."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for landing pages test")
            return False

        # Test GET landing pages
        self.log(f"Testing GET /v1/campaigns/{self.test_campaign_id}/landing-pages...")
        result = self.make_request('GET', f'/v1/campaigns/{self.test_campaign_id}/landing-pages')

        if result['success']:
            landing_pages = result['data']
            self.log("[OK] Landing pages retrieved successfully")
            pages = landing_pages.get('landingPages', [])
            self.log(f"   Found {len(pages)} landing pages")
            return True
        else:
            self.log(f"[FAIL] Landing pages failed: HTTP {result['status_code']}")
            if result['error']:
                self.log(f"   Error: {result['error']}")
            elif result['response_text']:
                self.log(f"   Response: {result['response_text'][:200]}")
            if 'json_error' in result:
                self.log(f"   JSON Error: {result['json_error']}")
            return False

    def test_offers(self):
        """Test offers endpoints."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for offers test")
            return False

        # Test GET offers
        self.log(f"Testing GET /v1/campaigns/{self.test_campaign_id}/offers...")
        result = self.make_request('GET', f'/v1/campaigns/{self.test_campaign_id}/offers')

        if result['success']:
            offers = result['data']
            self.log("[OK] Offers retrieved successfully")
            offers_list = offers.get('offers', [])
            pagination = offers.get('pagination', {})
            self.log(f"   Found {len(offers_list)} offers")
            self.log(f"   Pagination: {pagination}")
            return True
        else:
            self.log(f"[FAIL] Offers failed: HTTP {result['status_code']}")
            if result['error']:
                self.log(f"   Error: {result['error']}")
            elif result['response_text']:
                self.log(f"   Response: {result['response_text'][:200]}")
            if 'json_error' in result:
                self.log(f"   JSON Error: {result['json_error']}")
            return False

    def test_campaigns_pagination(self):
        """Test campaigns pagination."""
        self.log("Testing campaigns pagination...")

        # Test with different page sizes
        test_cases = [
            {'page': 1, 'pageSize': 5},
            {'page': 2, 'pageSize': 3},
            {'page': 1, 'pageSize': 10},
        ]

        for params in test_cases:
            query_string = f"?page={params['page']}&pageSize={params['pageSize']}"
            result = self.make_request('GET', f'/v1/campaigns{query_string}')

            if not result['success']:
                self.log(f"[FAIL] Pagination failed for {query_string}: HTTP {result['status_code']}")
                return False

            data = result['data']
            campaigns = data.get('campaigns', [])
            pagination = data.get('pagination', {})

            # Validate pagination structure
            required_fields = ['page', 'pageSize', 'totalItems', 'totalPages', 'hasNext', 'hasPrev']
            missing_fields = [field for field in required_fields if field not in pagination]

            if missing_fields:
                self.log(f"[FAIL] Missing pagination fields {missing_fields} for {query_string}")
                return False

            # Validate pagination values
            if pagination['page'] != params['page']:
                self.log(f"[FAIL] Page mismatch: expected {params['page']}, got {pagination['page']}")
                return False

            if pagination['pageSize'] != params['pageSize']:
                self.log(f"[FAIL] Page size mismatch: expected {params['pageSize']}, got {pagination['pageSize']}")
                return False

            if len(campaigns) > params['pageSize']:
                self.log(f"[FAIL] Too many items returned: {len(campaigns)} > {params['pageSize']}")
                return False

            self.log(f"[OK] Pagination {query_string}: {len(campaigns)} items, page {pagination['page']}/{pagination['totalPages']}")

        # Test invalid parameters
        invalid_cases = [
            "?page=0&pageSize=10",  # page < 1
            "?page=1&pageSize=0",   # pageSize < 1
            "?page=1&pageSize=101", # pageSize > 100
        ]

        for query_string in invalid_cases:
            result = self.make_request('GET', f'/v1/campaigns{query_string}')
            if result['status_code'] != 400:
                self.log(f"[FAIL] Invalid params {query_string} should return 400, got {result['status_code']}")
                return False
            self.log(f"[OK] Invalid params {query_string} correctly rejected (400)")

        self.log("[OK] Campaigns pagination tests passed")
        return True

    def test_landing_pages_pagination(self):
        """Test landing pages pagination."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for landing pages pagination test")
            return False

        self.log(f"Testing landing pages pagination for campaign {self.test_campaign_id}...")

        # Test basic pagination
        test_cases = [
            {'page': 1, 'pageSize': 10},
            {'page': 1, 'pageSize': 5},
        ]

        for params in test_cases:
            query_string = f"?page={params['page']}&pageSize={params['pageSize']}"
            result = self.make_request('GET', f'/v1/campaigns/{self.test_campaign_id}/landing-pages{query_string}')

            if not result['success']:
                self.log(f"[FAIL] Landing pages pagination failed for {query_string}: HTTP {result['status_code']}")
                return False

            data = result['data']
            landing_pages = data.get('landingPages', [])
            pagination = data.get('pagination', {})

            # Validate pagination structure
            required_fields = ['page', 'pageSize', 'totalItems', 'totalPages', 'hasNext', 'hasPrev']
            missing_fields = [field for field in required_fields if field not in pagination]

            if missing_fields:
                self.log(f"[FAIL] Missing pagination fields {missing_fields} for landing pages {query_string}")
                return False

            if len(landing_pages) > params['pageSize']:
                self.log(f"[FAIL] Too many landing pages returned: {len(landing_pages)} > {params['pageSize']}")
                return False

            self.log(f"[OK] Landing pages pagination {query_string}: {len(landing_pages)} items")

        self.log("[OK] Landing pages pagination tests passed")
        return True

    def test_offers_pagination(self):
        """Test offers pagination."""
        if not self.test_campaign_id:
            self.log("[FAIL] No campaign ID available for offers pagination test")
            return False

        self.log(f"Testing offers pagination for campaign {self.test_campaign_id}...")

        # Test basic pagination
        test_cases = [
            {'page': 1, 'pageSize': 10},
            {'page': 1, 'pageSize': 5},
        ]

        for params in test_cases:
            query_string = f"?page={params['page']}&pageSize={params['pageSize']}"
            result = self.make_request('GET', f'/v1/campaigns/{self.test_campaign_id}/offers{query_string}')

            if not result['success']:
                self.log(f"[FAIL] Offers pagination failed for {query_string}: HTTP {result['status_code']}")
                return False

            data = result['data']
            offers = data.get('offers', [])
            pagination = data.get('pagination', {})

            # Validate pagination structure
            required_fields = ['page', 'pageSize', 'totalItems', 'totalPages', 'hasNext', 'hasPrev']
            missing_fields = [field for field in required_fields if field not in pagination]

            if missing_fields:
                self.log(f"[FAIL] Missing pagination fields {missing_fields} for offers {query_string}")
                return False

            if len(offers) > params['pageSize']:
                self.log(f"[FAIL] Too many offers returned: {len(offers)} > {params['pageSize']}")
                return False

            self.log(f"[OK] Offers pagination {query_string}: {len(offers)} items")

        self.log("[OK] Offers pagination tests passed")
        return True

    def test_pagination_edge_cases(self):
        """Test pagination edge cases."""
        self.log("Testing pagination edge cases...")

        # Test large page number (should return empty or last page)
        result = self.make_request('GET', '/v1/campaigns?page=999&pageSize=10')
        if not result['success']:
            self.log(f"[FAIL] Large page number failed: HTTP {result['status_code']}")
            return False

        data = result['data']
        campaigns = data.get('campaigns', [])
        pagination = data.get('pagination', {})

        if len(campaigns) > 10:
            self.log(f"[FAIL] Too many campaigns for large page: {len(campaigns)}")
            return False

        self.log(f"[OK] Large page handled correctly: {len(campaigns)} campaigns")

        # Test default parameters (no query params)
        result = self.make_request('GET', '/v1/campaigns')
        if not result['success']:
            self.log(f"[FAIL] Default params failed: HTTP {result['status_code']}")
            return False

        data = result['data']
        pagination = data.get('pagination', {})

        if pagination.get('page') != 1 or pagination.get('pageSize') != 20:
            self.log(f"[FAIL] Wrong defaults: page={pagination.get('page')}, pageSize={pagination.get('pageSize')}")
            return False

        self.log("[OK] Default pagination parameters work correctly")
        self.log("[OK] Pagination edge cases tests passed")
        return True

    def run_all_tests(self):
        """Run all business logic tests."""
        self.log("=" * 60)
        self.log("STARTING BUSINESS LOGIC TESTS")
        self.log("=" * 60)

        tests = [
            ("Health Check", self.test_health_check),
            ("List Campaigns", self.test_list_campaigns),
            ("Get Campaign Detail", self.test_get_campaign_detail),
            ("Create Campaign", self.test_create_campaign),
            ("Update Campaign", self.test_update_campaign),
            ("Campaign Actions (Pause/Resume)", self.test_campaign_actions),
            ("Analytics", self.test_analytics),
            ("Landing Pages", self.test_landing_pages),
            ("Offers", self.test_offers),
            ("Campaigns Pagination", self.test_campaigns_pagination),
            ("Landing Pages Pagination", self.test_landing_pages_pagination),
            ("Offers Pagination", self.test_offers_pagination),
            ("Pagination Edge Cases", self.test_pagination_edge_cases),
        ]

        results = []
        for test_name, test_func in tests:
            self.log(f"\n--- Testing {test_name} ---")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.log(f"[FAIL] Test {test_name} crashed: {e}")
                results.append((test_name, False))

        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)

        passed = 0
        total = len(results)

        for test_name, result in results:
            status = "[OK] PASS" if result else "[FAIL] FAIL"
            self.log(f"{status}: {test_name}")
            if result:
                passed += 1

        self.log(f"\nTOTAL: {passed}/{total} tests passed")

        if passed == total:
            self.log("[SUCCESS] ALL TESTS PASSED! Business logic and pagination are working correctly.")
        else:
            self.log(f"[WARN]  {total - passed} tests failed. Check the logs above for details.")

        # Detailed breakdown
        core_tests = 9  # Original business logic tests
        pagination_tests = 4  # New pagination tests

        core_passed = sum(1 for name, result in results[:core_tests] if result)
        pagination_passed = sum(1 for name, result in results[core_tests:] if result)

        self.log(f"\nBreakdown:")
        self.log(f"  Core Business Logic: {core_passed}/{core_tests} [OK]")
        self.log(f"  Pagination Tests: {pagination_passed}/{pagination_tests} [OK]")

        return passed == total


def main():
    """Main test function."""
    tester = CampaignAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
