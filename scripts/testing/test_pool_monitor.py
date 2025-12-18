
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
Test database connection pool monitoring
"""

import time
from src.container import container


import pytest

@pytest.mark.asyncio
async def test_pool_stats():
    """Test database connection pool statistics."""
    print("=== Testing Database Connection Pool ===")
    await container.get_db_connection_pool()

    # Get initial pool stats
    initial_stats = container.get_pool_stats()
    print(f"Initial pool stats: {initial_stats}")

    # Get a connection
    conn1 = container.get_db_connection()
    print("Got connection 1")

    stats_after_conn1 = container.get_pool_stats()
    print(f"Stats after getting connection 1: {stats_after_conn1}")

    # Get another connection
    conn2 = container.get_db_connection()
    print("Got connection 2")

    stats_after_conn2 = container.get_pool_stats()
    print(f"Stats after getting connection 2: {stats_after_conn2}")

    # Release first connection
    container.release_db_connection(conn1)
    print("Released connection 1")

    stats_after_release1 = container.get_pool_stats()
    print(f"Stats after releasing connection 1: {stats_after_release1}")

    # Release second connection
    container.release_db_connection(conn2)
    print("Released connection 2")

    final_stats = container.get_pool_stats()
    print(f"Final pool stats: {final_stats}")

    # Check for leaks
    if initial_stats.get('available', 0) != final_stats.get('available', 0):
        print("[WARN]  WARNING: Possible connection leak detected!")
        print(f"   Initial available: {initial_stats.get('available', 'unknown')}")
        print(f"   Final available: {final_stats.get('available', 'unknown')}")
    else:
        print("[OK] No connection leaks detected")

    # Test pool limits
    connections = []
    try:
        print("\nTesting pool limits...")
        for i in range(25):  # Try to get more than maxconn (20)
            try:
                conn = container.get_db_connection()
                connections.append(conn)
                print(f"Got connection {i+1}")
            except Exception as e:
                print(f"Failed to get connection {i+1}: {e}")
                break

        print(f"Successfully got {len(connections)} connections")

    finally:
        # Clean up
        for conn in connections:
            try:
                container.release_db_connection(conn)
            except Exception as e:
                print(f"Error releasing connection: {e}")

    final_cleanup_stats = container.get_pool_stats()
    print(f"Stats after cleanup: {final_cleanup_stats}")

    print("\n=== Pool Test Complete ===")


if __name__ == "__main__":
    test_pool_stats()
