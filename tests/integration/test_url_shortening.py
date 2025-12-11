import pytest
import json
import uuid
from urllib.parse import urlparse, parse_qs
import httpx # Import httpx
import asyncio # Import asyncio for running the app in the background

from src.main import create_app
from src.container import container
from src.domain.value_objects import ClickId, CampaignId
from src.domain.entities.pre_click_data import PreClickData

@pytest.fixture(scope="session")
async def test_app():
    # Run the Socketify app in the background
    app = await create_app() # This creates the app instance

    # Use asyncio.Server to serve the app
    loop = asyncio.get_event_loop()
    # Assuming create_app returns an object with a .app property that is the uWSGI app
    # If create_app returns the raw uWSGI app, then just use 'app'
    server = await loop.create_server(app.asgi_app if hasattr(app, 'asgi_app') else app, host='127.0.0.1', port=5000) # Assuming app has asgi_app or is the asgi_app itself

    print("\n--- Starting test server on http://127.0.0.1:5000 ---")
    asyncio.create_task(server.serve_forever())

    yield app # Yield the app instance, not the server

    print("\n--- Stopping test server ---")
    server.close()
    await server.wait_closed()

@pytest.fixture(scope="session")
async def http_client():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:5000") as client:
        yield client

@pytest.fixture
async def pre_click_data_repository():
    return await container.get_postgres_pre_click_data_repository()

async def test_url_shortening_and_redirection(http_client, pre_click_data_repository, test_app):
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
    response_data = await response.json()
    assert response_data["status"] == "success"
    short_url = response_data["short_url"]
    print(f"Generated short URL: {short_url}")

    # Extract short code from the URL
    parsed_short_url = urlparse(short_url)
    short_code = parsed_short_url.path.split('/')[-1]
    assert short_code

    # 2. Validate data storage in PreClickDataRepository
    stored_pre_click_data = await pre_click_data_repository.find_by_click_id(ClickId(test_click_id))
    assert stored_pre_click_data is not None
    assert stored_pre_click_data.click_id.value == test_click_id
    assert stored_pre_click_data.campaign_id.value == f"camp_{campaign_id_str}"
    assert stored_pre_click_data.metadata.get('original_base_url') == original_base_url
    for key, value in tracking_params.items():
        if key != "click_id": # click_id is explicitly handled
            assert stored_pre_click_data.tracking_params.get(key) == str(value)

    # 3. Simulate redirect using the short URL
    # Use http_client here
    redirect_response = await http_client.get(f"/s/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 302 # Expect a redirect

    # 4. Verify final redirection URL
    final_redirect_location = redirect_response.headers.get("Location")
    assert final_redirect_location

    # The final redirect URL should be to the campaign's offer page
    # We're assuming 'https://offer.test.com' is the default offer page URL from TrackClickHandler
    expected_base_redirect_url = "https://offer.test.com"
    parsed_final_redirect_url = urlparse(final_redirect_location)

    assert parsed_final_redirect_url.scheme == urlparse(expected_base_redirect_url).scheme
    assert parsed_final_redirect_url.netloc == urlparse(expected_base_redirect_url).netloc

    # Verify parameters in the final redirect URL
    final_query_params = parse_qs(parsed_final_redirect_url.query)
    assert final_query_params.get('click_id') == [test_click_id]
    assert final_query_params.get('cid') == [campaign_id_str]
    assert final_query_params.get('source') == [tracking_params['source']]
    assert final_query_params.get('sub1') == [tracking_params['sub1']]
    assert final_query_params.get('lp_id') == [str(tracking_params['lp_id'])]
    assert final_query_params.get('offer_id') == [str(tracking_params['offer_id'])]
    assert final_query_params.get('ts_id') == [str(tracking_params['ts_id'])]

    print(f"Final redirect location: {final_redirect_location}")

    # Optional: Verify that PreClickData is deleted after successful redirection (if applicable)
    deleted_pre_click_data = await pre_click_data_repository.find_by_click_id(ClickId(test_click_id))
    assert deleted_pre_click_data is None # Expect data to be deleted after use
