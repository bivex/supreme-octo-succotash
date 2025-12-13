# Advertising Platform API Python SDK

A comprehensive Python SDK for the Advertising Platform API, generated from OpenAPI specification.

## Features

- **Domain-Driven Design**: API designed around business domains, not database tables
- **Full Type Safety**: Complete Pydantic models with validation
- **Async Support**: Both synchronous and asynchronous HTTP clients
- **Authentication**: JWT Bearer tokens and API key support
- **Error Handling**: Comprehensive exception hierarchy
- **Rate Limiting**: Built-in awareness of API rate limits
- **Pagination**: Automatic handling of paginated responses
- **Retry Logic**: Automatic retry with exponential backoff

## Installation

```bash
pip install -r requirements.txt
```

Or install specific dependencies:

```bash
pip install httpx>=0.24.0 pydantic>=2.0.0
```

## Quick Start

### Basic Usage

```python
from advertising_platform_sdk import AdvertisingPlatformClient

# Initialize client with bearer token
client = AdvertisingPlatformClient(
    base_url="https://api.advertising-platform.com/v1",
    bearer_token="your-jwt-token-here"
)

# Or use API key authentication
client = AdvertisingPlatformClient(
    api_key="your-api-key-here"
)

# Use context manager for automatic cleanup
with client:
    # Health check
    health = client.get_health()
    print(f"API Status: {health['status']}")

    # Get campaigns
    campaigns = client.get_campaigns(page=1, page_size=20)
    for campaign in campaigns['data']:
        print(f"Campaign: {campaign['name']}")
```

### Async Usage

```python
import asyncio
from advertising_platform_sdk import AdvertisingPlatformClient

async def main():
    client = AdvertisingPlatformClient(bearer_token="your-token")

    try:
        # Async health check
        health = await client.get_health_async()
        print(f"API Status: {health['status']}")

        # Async campaign operations
        campaigns = await client.get_campaigns_async()
        print(f"Found {len(campaigns['data'])} campaigns")

    finally:
        await client.close()

asyncio.run(main())
```

## API Methods

### Health Check

```python
# Check API health
health = client.get_health()
```

### Campaigns

```python
# List campaigns
campaigns = client.get_campaigns(
    page=1,
    page_size=20,
    status="active",
    search="summer campaign"
)

# Create campaign
new_campaign = client.create_campaign({
    "name": "Summer Sale Campaign",
    "status": "active",
    "budget": {"amount": 1000.0, "currency": "USD"}
})

# Get specific campaign
campaign = client.get_campaign("campaign-id-123")

# Update campaign
updated = client.update_campaign("campaign-id-123", {
    "name": "Updated Campaign Name",
    "status": "paused"
})

# Delete campaign
client.delete_campaign("campaign-id-123")

# Pause/Resume campaign
client.pause_campaign("campaign-id-123")
client.resume_campaign("campaign-id-123")
```

### Analytics

```python
# Get campaign analytics
analytics = client.get_campaign_analytics(
    campaign_id="campaign-id-123",
    start_date="2024-01-01",
    end_date="2024-01-31",
    breakdown="daily"
)

# Get real-time analytics
realtime = client.get_real_time_analytics(
    campaign_id="campaign-id-123",
    metric="clicks"
)
```

### Clicks

```python
# Track click
click_response = client.track_click({
    "campaign_id": "campaign-123",
    "click_id": "click-456",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1",
    "referrer": "https://example.com"
})

# Get click details
click = client.get_click("click-id-456")

# List clicks
clicks = client.get_clicks(
    campaign_id="campaign-123",
    page=1,
    page_size=50
)

# Generate click URL
click_url = client.generate_click({
    "campaign_id": "campaign-123",
    "landing_page_id": "page-456",
    "sub1": "source1",
    "sub2": "source2"
})

# Validate click
validation = client.validate_click("click-id-456")
```

### Conversions

```python
# Track conversion
conversion = client.track_conversion({
    "click_id": "click-456",
    "goal_id": "goal-123",
    "revenue": {"amount": 25.50, "currency": "USD"},
    "transaction_id": "txn-789"
})
```

### Goals

```python
# List goals
goals = client.get_goals(
    campaign_id="campaign-123",
    page=1,
    page_size=20
)

# Create goal
new_goal = client.create_goal({
    "name": "Purchase Goal",
    "campaign_id": "campaign-123",
    "type": "purchase",
    "value": {"amount": 50.0, "currency": "USD"}
})

# Get goal
goal = client.get_goal("goal-id-123")

# Update goal
updated_goal = client.update_goal("goal-id-123", {
    "name": "Updated Goal Name"
})

# Delete goal
client.delete_goal("goal-id-123")

# Duplicate goal
duplicated = client.duplicate_goal("goal-id-123")

# Get goal templates
templates = client.get_goal_templates()
```

## Error Handling

The SDK provides specific exceptions for different error types:

```python
from advertising_platform_sdk import AdvertisingPlatformClient
from advertising_platform_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    APIError,
)

client = AdvertisingPlatformClient(bearer_token="invalid-token")

try:
    campaigns = client.get_campaigns()
except AuthenticationError:
    print("Invalid authentication token")
except AuthorizationError:
    print("Insufficient permissions")
except RateLimitError:
    print("Rate limit exceeded, please retry later")
except ValidationError as e:
    print(f"Validation error: {e}")
except NotFoundError:
    print("Resource not found")
except APIError as e:
    print(f"API error: {e}")
```

## Data Models

The SDK includes comprehensive Pydantic models for all API entities:

```python
from advertising_platform_sdk.models import (
    Campaign, Click, Conversion, Goal, Money,
    CampaignAnalytics, ClickTrackingRequest
)

# Models provide full type safety and validation
campaign = Campaign(
    name="Test Campaign",
    status="active",
    budget=Money(amount=1000.0, currency="USD")
)
```

## Configuration

### Client Configuration

```python
client = AdvertisingPlatformClient(
    base_url="https://api.advertising-platform.com/v1",  # Default
    bearer_token="your-jwt-token",                       # Optional
    api_key="your-api-key",                             # Optional
    timeout=30.0,                                        # Default 30s
    max_retries=3,                                       # Default 3
)
```

### Environment Variables

You can configure the client using environment variables:

```bash
export ADVERTISING_PLATFORM_BASE_URL="https://api.example.com/v1"
export ADVERTISING_PLATFORM_BEARER_TOKEN="your-token"
export ADVERTISING_PLATFORM_API_KEY="your-key"
export ADVERTISING_PLATFORM_TIMEOUT="30.0"
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run specific test
pytest tests/test_client.py::TestAdvertisingPlatformClient::test_health_check
```

## Advanced Usage

### Custom HTTP Client

```python
import httpx
from advertising_platform_sdk.client import AdvertisingPlatformClient

# Use custom HTTP client configuration
custom_client = httpx.Client(
    timeout=60.0,
    proxies={"https": "https://proxy.example.com:8080"}
)

client = AdvertisingPlatformClient(bearer_token="token")
# The client will use its own HTTP client, but you can access it
sync_client = client._get_sync_client()
```

### Batch Operations

```python
# Process multiple campaigns
campaign_ids = ["id1", "id2", "id3"]

for campaign_id in campaign_ids:
    try:
        campaign = client.get_campaign(campaign_id)
        # Process campaign
        print(f"Processing: {campaign['name']}")
    except NotFoundError:
        print(f"Campaign {campaign_id} not found")
    except Exception as e:
        print(f"Error processing {campaign_id}: {e}")
```

### Monitoring and Logging

```python
import logging

logging.basicConfig(level=logging.INFO)

# The client will log HTTP requests/responses
client = AdvertisingPlatformClient(bearer_token="token")

# Enable debug logging for troubleshooting
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

## API Rate Limits

The API has the following rate limits:

- **Authenticated requests**: 60/minute, 1000/hour
- **Public requests**: 10/minute, burst limit 50

The SDK includes built-in rate limit handling and will automatically retry requests that hit rate limits.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This SDK is released under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:

- Create an issue on GitHub
- Check the API documentation at `/docs`
- Contact API support at api@advertising-platform.com