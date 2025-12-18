#!/usr/bin/env python3
"""
Test script to verify that async traces are automatically saved during server lifecycle.
"""

import asyncio
import signal
import sys
import os
import time
import subprocess

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_server_traces():
    """Test that server automatically saves traces during startup and shutdown."""
    print("🧪 Testing automatic async-trace saving during server lifecycle")
    print("=" * 70)

    # Check if traces directory exists
    traces_dir = "traces"
    if not os.path.exists(traces_dir):
        os.makedirs(traces_dir)
        print(f"📁 Created traces directory: {traces_dir}")

    # Check existing trace files before test
    existing_files = []
    if os.path.exists(traces_dir):
        existing_files = os.listdir(traces_dir)
        print(f"📄 Existing trace files: {len(existing_files)}")
        for f in existing_files[:5]:  # Show first 5
            print(f"   • {f}")
        if len(existing_files) > 5:
            print(f"   ... and {len(existing_files) - 5} more")

    print("\n🚀 Starting server with --async-trace for 10 seconds...")

    try:
        # Start server process
        cmd = [sys.executable, "main_clean.py", "--async-trace"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )

        # Let server start up
        time.sleep(3)

        # Send SIGINT to gracefully shutdown
        print("🛑 Sending SIGINT to server for graceful shutdown...")
        process.send_signal(signal.SIGINT)

        # Wait for process to finish
        stdout, stderr = process.communicate(timeout=10)

        print("📋 Server output:")
        print("-" * 40)
        # Show last 20 lines of output
        lines = stdout.split('\n')[-20:]
        for line in lines:
            if line.strip():
                print(f"   {line}")

        if stderr:
            print("⚠️  Server stderr:")
            print(stderr)

        print("-" * 40)

    except subprocess.TimeoutExpired:
        print("⏰ Server didn't shutdown gracefully, terminating...")
        process.kill()
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        if 'process' in locals():
            process.kill()
        return False

    # Check for new trace files
    time.sleep(1)  # Give filesystem time to sync
    new_files = []
    if os.path.exists(traces_dir):
        new_files = os.listdir(traces_dir)

    added_files = set(new_files) - set(existing_files)
    print(f"\n📊 Trace files added during server run: {len(added_files)}")

    if added_files:
        print("📄 New trace files:")
        for f in sorted(added_files):
            file_path = os.path.join(traces_dir, f)
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {f} ({file_size} bytes)")

            # Show file type
            if f.endswith('.json'):
                print("      └─ JSON format (for analysis)")
            elif f.endswith('.html'):
                print("      └─ HTML format (for viewing)")
            elif f.endswith('.jsonl'):
                print("      └─ JSONL format (continuous log)")

    else:
        print("⚠️  No new trace files were created")
        return False

    # Check for expected trace types
    expected_patterns = ['server_startup', 'signal_shutdown', 'server_shutdown']
    found_patterns = []

    for pattern in expected_patterns:
        if any(pattern in f for f in added_files):
            found_patterns.append(pattern)

    print("\n🎯 Expected trace patterns found:")
    for pattern in expected_patterns:
        status = "✅" if pattern in found_patterns else "❌"
        print(f"   {status} {pattern}")

    if len(found_patterns) == len(expected_patterns):
        print("\n🎉 SUCCESS: All expected traces were automatically saved!")
        print("🔍 Server now automatically saves traces at:")
        print("   • Startup (server_startup)")
        print("   • Signal interruption (signal_shutdown_*)")
        print("   • Graceful shutdown (server_shutdown)")
        print("   • Unhandled exceptions (unhandled_exception)")
        print("   • Route handler errors (create_offer_error, etc.)")
        return True
    else:
        print(f"\n⚠️  Only {len(found_patterns)}/{len(expected_patterns)} expected trace patterns found")
        return False

if __name__ == "__main__":
    success = test_server_traces()
    sys.exit(0 if success else 1)
