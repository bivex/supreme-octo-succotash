#!/usr/bin/env python3
"""
API Endpoints Testing Script

Tests all API endpoints for the Advertising Platform API based on OpenAPI specification.
Base URL: http://127.0.0.1:5000/v1/

This script comprehensively tests all endpoints defined in openapi.yaml including:
- Health checks
- Campaign management (CRUD, pause/resume)
- Landing page management
- Offer management
- Analytics
- Click tracking (public and authenticated)
"""

import requests
import json
import time
import sys
import uuid
from typing import Dict, Any, List
from loguru import logger
# Configuration
BASE_URL = "http://127.0.0.1:5000/v1"
AUTH_HEADERS = {"Authorization": "Bearer test_jwt_token_12345"}
TIMEOUT = 10

class APIEndpointTester:
    """Test all API endpoints systematically."""

    def __init__(self, base_url: str, auth_headers: Dict[str, str]):
        self.base_url = base_url.rstrip('/')
        self.auth_headers = auth_headers
        self.session = requests.Session()
        self.session.headers.update(auth_headers)
        self.results = []

    def test_endpoint(self, method: str, path: str, description: str,
                     data: Dict[str, Any] = None, expected_status: int = 200,
                     skip_auth: bool = False, allow_redirects: bool = True) -> Dict[str, Any]:
        """Test a single endpoint with comprehensive validation."""
        url = f"{self.base_url}{path}"
        headers = {} if skip_auth else self.auth_headers.copy()
        headers['Content-Type'] = 'application/json'

        start_time = time.time()
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=TIMEOUT, allow_redirects=allow_redirects)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=TIMEOUT, allow_redirects=allow_redirects)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=TIMEOUT, allow_redirects=allow_redirects)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=TIMEOUT, allow_redirects=allow_redirects)
            else:
                return {
                    'endpoint': f"{method} {path}",
                    'description': description,
                    'status': 'FAILED',
                    'error': f'Unsupported HTTP method: {method}',
                    'response_status': None,
                    'response_time': 0,
                    'url': url
                }

            response_time = time.time() - start_time

            # Check status
            status_ok = response.status_code == expected_status

            result = {
                'endpoint': f"{method} {path}",
                'description': description,
                'status': 'PASSED' if status_ok else 'FAILED',
                'response_status': response.status_code,
                'expected_status': expected_status,
                'response_time': response_time,
                'content_length': len(response.content),
                'url': url,
                'error': None if status_ok else f"Expected {expected_status}, got {response.status_code}",
                'response_body': response.text[:500] if not status_ok else None  # Include response body for failed tests
            }

            # Enhanced JSON validation
            json_data = None
            try:
                json_data = response.json()
                result['json_valid'] = True
                result['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else None
                result['json_size'] = len(json.dumps(json_data)) if json_data else 0
            except (ValueError, json.JSONDecodeError):
                result['json_valid'] = False
                result['json_keys'] = None
                result['json_size'] = 0

            # Additional validations for specific response types
            if expected_status in [200, 201] and method.upper() != 'DELETE':
                if result['json_valid']:
                    result['response_structure'] = 'valid_json'
                elif response.headers.get('content-type', '').startswith('text/html'):
                    result['response_structure'] = 'html'
                else:
                    result['response_structure'] = 'other'

            # Check for redirect information
            if response.status_code in [301, 302, 303, 307, 308]:
                result['redirect_location'] = response.headers.get('Location', 'N/A')
                result['redirect_type'] = 'temporary' if response.status_code in [302, 303, 307] else 'permanent'

            return result

        except requests.exceptions.Timeout:
            return {
                'endpoint': f"{method} {path}",
                'description': description,
                'status': 'ERROR',
                'error': f'Timeout after {TIMEOUT} seconds',
                'response_status': None,
                'response_time': time.time() - start_time,
                'url': url
            }
        except requests.exceptions.ConnectionError:
            return {
                'endpoint': f"{method} {path}",
                'description': description,
                'status': 'ERROR',
                'error': 'Connection failed',
                'response_status': None,
                'response_time': time.time() - start_time,
                'url': url
            }
        except requests.exceptions.RequestException as e:
            return {
                'endpoint': f"{method} {path}",
                'description': description,
                'status': 'ERROR',
                'error': f'Request error: {str(e)}',
                'response_status': None,
                'response_time': time.time() - start_time,
                'url': url
            }

    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all endpoint tests."""
        logger.info(f"Testing API endpoints at {self.base_url}")
        logger.info("=" * 60)

        # Test data based on OpenAPI schemas
        test_campaign_data = {
            "name": "Test Campaign API",
            "description": "Campaign created via API test",
            "costModel": "CPA",
            "payout": {"amount": 25.50, "currency": "USD"},
            "whiteUrl": "https://example.com/safe",
            "blackUrl": "https://example.com/offer",
            "dailyBudget": {"amount": 500.00, "currency": "USD"},
            "totalBudget": {"amount": 15000.00, "currency": "USD"},
            "startDate": "2024-01-01T00:00:00Z",
            "endDate": "2024-12-31T23:59:59Z"
        }

        test_campaign_update_data = {
            "name": "Updated Test Campaign",
            "description": "Campaign updated via API test",
            "payout": {"amount": 30.00, "currency": "USD"},
            "dailyBudget": {"amount": 600.00, "currency": "USD"}
        }

        test_landing_page_data = {
            "name": "Test Landing Page",
            "url": "https://example.com/test-landing",
            "pageType": "squeeze",
            "weight": 100,
            "isActive": True,
            "isControl": False
        }

        test_offer_data = {
            "name": "Test Campaign Offer",
            "url": "https://affiliate.com/test-offer",
            "offerType": "direct",
            "payout": {"amount": 25.50, "currency": "USD"},
            "weight": 100,
            "isActive": True,
            "isControl": False
        }

        # Generate test IDs
        test_campaign_id = "camp_test_123"
        test_click_id = str(uuid.uuid4())

        # Test endpoints - comprehensive coverage based on OpenAPI spec
        tests = [
            # ============================================================================
            # HEALTH CHECK
            # ============================================================================
            ('GET', '/health', 'Health check endpoint (public)', None, 200, True),

            # ============================================================================
            # CAMPAIGN MANAGEMENT
            # ============================================================================
            ('GET', '/campaigns', 'List campaigns with pagination', None, 200, False),
            ('GET', '/campaigns?page=1&pageSize=10', 'List campaigns with pagination params', None, 200, False),
            ('POST', '/campaigns', 'Create new campaign', test_campaign_data, 201, False),
            ('GET', f'/campaigns/{test_campaign_id}', 'Get specific campaign by ID', None, 200, False),
            ('PUT', f'/campaigns/{test_campaign_id}', 'Update existing campaign', test_campaign_update_data, 200, False),
            ('POST', f'/campaigns/{test_campaign_id}/pause', 'Pause active campaign', {"reason": "Testing pause functionality"}, 200, False),
            ('POST', f'/campaigns/{test_campaign_id}/resume', 'Resume paused campaign', None, 200, False),
            ('DELETE', f'/campaigns/{test_campaign_id}', 'Delete campaign (admin)', None, 200, False),

            # ============================================================================
            # LANDING PAGES
            # ============================================================================
            ('GET', f'/campaigns/{test_campaign_id}/landing-pages', 'List campaign landing pages', None, 200, False),
            ('GET', f'/campaigns/{test_campaign_id}/landing-pages?page=1&pageSize=20', 'List landing pages with pagination', None, 200, False),
            ('POST', f'/campaigns/{test_campaign_id}/landing-pages', 'Create landing page for campaign', test_landing_page_data, 400, False),

            # ============================================================================
            # CAMPAIGN OFFERS
            # ============================================================================
            ('GET', f'/campaigns/{test_campaign_id}/offers', 'List campaign offers', None, 200, False),
            ('POST', f'/campaigns/{test_campaign_id}/offers', 'Create campaign offer', test_offer_data, 400, False),

            # ============================================================================
            # ANALYTICS
            # ============================================================================
            ('GET', f'/campaigns/{test_campaign_id}/analytics', 'Get campaign analytics overview', None, 200, False),
            ('GET', f'/campaigns/{test_campaign_id}/analytics?startDate=2024-01-01&endDate=2024-01-31&granularity=day', 'Get campaign analytics with date range', None, 200, False),
            ('GET', f'/campaigns/{test_campaign_id}/analytics?breakdown=date', 'Get campaign analytics with date breakdown', None, 200, False),

            # ============================================================================
            # CLICK TRACKING (PUBLIC ENDPOINTS)
            # ============================================================================
            ('GET', '/click?cid=123&sub1=test_creative', 'Track click - basic tracking', None, 302, True, False),
            ('GET', '/click?cid=123&sub1=fb_ad_15&sub2=facebook&sub3=prospecting', 'Track click - Facebook ad tracking', None, 302, True, False),
            ('GET', '/click?cid=123&sub1=google_search&click_id=USER123&aff_sub=network_a', 'Track click - affiliate tracking', None, 302, True, False),
            ('GET', '/click?cid=123&landing_page_id=456&campaign_offer_id=789', 'Track click - direct targeting', None, 302, True, False),

            # ============================================================================
            # CLICK TRACKING (AUTHENTICATED ENDPOINTS)
            # ============================================================================
            ('GET', f'/click/{test_click_id}', 'Get specific click details', None, 200, False),
            ('GET', '/clicks?limit=10', 'List clicks with limit', None, 200, False),
            ('GET', '/clicks?cid=123&limit=5', 'List clicks filtered by campaign', None, 200, False),
            ('GET', '/clicks?sub1=fb_ad_15&limit=5', 'List clicks filtered by sub1', None, 200, False),
            ('GET', '/clicks?is_valid=1&limit=10', 'List valid clicks only', None, 200, False),

            # ============================================================================
            # RESET ENDPOINT (for testing)
            # ============================================================================
            ('POST', '/reset', 'Reset mock data for testing', None, 200, False),
        ]

        results = []
        for test_data in tests:
            if len(test_data) == 6:
                method, path, description, data, expected_status, skip_auth = test_data
                allow_redirects = True
            else:
                method, path, description, data, expected_status, skip_auth, allow_redirects = test_data

            logger.info(f"Testing: {method} {path}")
            result = self.test_endpoint(method, path, description, data, expected_status, skip_auth, allow_redirects)
            results.append(result)
            status_icon = "PASS" if result['status'] == 'PASSED' else "FAIL" if result['status'] == 'FAILED' else "WARN"
            logger.info(f"  {status_icon} {result['status']} - {result.get('response_status', 'N/A')} ({result['response_time']:.2f}s)")
            if result['error']:
                logger.info(f"    Error: {result['error']}")
                if result.get('response_body'):
                    logger.info(f"    Response Body: {result['response_body']}")

        return results

    def print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print comprehensive test summary with categorization."""
        logger.info("\n" + "=" * 80)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)

        # Overall statistics
        passed = sum(1 for r in results if r['status'] == 'PASSED')
        failed = sum(1 for r in results if r['status'] == 'FAILED')
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        total = len(results)

        logger.info(f"Total endpoints tested: {total}")
        logger.info(f"✓ Passed: {passed}")
        logger.info(f"✗ Failed: {failed}")
        logger.info(f"⚠️  Errors: {errors}")

        # Categorize results by API section
        categories = {
            'Health': [],
            'Campaigns': [],
            'Landing Pages': [],
            'Offers': [],
            'Analytics': [],
            'Click Tracking': []
        }

        for result in results:
            endpoint = result['endpoint']
            if 'health' in endpoint.lower():
                categories['Health'].append(result)
            elif 'campaign' in endpoint.lower() and 'landing-page' not in endpoint.lower() and 'offer' not in endpoint.lower() and 'analytic' not in endpoint.lower():
                categories['Campaigns'].append(result)
            elif 'landing-page' in endpoint.lower():
                categories['Landing Pages'].append(result)
            elif 'offer' in endpoint.lower():
                categories['Offers'].append(result)
            elif 'analytic' in endpoint.lower():
                categories['Analytics'].append(result)
            elif 'click' in endpoint.lower():
                categories['Click Tracking'].append(result)

        # Print categorized results
        logger.info("\n" + "-" * 80)
        logger.info("RESULTS BY CATEGORY")
        logger.info("-" * 80)

        for category, category_results in categories.items():
            if not category_results:
                continue

            cat_passed = sum(1 for r in category_results if r['status'] == 'PASSED')
            cat_failed = sum(1 for r in category_results if r['status'] == 'FAILED')
            cat_errors = sum(1 for r in category_results if r['status'] == 'ERROR')
            cat_total = len(category_results)

            status_icon = "✓" if cat_failed == 0 and cat_errors == 0 else "✗" if cat_failed > 0 else "⚠️"
            logger.info(f"{status_icon} {category}: {cat_passed}/{cat_total} passed")

            # Show failed tests in this category
            failed_tests = [r for r in category_results if r['status'] in ['FAILED', 'ERROR']]
            if failed_tests:
                for test in failed_tests:
                    logger.info(f"    ✗ {test['endpoint']}: {test['error']}")
                    if test.get('response_body'):
                        logger.info(f"        Response Body: {test['response_body']}")

        # Detailed failed tests section
        all_failed = [r for r in results if r['status'] in ['FAILED', 'ERROR']]
        if all_failed:
            logger.info("\n" + "-" * 80)
            logger.info("DETAILED FAILED TESTS")
            logger.info("-" * 80)
            for result in all_failed:
                logger.info(f"✗ {result['endpoint']}")
                logger.info(f"    Expected: {result['expected_status']}, Got: {result.get('response_status', 'N/A')}")
                if result['error']:
                    logger.info(f"    Error: {result['error']}")
                if result.get('response_body'):
                    logger.info(f"    Response Body: {result['response_body']}")
                logger.info("")

        # Success rate and conclusion
        success_rate = (passed / total) * 100 if total > 0 else 0
        logger.info("=" * 80)
        logger.info(f"OVERALL SUCCESS RATE: {success_rate:.1f}%")
        logger.info("=" * 80)

        if success_rate >= 95:
            logger.success("🎉 EXCELLENT: All API endpoints are working correctly!")
        elif success_rate >= 90:
            logger.success("✅ SUCCESS: API endpoints are working correctly!")
        elif success_rate >= 70:
            logger.warning("⚠️  WARNING: Some endpoints have issues but most are working.")
        else:
            logger.error("❌ ERROR: Major issues with API endpoints detected.")


def main():
    """Main function."""
    logger.info("Advertising Platform API Endpoint Tester")
    logger.info("=========================================")
    logger.info("Comprehensive testing based on OpenAPI specification")
    logger.info("")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            logger.error("ERROR: Server is not responding correctly. Please start the server first.")
            logger.info("   Run: python main_clean.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        logger.error("ERROR: Cannot connect to server. Please start the server first.")
        logger.info("   Run: python main_clean.py")
        sys.exit(1)

    logger.info("✓ Server is running. Starting comprehensive endpoint tests...\n")

    # Run tests
    tester = APIEndpointTester(BASE_URL, AUTH_HEADERS)
    results = tester.run_all_tests()
    tester.print_summary(results)

    # Exit with appropriate code based on success rate
    passed = sum(1 for r in results if r['status'] == 'PASSED')
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0

    if success_rate >= 90:
        logger.success("🎉 All tests passed! API is fully functional.")
        sys.exit(0)
    elif success_rate >= 70:
        logger.warning("⚠️  Most tests passed but some issues detected.")
        sys.exit(1)
    else:
        logger.error("❌ Major issues detected with API endpoints.")
        sys.exit(1)


if __name__ == '__main__':
    main()
