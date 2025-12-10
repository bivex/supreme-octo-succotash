"""
Test script for URLShortener functionality
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared_url_shortener import URLShortener

def test_url_shortener():
    """Test URLShortener basic functionality."""
    print("Testing URLShortener...")

    # Create shortener instance
    shortener = URLShortener()

    # Test URL to shorten
    original_url = "https://example.com/v1/click?cid=123&sub1=test&sub2=value&click_id=abc123"

    print(f"Original URL: {original_url}")

        # Shorten URL
    try:
        short_url, params = shortener.shorten_url(original_url)
        print(f"Short URL: {short_url}")
        print(f"Extracted params: {params}")
        print(f"Storage keys after shortening: {list(shortener.storage.keys())}")

        # Expand URL
        expanded_url, expanded_params = shortener.expand_url(short_url)
        print(f"Expanded URL: {expanded_url}")
        print(f"Expanded params: {expanded_params}")

        # Check storage has data
        if shortener.storage:
            print(f"✅ Storage has {len(shortener.storage)} entries")
        else:
            print("❌ Storage is empty")

        # Verify parameters match
        if params == expanded_params:
            print("✅ Parameters match - URL shortening works correctly!")
        else:
            print("❌ Parameters don't match!")
            return False

        # Test with different URL
        test_url2 = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev/v1/click?cid=camp_9061&sub1=telegram_bot&sub2=premium&sub3=callback_offer"
        print(f"\nTesting second URL: {test_url2}")

        short_url2, params2 = shortener.shorten_url(test_url2)
        print(f"Short URL 2: {short_url2}")

        expanded_url2, expanded_params2 = shortener.expand_url(short_url2)
        print(f"Expanded URL 2: {expanded_url2}")

        if params2 == expanded_params2:
            print("✅ Second URL test passed!")
        else:
            print("❌ Second URL test failed!")
            return False

        # Test invalid short URL
        invalid_expanded, invalid_params = shortener.expand_url("https://example.com/invalid")
        if invalid_expanded is None and invalid_params is None:
            print("✅ Invalid URL handling works correctly!")
        else:
            print("❌ Invalid URL handling failed!")
            return False

        print("\n🎉 All tests passed! URLShortener is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_global_instance():
    """Test the global URLShortener instance."""
    print("\nTesting global URLShortener instance...")

    from shared_url_shortener import url_shortener

    # Test URL to shorten
    original_url = "https://example.com/v1/click?cid=999&sub1=global_test"

    print("Global instance uses in-memory storage")

    # Shorten URL
    short_url, params = url_shortener.shorten_url(original_url)
    print(f"Short URL: {short_url}")
    print(f"Params: {params}")

    # Expand URL
    expanded_url, expanded_params = url_shortener.expand_url(short_url)
    print(f"Expanded URL: {expanded_url}")

    # Check if storage has data
    if url_shortener.storage:
        print(f"✅ Global storage has {len(url_shortener.storage)} entries")
        return True
    else:
        print("❌ Global storage is empty")
        return False

if __name__ == "__main__":
    success1 = test_url_shortener()
    success2 = test_global_instance()
    sys.exit(0 if (success1 and success2) else 1)
