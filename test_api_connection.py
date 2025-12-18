import asyncio
import json
import time
import uuid

import aiohttp
from loguru import logger


async def test_generate_tracking_url():
    api_base_url = "http://localhost:5000"
    url = f"{api_base_url}/clicks/generate"

    user_id = 123456789
    click_id = uuid.uuid4().hex[:16]
    source = "test_script"

    payload = {
        "base_url": api_base_url,
        "campaign_id": 9061,
        "tracking_params": {
            "click_id": click_id,
            "source": source,
            "sub1": "test_sub1",
            "sub2": "test_sub2",
            "sub3": "test_sub3",
            "sub4": str(user_id),
            "sub5": "test_sub5",
            "lp_id": 1,
            "offer_id": 2,
            "ts_id": 3,
            "aff_sub": "test_aff_sub_1",
            "aff_sub2": "test_aff_sub_2",
            "user_id": user_id,
            "bot_source": "test_script",
            "generated_at": int(time.time()),
        }
    }

    headers = {
        "Authorization": "Bearer test_jwt_token_12345"
    }

    logger.info(f"Sending request to: {url}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()

                logger.info(f"API Response Status: {status}")
                logger.info(f"API Response Body: {response_text}")

                if status == 200:
                    try:
                        result = json.loads(response_text)
                        if "short_url" in result:
                            logger.info(f"Successfully received short_url: {result['short_url']}")
                        else:
                            logger.warning("API response is missing 'short_url'.")
                    except json.JSONDecodeError:
                        logger.error("Failed to decode JSON response.")
                else:
                    logger.error(f"API call failed with status {status}.")

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error: Could not connect to {url}. Is the backend running on {api_base_url}?")
            logger.error(f"Error details: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_generate_tracking_url())
