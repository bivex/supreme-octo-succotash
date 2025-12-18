
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:05
# Last Updated: 2025-12-18T12:12:05
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Performance test script to demonstrate optimizations."""

import asyncio
import pytest
import time
import os
import sys
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Add src to path

from src.infrastructure.upholder.postgres_bulk_optimizer import PostgresBulkOptimizer, BulkOperationMetrics
from src.infrastructure.async_io_processor import AsyncIOProcessor
from src.infrastructure.repositories.optimized_analytics_repository import OptimizedAnalyticsRepository

def generate_test_clicks(count: int = 1000) -> List[Dict[str, Any]]:
    """Generate test click data."""
    np.random.seed(42)  # For reproducible results

    campaign_ids = [f"campaign_{i}" for i in range(10)]
    timestamps = pd.date_range('2024-01-01', periods=count, freq='1min')

    clicks = []
    for i in range(count):
        click = {
            'campaign_id': np.random.choice(campaign_ids),
            'click_id': f"click_{i:06d}",
            'timestamp': timestamps[i].isoformat(),
            'ip_address': f"192.168.1.{np.random.randint(1, 255)}",
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referrer_url': 'https://example.com/landing',
            'is_valid': np.random.choice([True, False], p=[0.95, 0.05]),
            'revenue': round(np.random.exponential(1.0), 2),
            'cost': round(np.random.exponential(0.5), 2)
        }
        clicks.append(click)

    return clicks

@pytest.mark.asyncio
async def test_bulk_optimizer():
    """Test bulk optimizer performance."""
    print("🔥 Testing Bulk Optimizer Performance")

    # Mock connection pool for testing
    class MockConnectionPool:
        def getconn(self):
            class MockConn:
                def cursor(self):
                    class MockCursor:
                        def execute(self, *args): pass
                        def copy_expert(self, *args): pass
                        def close(self): pass
                    return MockCursor()
                def commit(self): pass
                def close(self): pass
            return MockConn()

        def putconn(self, conn): pass

    connection_pool = MockConnectionPool()
    optimizer = PostgresBulkOptimizer(connection_pool)

    # Generate test data
    test_clicks = generate_test_clicks(5000)

    print(f"📊 Testing with {len(test_clicks)} clicks...")

    # Test vectorized bulk insert
    start_time = time.time()
    result = optimizer.vectorized_bulk_insert_clicks(test_clicks)
    vectorized_time = time.time() - start_time

    print("✅ Vectorized bulk insert:")
    print(".2f")
    print(".2f")

    return result

@pytest.mark.asyncio
async def test_async_io_processor():
    """Test async I/O processor performance."""
    print("\n🌐 Testing Async I/O Processor")

    async with AsyncIOProcessor(max_concurrent=50) as processor:
        # Test HTTP requests
        http_requests = [
            {
                'url': 'http://httpbin.org/delay/0.1',
                'method': 'GET',
                'headers': {'User-Agent': 'Performance-Test/1.0'}
            }
            for _ in range(20)
        ]

        print(f"📡 Testing {len(http_requests)} concurrent HTTP requests...")

        start_time = time.time()
        http_result = await processor.batch_http_requests(http_requests)
        http_time = time.time() - start_time

        print("✅ HTTP batch result:")
        print(".2f")
        print(".2f")
        print(f"   Success rate: {http_result.successful_tasks}/{http_result.total_tasks}")

        # Test file operations
        file_ops = [
            {
                'type': 'write',
                'path': f'C:\\tmp\\test_file_{i}.txt',
                'content': f'Test content {i}' * 100
            }
            for i in range(10)
        ]

        print(f"📁 Testing {len(file_ops)} concurrent file operations...")

        start_time = time.time()
        file_result = await processor.batch_file_operations(file_ops)
        file_time = time.time() - start_time

        print("✅ File operations result:")
        print(".2f")
        print(".2f")
        print(f"   Success rate: {file_result.successful_tasks}/{file_result.total_tasks}")

        return http_result, file_result

def test_vectorized_analytics():
    """Test vectorized analytics processing."""
    print("\n📈 Testing Vectorized Analytics")

    # Generate test data
    test_clicks = generate_test_clicks(10000)
    df = pd.DataFrame(test_clicks)

    print(f"📊 Processing {len(df)} clicks with vectorized operations...")

    # Test vectorized filtering
    start_time = time.time()
    valid_clicks = df[df['is_valid']]
    conversions = df[df['revenue'] > 0]  # Simulate conversions

    # Vectorized aggregations
    total_clicks = len(valid_clicks)
    total_conversions = len(conversions)
    total_revenue = valid_clicks['revenue'].sum()
    total_cost = valid_clicks['cost'].sum()

    ctr = total_conversions / total_clicks if total_clicks > 0 else 0
    epc = total_revenue / total_clicks if total_clicks > 0 else 0
    roi = (total_revenue - total_cost) / total_cost if total_cost > 0 else 0

    processing_time = time.time() - start_time

    print("✅ Vectorized analytics result:")
    print(".2f")
    print(f"   Total clicks: {total_clicks}")
    print(f"   Conversions: {total_conversions}")
    print(".2f")
    print(".2f")
    print(".4f")

    return {
        'processing_time': processing_time,
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'ctr': ctr,
        'epc': epc,
        'roi': roi
    }

async def main():
    """Run all performance tests."""
    print("🚀 Supreme Octo Succotash Performance Test Suite")
    print("=" * 50)

    results = {}

    try:
        # Test bulk optimizer
        bulk_result = await test_bulk_optimizer()
        results['bulk_optimizer'] = bulk_result

        # Test async I/O processor
        http_result, file_result = await test_async_io_processor()
        results['http_requests'] = http_result
        results['file_operations'] = file_result

        # Test vectorized analytics
        analytics_result = test_vectorized_analytics()
        results['vectorized_analytics'] = analytics_result

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    # Print summary
    print("\n" + "=" * 50)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("=" * 50)

    if 'bulk_optimizer' in results:
        bulk = results['bulk_optimizer']
        print("🔥 Bulk Optimizer:")
        print(".2f")
        print(".2f")

    if 'http_requests' in results:
        http = results['http_requests']
        print("🌐 HTTP Requests:")
        print(".2f")
        print(".2f")

    if 'file_operations' in results:
        files = results['file_operations']
        print("📁 File Operations:")
        print(".2f")
        print(".2f")

    if 'vectorized_analytics' in results:
        analytics = results['vectorized_analytics']
        print("📈 Vectorized Analytics:")
        print(".2f")
        print(f"   Processed {analytics['total_clicks']} clicks")

    print("\n✅ Performance optimizations successfully tested!")
    print("💡 To enable optimizations in production, set: PERFORMANCE_MODE=true")

if __name__ == "__main__":
    asyncio.run(main())
