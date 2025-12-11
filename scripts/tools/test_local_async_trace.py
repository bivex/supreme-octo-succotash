#!/usr/bin/env python3
"""
Test script for the local async-trace installation.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_import():
    """Test that async_trace can be imported."""
    try:
        import async_trace
        print("✅ async_trace imported successfully")
        print(f"   Version: {async_trace.__version__}")
        print(f"   Path: {async_trace.__file__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import async_trace: {e}")
        return False

async def test_basic_functionality():
    """Test basic async-trace functionality."""
    try:
        from async_trace import print_trace, collect_async_trace

        print("\n🔍 Testing basic functionality...")

        async def nested_function():
            print_trace()
            await asyncio.sleep(0.01)
            return "nested_result"

        async def main_test():
            print("Starting main test...")
            result = await nested_function()
            print(f"Result: {result}")

            # Test structured data
            trace_data = collect_async_trace()
            print(f"Frames in trace: {len(trace_data['frames'])}")
            print(f"Current task: {trace_data['current_task'].get_name()}")

        await main_test()
        print("✅ Basic functionality test passed")
        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🎭 Testing Local Async-Trace Installation")
    print("=" * 50)

    # Test import
    if not test_import():
        return

    # Test functionality
    if not await test_basic_functionality():
        return

    print("\n🎉 All tests passed! Local async-trace is working correctly.")
    print("\n📍 Local installation path: scripts/tools/async-trace/")
    print("🔧 You can now modify the library locally and test changes immediately!")

if __name__ == "__main__":
    asyncio.run(main())
