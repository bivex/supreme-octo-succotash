
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
"""Test script for PostgreSQL Auto Upholder integration."""

import requests
import json
import time
import sys
from datetime import datetime

def test_upholder_endpoints(base_url: str = "http://localhost:5000"):
    """Test PostgreSQL upholder endpoints."""

    print("🧪 Testing PostgreSQL Auto Upholder Integration")
    print("=" * 50)

    # Test 1: Get upholder status
    print("\n1️⃣  Testing GET /v1/system/upholder/status")
    try:
        response = requests.get(f"{base_url}/v1/system/upholder/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint working")
            print(f"   - Upholder running: {data['upholder_status']['is_running']}")
            print(f"   - Reports count: {data['upholder_status']['reports_count']}")

            # Show cache metrics if available
            cache = data.get('performance_dashboard', {}).get('current_metrics', {}).get('cache', {})
            if cache.get('current_metrics'):
                metrics = cache['current_metrics']
                print(f"   - Heap hit ratio: {metrics.get('heap_hit_ratio', 'N/A')}%")
                print(f"   - Index hit ratio: {metrics.get('index_hit_ratio', 'N/A')}%")

            # Show connection pool metrics
            pool = data.get('performance_dashboard', {}).get('current_metrics', {}).get('connection_pool', {})
            if pool.get('pool_metrics'):
                pool_metrics = pool['pool_metrics']
                print(f"   - Pool utilization: {pool_metrics.get('utilization_rate', 'N/A')}%")
                print(f"   - Pool efficiency: {pool_metrics.get('efficiency_score', 'N/A')}%")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")

    # Test 2: Get connection pool status
    print("\n2️⃣  Testing GET /v1/system/upholder/connection-pool/status")
    try:
        response = requests.get(f"{base_url}/v1/system/upholder/connection-pool/status")
        if response.status_code == 200:
            pool_data = response.json()
            print("✅ Connection pool status endpoint working")
            metrics = pool_data.get('pool_metrics', {})
            print(f"   - Used connections: {metrics.get('used_connections', 'N/A')}")
            print(f"   - Total connections: {metrics.get('total_connections', 'N/A')}")
            print(f"   - Health status: {pool_data.get('health_status', 'N/A')}")
        else:
            print(f"❌ Connection pool status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection pool status endpoint error: {e}")

    # Test 3: Get connection pool suggestions
    print("\n3️⃣  Testing GET /v1/system/upholder/connection-pool/suggestions")
    try:
        response = requests.get(f"{base_url}/v1/system/upholder/connection-pool/suggestions")
        if response.status_code == 200:
            suggestions = response.json()
            print("✅ Connection pool suggestions endpoint working")
            print(f"   - Found {len(suggestions)} optimization suggestions")
            if suggestions:
                for i, sug in enumerate(suggestions[:2], 1):  # Show first 2
                    print(f"      {i}. {sug.get('action', 'N/A')} (confidence: {sug.get('confidence_score', 'N/A')}%)")
        else:
            print(f"❌ Connection pool suggestions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection pool suggestions endpoint error: {e}")

    # Test 4: Get upholder config
    print("\n4️⃣  Testing GET /v1/system/upholder/config")
    try:
        response = requests.get(f"{base_url}/v1/system/upholder/config")
        if response.status_code == 200:
            config = response.json()
            print("✅ Config endpoint working")
            print(f"   - Auto-apply: {config.get('auto_apply_optimizations', 'N/A')}")
            print(f"   - Dry-run: {config.get('dry_run_mode', 'N/A')}")
            print(f"   - Query analysis interval: {config.get('query_analysis_interval', 'N/A')} min")
        else:
            print(f"❌ Config endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Config endpoint error: {e}")

    # Test 5: Run manual audit
    print("\n5️⃣  Testing POST /v1/system/upholder/audit")
    try:
        print("   Running manual audit (this may take a few seconds)...")
        start_time = time.time()
        response = requests.post(f"{base_url}/v1/system/upholder/audit")
        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print("✅ Manual audit completed")
            print(f"   - Duration: {duration:.2f}s")
            print(f"   - Optimizations applied: {len(result.get('optimizations_applied', []))}")
            print(f"   - Alerts generated: {len(result.get('alerts_generated', []))}")
            print(f"   - Recommendations: {len(result.get('recommendations_pending', []))}")

            # Show some alerts if any
            alerts = result.get('alerts_generated', [])
            if alerts:
                print("   📢 Recent alerts:")
                for alert in alerts[:3]:  # Show first 3
                    print(f"      - {alert}")

        else:
            print(f"❌ Manual audit failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Manual audit error: {e}")

    # Test 6: Check health endpoint includes database status
    print("\n6️⃣  Testing GET /health (with DB status)")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print("✅ Health endpoint working")
            print(f"   - Status: {health.get('status', 'unknown')}")
            print(f"   - Database: {health.get('database', 'unknown')}")
            print(f"   - Service: {health.get('service', 'unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")

    print("\n" + "=" * 50)
    print("🎉 PostgreSQL Auto Upholder integration test completed!")
    print("\n📚 Useful commands:")
    print("   - View status: curl http://localhost:5000/v1/system/upholder/status")
    print("   - Connection pool status: curl http://localhost:5000/v1/system/upholder/connection-pool/status")
    print("   - Pool suggestions: curl http://localhost:5000/v1/system/upholder/connection-pool/suggestions")
    print("   - Run audit: curl -X POST http://localhost:5000/v1/system/upholder/audit")
    print("   - View config: curl http://localhost:5000/v1/system/upholder/config")
    print("   - Check health: curl http://localhost:5000/health")


def wait_for_server(url: str, timeout: int = 30):
    """Wait for server to be ready."""
    print(f"⏳ Waiting for server at {url}...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass

        time.sleep(2)
        print(".", end="", flush=True)

    print("\n❌ Server didn't start within timeout")
    return False


if __name__ == "__main__":
    base_url = "http://localhost:5000"

    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    # Wait for server to be ready
    if not wait_for_server(base_url):
        sys.exit(1)

    # Run tests
    test_upholder_endpoints(base_url)
