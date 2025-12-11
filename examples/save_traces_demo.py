#!/usr/bin/env python3
"""
Demo of saving async traces to files for later analysis.
Shows how to use the new file saving functionality.
"""

import asyncio
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def demo_save_traces():
    """Demonstrate saving traces to different formats."""
    print("💾 Async-Trace File Saving Demo")
    print("=" * 50)

    from utils.async_debug import (
        debug_async_trace,
        save_trace_to_file,
        log_trace_to_continuous_file,
        save_debug_snapshot
    )

    async def nested_operation(depth: int):
        """Nested async operation to create interesting traces."""
        debug_async_trace(f"Nested operation at depth {depth}")

        if depth > 0:
            # Create a sub-task
            sub_task = asyncio.create_task(nested_operation(depth - 1))
            await sub_task

        await asyncio.sleep(0.1)
        debug_async_trace(f"Completing operation at depth {depth}")

    async def complex_workflow():
        """Complex workflow with multiple tasks."""
        debug_async_trace("Starting complex workflow")

        # Start multiple concurrent tasks
        tasks = []
        for i in range(3):
            task = asyncio.create_task(nested_operation(2))
            tasks.append(task)

        # Wait for all tasks
        await asyncio.gather(*tasks)
        debug_async_trace("Complex workflow completed")

    print("\n🔄 Running complex workflow...")
    await complex_workflow()

    print("\n💾 Saving traces to files...")

    # Save as JSON
    json_file = save_trace_to_file(format="json")
    print(f"📄 JSON trace saved: {json_file}")

    # Save as HTML
    html_file = save_trace_to_file(format="html")
    print(f"🌐 HTML trace saved: {html_file}")

    # Create debug snapshot
    snapshot_file = save_debug_snapshot("demo_workflow")
    print(f"📸 Debug snapshot saved: {snapshot_file}")

    # Log to continuous file (multiple entries)
    print("\n📝 Logging multiple traces to continuous file...")
    for i in range(3):
        debug_async_trace(f"Log entry {i+1}")
        log_file = log_trace_to_continuous_file()
        print(f"📋 Entry {i+1} logged to: {log_file}")
        await asyncio.sleep(0.1)

    print("\n✅ All traces saved!")
    print("\n📂 Check the 'traces/' directory for saved files:")
    print("   • JSON files for programmatic analysis")
    print("   • HTML files for visual inspection")
    print("   • JSONL files for continuous logging")

    # Show file listing
    try:
        traces_dir = os.path.join(os.getcwd(), "traces")
        if os.path.exists(traces_dir):
            print(f"\n📁 Files in traces directory:")
            for file in os.listdir(traces_dir)[:10]:  # Show first 10 files
                print(f"   • {file}")
            if len(os.listdir(traces_dir)) > 10:
                print(f"   ... and {len(os.listdir(traces_dir)) - 10} more files")
        else:
            print("\n⚠️  Traces directory not found")
    except Exception as e:
        print(f"\n⚠️  Error listing traces directory: {e}")

async def demo_error_tracing():
    """Demonstrate tracing errors and exceptions."""
    print("\n🚨 Error Tracing Demo")
    print("=" * 30)

    from utils.async_debug import save_debug_snapshot

    async def failing_operation():
        """Operation that will fail."""
        debug_async_trace("About to fail...")
        await asyncio.sleep(0.05)
        raise ValueError("Simulated error for tracing demo")

    async def error_handler():
        """Handle the error and save trace."""
        try:
            await failing_operation()
        except ValueError as e:
            print(f"❌ Caught error: {e}")
            # Save debug snapshot when error occurs
            snapshot = save_debug_snapshot("error_occurred")
            print(f"📸 Error snapshot saved: {snapshot}")
            return snapshot

    error_snapshot = await error_handler()

    if error_snapshot:
        print(f"\n🔍 Open {error_snapshot} in browser to see the call stack at error time")

async def main():
    """Main demo function."""
    await demo_save_traces()
    await demo_error_tracing()

    print("\n🎉 Demo completed!")
    print("\n💡 Usage patterns:")
    print("   • save_trace_to_file() - Save single trace snapshot")
    print("   • log_trace_to_continuous_file() - Append to log for monitoring")
    print("   • save_debug_snapshot('reason') - Quick debug snapshots")
    print("   • Use in exception handlers to capture error contexts")

if __name__ == "__main__":
    asyncio.run(main())
