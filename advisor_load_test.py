# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:34
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Load test script for Intel Advisor threading analysis."""

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def make_request(endpoint: str, method: str = "GET", data: dict = None):
    """Make a single request to the application."""
    try:
        url = f"http://127.0.0.1:5000{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        return response.status_code
    except Exception as e:
        print(f"Request error: {e}")
        return None


def run_load_test(duration_seconds: int = 60, concurrent_users: int = 10):
    """Run load test to generate threading activity."""
    print(f"🔥 Starting load test: {concurrent_users} concurrent users for {duration_seconds}s")

    endpoints = [
        "/v1/health",
        "/v1/campaigns",
        "/v1/goals",
        "/v1/clicks",
        "/v1/journeys/funnel",
        "/v1/ltv/analysis",
    ]

    start_time = time.time()
    request_count = 0

    def user_session():
        nonlocal request_count
        session_start = time.time()

        while time.time() - session_start < duration_seconds:
            endpoint = random.choice(endpoints)
            status = make_request(endpoint)
            if status:
                request_count += 1

            # Small delay between requests
            time.sleep(random.uniform(0.1, 0.5))

    # Run concurrent user sessions
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(user_session) for _ in range(concurrent_users)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"User session error: {e}")

    total_time = time.time() - start_time
    print(".2f"".2f")


if __name__ == "__main__":
    print("🎯 Advisor Load Test - Run this while Intel Advisor collects threading data")
    print("💡 This will exercise the application's threading components")

    # Run for 30 seconds with 5 concurrent users
    run_load_test(duration_seconds=30, concurrent_users=5)
