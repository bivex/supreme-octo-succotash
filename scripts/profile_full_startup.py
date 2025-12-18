
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Profile full application startup including server initialization.
"""

import sys
import os
import cProfile
import pstats
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def profile_full_startup():
    """Profile the complete application startup."""
    print("🚀 Starting full application startup profiling...")

    # Import
    from src.main import create_app

    print("📊 Phase 1: Creating application...")
    start_time = time.time()
    app = create_app()
    create_time = time.time() - start_time
    print(f"Phase 1 completed in: {create_time:.2f}s")
    # Simulate server startup (without actually starting server)
    print("📊 Phase 2: Preparing server startup...")
    prep_time = time.time()

    # This would normally be where the server starts listening
    # We'll simulate by waiting a bit
    time.sleep(0.1)

    total_time = time.time() - start_time
    print(f"Total startup time: {total_time:.2f}s")
    return app

def analyze_blocking():
    """Analyze what might be blocking the main thread."""
    print("\n🔍 Analyzing potential blocking operations...")

    # Check if there are any long-running synchronous operations
    from src.container import container

    print("Checking upholder initialization...")
    upholder = container.get_postgres_upholder()

    print(f"Upholder running: {upholder.is_running}")

    # Check if baseline was established
    baseline = upholder.performance_baseline
    if baseline:
        established = baseline.get('established_at')
        if established:
            print(f"Baseline established at: {established}")
        else:
            print("Baseline not yet established (async)")
    else:
        print("Baseline not established")

    # Check monitoring threads
    print(f"Cache monitor active: {upholder.cache_monitor.monitoring_active}")
    print(f"Connection pool monitor active: {hasattr(upholder.connection_pool_monitor, 'is_monitoring') and upholder.connection_pool_monitor.is_monitoring}")

def main():
    """Main profiling function."""
    print("🔬 Profiling complete PostgreSQL Auto Upholder startup...")

    # Create profiler
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    try:
        # Run the function we want to profile
        app = profile_full_startup()

        # Analyze blocking
        analyze_blocking()

        # Stop profiling
        profiler.disable()

        # Create stats
        stats = pstats.Stats(profiler)

        # Sort by cumulative time
        stats.sort_stats('cumulative')

        print("\n📈 FUNCTIONS WITH HIGHEST CUMULATIVE TIME (>0.1s):")
        print("=" * 60)
        # Filter to show only functions that took more than 0.1 seconds cumulatively
        stats.print_stats(0.1)

        print("\n⏱️  FUNCTIONS WITH HIGHEST TOTAL TIME (>0.05s):")
        print("=" * 60)
        stats = pstats.Stats(profiler)
        stats.sort_stats('time')
        stats.print_stats(0.05)

        # Save profile data
        stats.dump_stats('full_startup_profile.prof')
        print("💾 Profile data saved to: full_startup_profile.prof")

    except Exception as e:
        print(f"❌ Profiling failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
