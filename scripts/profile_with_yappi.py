
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
Profile application with yappi to find blocking operations and GIL issues.
"""

import sys
import os
import yappi
import time
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def start_profiling():
    """Start yappi profiling."""
    print("🚀 Starting yappi profiling...")
    yappi.start()

def stop_and_report():
    """Stop profiling and generate reports."""
    print("🛑 Stopping yappi profiling...")
    yappi.stop()

    print("\n" + "="*80)
    print("📊 YAPPI FUNCTION STATS (by cumulative time)")
    print("="*80)
    yappi.get_func_stats().print_all()

    print("\n" + "="*80)
    print("🧵 YAPPI THREAD STATS")
    print("="*80)
    yappi.get_thread_stats().print_all()

    print("\n" + "="*80)
    print("💾 Saving profile data...")
    yappi.get_func_stats().save('yappi_func_stats.prof', type='callgrind')
    yappi.get_thread_stats().save('yappi_thread_stats.prof')

    print("✅ Profile data saved to yappi_*.prof files")

def profile_application():
    """Profile the application startup and runtime."""
    print("🔬 Starting application profiling with yappi...")

    # Start profiling
    start_profiling()

    try:
        # Import and create app
        print("📊 Creating application...")
        from src.main import create_app
        app = create_app()
        print("✅ Application created")

        # Let it run for a bit to collect data
        print("⏳ Running application for profiling (10 seconds)...")
        time.sleep(10)

        # Try to make a request to trigger the blocking code
        print("🌐 Making test request to trigger potential blocking...")
        try:
            import requests
            response = requests.get('http://localhost:5000/v1/system/upholder/status', timeout=2)
            print(f"Request completed: {response.status_code}")
        except Exception as e:
            print(f"Request failed (expected): {e}")

        # Wait a bit more
        time.sleep(5)

    finally:
        # Stop and report
        stop_and_report()

def profile_with_server():
    """Profile application while running the server."""
    print("🔬 Profiling application with running server...")

    # Start profiling
    start_profiling()

    # Start server in background
    def run_server():
        try:
            print("🚀 Starting server...")
            from src.main import create_app
            app = create_app()

            # Simulate server run (in real scenario, this would be app.run())
            print("📡 Server simulation running...")
            time.sleep(15)  # Simulate server runtime
            print("🛑 Server simulation ended")

        except Exception as e:
            print(f"Server error: {e}")

    # Start server thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    # Make some requests to trigger blocking
    print("🌐 Making test requests...")
    try:
        import requests

        # Test health endpoint
        response = requests.get('http://localhost:5000/health', timeout=1)
        print(f"Health: {response.status_code}")

        # Test the problematic endpoint
        try:
            response = requests.get('http://localhost:5000/v1/system/upholder/status', timeout=3)
            print(f"Upholder status: {response.status_code}")
        except requests.exceptions.Timeout:
            print("Upholder status: TIMEOUT (this is the blocking issue!)")

    except Exception as e:
        print(f"Request error: {e}")

    # Wait for server thread
    server_thread.join(timeout=5)

    # Stop and report
    stop_and_report()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Profile application with yappi')
    parser.add_argument('--with-server', action='store_true',
                       help='Profile while running server')

    args = parser.parse_args()

    if args.with_server:
        profile_with_server()
    else:
        profile_application()
