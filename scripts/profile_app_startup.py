#!/usr/bin/env python3
"""
Profile application startup to identify blocking operations.
"""

import sys
import os
import cProfile
import pstats
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def profile_app_creation():
    """Profile the application creation process."""
    print("🚀 Starting application creation profiling...")

    # Import and create app
    from src.main import create_app

    print("📊 Creating application...")
    app = create_app()

    print("✅ Application created successfully")
    return app

def main():
    """Main profiling function."""
    print("🔬 Profiling PostgreSQL Auto Upholder startup...")

    # Create profiler
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    try:
        # Run the function we want to profile
        app = profile_app_creation()

        # Stop profiling
        profiler.disable()

        # Create stats
        stats = pstats.Stats(profiler)

        # Sort by cumulative time (total time spent in function and callees)
        stats.sort_stats('cumulative')

        print("\n📈 TOP 20 FUNCTIONS BY CUMULATIVE TIME:")
        print("=" * 60)
        stats.print_stats(20)

        print("\n⏱️  TOP 20 FUNCTIONS BY TOTAL TIME:")
        print("=" * 60)
        stats = pstats.Stats(profiler)
        stats.sort_stats('time')
        stats.print_stats(20)

        # Save profile data
        stats.dump_stats('app_startup_profile.prof')
        print("💾 Profile data saved to: app_startup_profile.prof")

    except Exception as e:
        print(f"❌ Profiling failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
