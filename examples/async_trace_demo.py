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
Demo of async-trace integration with the server.

This example shows how to use async-trace to debug asyncio tasks
in the affiliate marketing API server.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.async_debug import (
    debug_async_trace,
    get_async_trace_data,
    log_task_info,
    debug_before_await,
    debug_after_await,
    debug_task_creation
)

async def simulate_nested_tasks():
    """Simulate nested async tasks to demonstrate tracing."""
    print("🚀 Starting nested task simulation...")

    async def level_3_task():
        """Deepest level task."""
        debug_async_trace("Level 3 - Deepest task")
        await asyncio.sleep(0.1)
        return "level_3_result"

    async def level_2_task():
        """Middle level task."""
        debug_async_trace("Level 2 - Creating level 3 task")

        # Create a task
        task = asyncio.create_task(level_3_task())
        debug_task_creation()

        result = await task
        debug_async_trace("Level 2 - After awaiting level 3")
        return f"level_2_processed_{result}"

    async def level_1_task():
        """Top level task."""
        debug_async_trace("Level 1 - Creating level 2 task")

        result = await level_2_task()
        debug_async_trace("Level 1 - After level 2 completed")
        return f"level_1_final_{result}"

    # Start the chain
    debug_async_trace("Main - Starting the task chain")
    final_result = await level_1_task()

    print(f"✅ Final result: {final_result}")

    # Show structured trace data
    print("\n📊 Structured trace analysis:")
    trace_data = get_async_trace_data()
    if trace_data:
        print(f"Current task: {trace_data['current_task'].get_name()}")
        print(f"Call stack depth: {len(trace_data['frames'])}")

        print("\nCall stack (innermost to outermost):")
        for i, frame in enumerate(trace_data['frames']):
            indent = "  " * frame['indent']
            task_info = f" → creates {frame['task'].get_name()}" if frame['task'] else ""
            print(f"{indent}{i+1}. {frame['name']}(){task_info}")

    print("\n📋 Task summary:")
    log_task_info()

async def simulate_server_request():
    """Simulate a server request with database call."""
    print("\n🌐 Simulating server request...")

    async def mock_http_handler():
        """Mock HTTP request handler."""
        debug_async_trace("HTTP Request Handler - Start")

        # Simulate request processing
        await asyncio.sleep(0.05)

        # Simulate database call
        debug_before_await("database query")
        result = await mock_database_call()
        debug_after_await("database query")

        debug_async_trace("HTTP Request Handler - End")
        return f"response_with_{result}"

    async def mock_database_call():
        """Mock database operation."""
        debug_async_trace("Database Call - Inside DB operation")
        await asyncio.sleep(0.1)  # Simulate DB latency
        return "db_result"

    # Simulate concurrent requests
    tasks = []
    for i in range(3):
        task = asyncio.create_task(mock_http_handler())
        debug_task_creation()
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    print(f"✅ All requests completed: {results}")

async def demonstrate_timeout_scenario():
    """Demonstrate how async-trace helps with timeout debugging."""
    print("\n⏰ Demonstrating timeout scenario...")

    async def slow_operation():
        """An operation that might hang."""
        debug_async_trace("Slow operation - Starting")
        await asyncio.sleep(2)  # Intentionally slow
        debug_async_trace("Slow operation - Completed")
        return "slow_result"

    async def handler_with_timeout():
        """Handler that uses timeout."""
        debug_async_trace("Handler with timeout - Starting")

        try:
            async with asyncio.timeout(1):  # 1 second timeout
                result = await slow_operation()
            return result
        except asyncio.TimeoutError:
            debug_async_trace("Handler with timeout - TIMEOUT OCCURRED!")
            print("⚠️  Timeout detected! Here's where it happened:")
            return "timeout"

    result = await handler_with_timeout()
    print(f"Result: {result}")

async def main():
    """Main demo function."""
    print("🎭 Async-Trace Integration Demo")
    print("=" * 50)

    print("\n🔧 Testing async-trace availability...")
    try:
        from async_trace import print_trace
        print("✅ async-trace is available and working!")
    except ImportError:
        print("❌ async-trace not available. Install with: pip install async-trace")
        return

    # Demo 1: Nested tasks
    await simulate_nested_tasks()

    # Demo 2: Server request simulation
    await simulate_server_request()

    # Demo 3: Timeout handling
    await demonstrate_timeout_scenario()

    print("\n🎉 Demo completed!")
    print("\n💡 Tips for using async-trace in your server:")
    print("   • Run with: python main_clean.py --async-trace")
    print("   • Add debug_async_trace() calls in suspicious places")
    print("   • Use debug_before_await() and debug_after_await() around async ops")
    print("   • Check call stack when server hangs")

if __name__ == "__main__":
    asyncio.run(main())
