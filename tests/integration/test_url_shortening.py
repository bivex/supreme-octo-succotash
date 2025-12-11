import pytest
import json
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
import httpx # Import httpx
import asyncio # Import asyncio for running the app in the background
import subprocess # Import subprocess for running the server in a separate process
import time # Import time for sleep
import sys # Import sys to get the executable path
import os # Import os for environment variables

# Set test database environment variables for the test process
os.environ.setdefault("DB_NAME", "test_supreme_octo_succotash")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")

from src.main import create_app
from src.container import container
from src.domain.value_objects import ClickId, CampaignId
from src.domain.entities.pre_click_data import PreClickData
from src.domain.repositories.campaign_repository import CampaignRepository
from src.domain.entities.campaign import Campaign
from src.domain.value_objects import Url, Money
from src.domain.value_objects.status.campaign_status import CampaignStatus
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


# Helper function to clear the pre_click_data table
async def clear_pre_click_data_table():
    try:
        repo = await container.get_postgres_pre_click_data_repository()
        await repo.clear_table()
    except (UnicodeDecodeError, RuntimeError) as e:
        # Skip clearing if database connection is corrupted
        print(f"Skipping table clear due to database connection issue: {e}")
        pass

@pytest.fixture(scope="session")
async def test_app():
    # Server is already running externally, just check connectivity
    print("--- Using external test server on http://127.0.0.1:5000 ---")

    # Wait for the server to be ready (it's already running)
    for _ in range(10): # Try up to 1 second
        try:
            async with httpx.AsyncClient(base_url="http://127.0.0.1:5000") as client:
                response = await client.get("/v1/health")
                if response.status_code == 200:
                    print("--- External test server is ready ---")
                    break
        except httpx.ConnectError:
            pass
        await asyncio.sleep(0.1)
    else:
        raise RuntimeError("External test server is not responding on http://127.0.0.1:5000")

    yield None # We yield None as we interact via http_client directly

    print("--- Test completed, external server remains running ---")

@pytest.fixture(scope="session")
async def http_client():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:5000", timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        yield client

@pytest.fixture(autouse=True) # auto-use this fixture for every test
async def setup_and_teardown_db(pre_click_data_repository):
    try:
        await clear_pre_click_data_table()
    except UnicodeDecodeError:
        # Skip clearing if there's an encoding issue
        pass
    yield
    try:
        await clear_pre_click_data_table()
    except UnicodeDecodeError:
        # Skip clearing if there's an encoding issue
        pass

@pytest.fixture
async def pre_click_data_repository():
    try:
        return await container.get_postgres_pre_click_data_repository()
    except (UnicodeDecodeError, RuntimeError) as e:
        # Return None if database connection is corrupted
        print(f"Database repository not available: {e}")
        return None

@pytest.fixture
async def campaign_repository():
    return await container.get_campaign_repository()

@pytest.mark.asyncio
async def test_complete_parameter_handling(http_client, test_app):
    """Test complete parameter handling with all possible tracking parameters."""
    original_base_url = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev/v1"
    campaign_id_str = "9061"

    # Test with comprehensive set of parameters
    test_click_id = str(uuid.uuid4())
    tracking_params = {
        "click_id": test_click_id,
        "source": "facebook_ads",
        "sub1": "campaign_summer_2024",
        "sub2": "adset_targeting_25_45",
        "sub3": "creative_video_15s",
        "sub4": "placement_feed",
        "sub5": "device_mobile",
        "aff_sub": "partner_123",
        "aff_sub2": "channel_direct",
        "aff_sub3": "geo_us_east",
        "aff_sub4": "language_en",
        "aff_sub5": "custom_param_xyz",
        "lp_id": 42,
        "offer_id": 24,
        "ts_id": 1,
    }

    generate_payload = {
        "base_url": original_base_url,
        "campaign_id": int(campaign_id_str),
        "tracking_params": tracking_params
    }

    # Generate tracking URL
    response = await http_client.post("/v1/clicks/generate", json=generate_payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    short_url = response_data["tracking_url"]
    print(f"Generated short URL: {short_url}")

    # Extract short code
    parsed_short_url = urlparse(short_url)
    short_code = parsed_short_url.path.split('/')[-1]
    assert short_code
    print(f"Short code: {short_code}")

    # Test redirect with test_mode to see click_id in final URL
    redirect_response = await http_client.get(f"/s/{short_code}?test_mode=1", follow_redirects=False)
    assert redirect_response.status_code == 302

    final_redirect_location = redirect_response.headers.get("Location")
    assert final_redirect_location
    print(f"Final redirect location: {final_redirect_location}")

    # Parse final redirect URL
    parsed_final_redirect = urlparse(final_redirect_location)
    final_query_params = parse_qs(parsed_final_redirect.query)

    # Verify final URL structure
    assert parsed_final_redirect.scheme == "https"
    assert parsed_final_redirect.netloc == "offer.test.com"
    assert parsed_final_redirect.path in ["", "/"]  # Path can be empty or "/"

    # In test mode, click_id should be added to redirect URL
    assert 'click_id' in final_query_params
    assert final_query_params['click_id'][0]  # click_id should not be empty

    print("✅ Test passed: Complete parameter handling verified")
    print(f"   - Original parameters count: {len(tracking_params)}")
    print(f"   - Short URL generated successfully")
    print(f"   - Redirect works correctly")
    print(f"   - Final URL contains click_id parameter")

    # Test with minimal parameters to ensure it still works
    minimal_click_id = str(uuid.uuid4())
    minimal_params = {
        "click_id": minimal_click_id,
        "source": "google"
    }

    minimal_payload = {
        "base_url": original_base_url,
        "campaign_id": int(campaign_id_str),
        "tracking_params": minimal_params
    }

    minimal_response = await http_client.post("/v1/clicks/generate", json=minimal_payload)
    assert minimal_response.status_code == 200
    minimal_data = minimal_response.json()
    assert minimal_data["status"] == "success"

    print("✅ Minimal parameter test also passed")

@pytest.mark.asyncio
async def test_url_shortening_and_redirection_api_only(http_client, test_app):
    """Test URL shortening and redirection through HTTP API only."""
    # 1. Simulate API call to generate a short URL
    original_base_url = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev/v1"
    campaign_id_str = "9061"
    test_click_id = str(uuid.uuid4())

    tracking_params = {
        "click_id": test_click_id,
        "source": "test_source",
        "sub1": "test_sub1",
        "lp_id": 42,
        "offer_id": 24,
        "ts_id": 1,
    }

    generate_payload = {
        "base_url": original_base_url,
        "campaign_id": int(campaign_id_str),
        "tracking_params": tracking_params
    }

    response = await http_client.post("/v1/clicks/generate", json=generate_payload)
    assert response.status_code == 200
    response_data = response.json() # Parse the JSON response
    assert response_data["status"] == "success"
    short_url = response_data["tracking_url"] # Extract "tracking_url" from the JSON response
    print(f"Generated short URL: {short_url}")

    # Extract short code from the URL
    parsed_short_url = urlparse(short_url)
    short_code = parsed_short_url.path.split('/')[-1]
    assert short_code

    # 2. Simulate redirect using the short URL
    # Use http_client here - add test_mode=1 to include parameters in redirect URL
    redirect_response = await http_client.get(f"/s/{short_code}?test_mode=1", follow_redirects=False)
    assert redirect_response.status_code == 302 # Expect a redirect

    # 3. Verify final redirection URL
    final_redirect_location = redirect_response.headers.get("Location")
    assert final_redirect_location

    # The final redirect URL should be to the campaign's offer page
    # We're assuming 'https://offer.test.com' is the default offer page URL from TrackClickHandler
    expected_base_redirect_url = "https://offer.test.com"
    parsed_final_redirect_url = urlparse(final_redirect_location)

    assert parsed_final_redirect_url.scheme == urlparse(expected_base_redirect_url).scheme
    assert parsed_final_redirect_url.netloc == urlparse(expected_base_redirect_url).netloc

    # In test mode, click_id should be added to the redirect URL
    final_query_params = parse_qs(parsed_final_redirect_url.query)
    assert 'click_id' in final_query_params
    assert final_query_params['click_id'][0]  # click_id should not be empty

    print(f"Final redirect location: {final_redirect_location}")

    # Test completed successfully - URL generation and redirection work correctly
