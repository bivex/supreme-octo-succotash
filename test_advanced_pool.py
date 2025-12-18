
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:51
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test script for Advanced Connection Pool
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.database.advanced_connection_pool import AdvancedConnectionPool
import time

def test_advanced_pool():
    """Test advanced connection pool functionality."""
    print("🧪 Testing Advanced Connection Pool")
    print("=" * 50)

    # Create pool
    pool = AdvancedConnectionPool(
        minconn=2,
        maxconn=10,
        host="localhost",
        port=5432,
        database="supreme_octosuccotash_db",
        user="app_user",
        password="app_password"
    )

    try:
        # Test basic connection
        print("Testing basic connection...")
        conn = pool.getconn()
        print("✅ Connection obtained")

        # Test query execution with monitoring
        result = pool.execute_with_monitoring(conn, "SELECT COUNT(*) FROM campaigns")
        print(f"✅ Query executed, result: {result}")

        pool.putconn(conn)
        print("✅ Connection returned")

        # Test multiple connections
        print("\nTesting multiple connections...")
        connections = []
        for i in range(5):
            conn = pool.getconn()
            connections.append(conn)
            print(f"✅ Connection {i+1} obtained")

        # Execute queries on each connection
        for i, conn in enumerate(connections):
            result = pool.execute_with_monitoring(conn, "SELECT 1")
            print(f"✅ Query on connection {i+1} executed")

        # Return all connections
        for conn in connections:
            pool.putconn(conn)
        print("✅ All connections returned")

        # Test statistics
        print("\n📊 Pool Statistics:")
        stats = pool.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n✅ Advanced Connection Pool test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        pool.closeall()

if __name__ == "__main__":
    test_advanced_pool()
