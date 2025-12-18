
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:49
# Last Updated: 2025-12-18T12:11:49
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test script to verify index effectiveness by generating realistic application usage.
"""

import sys
import os
import time
import requests
import json
import threading
import subprocess
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.container import Container

class IndexEffectivenessTester:
    """Test index effectiveness by generating realistic application usage."""

    def __init__(self):
        self.container = Container()
        self.base_url = "http://localhost:5000"
        self.server_process = None

    def start_server(self):
        """Start the application server in background."""
        print("🚀 Starting application server...")
        self.server_process = subprocess.Popen(
            [sys.executable, "src/main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )

        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)

        # Test server health
        try:
            response = requests.get(f"{self.base_url}/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server started successfully")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            return False

    def stop_server(self):
        """Stop the application server."""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Server stopped")

    def get_campaign_ids(self):
        """Get existing campaign IDs from database."""
        conn = None
        try:
            conn = self.container.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM campaigns WHERE is_deleted = FALSE LIMIT 10")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            if conn:
                self.container.release_db_connection(conn)

    def generate_clicks(self, campaign_ids, num_clicks=50):
        """Generate clicks for campaigns."""
        print(f"🖱️ Generating {num_clicks} clicks...")

        for i in range(num_clicks):
            campaign_id = random.choice(campaign_ids)
            click_data = {
                "campaign_id": campaign_id,
                "ip_address": f"192.168.1.{random.randint(1, 255)}",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "referrer": f"https://example.com/campaign/{campaign_id}",
                "click_timestamp": datetime.now().isoformat()
            }

            try:
                response = requests.post(
                    f"{self.base_url}/clicks",
                    json=click_data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if response.status_code in [200, 201]:
                    print(f"✅ Click {i+1} created for campaign {campaign_id}")
                else:
                    print(f"❌ Click {i+1} failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Click {i+1} error: {e}")

            time.sleep(0.1)  # Small delay between requests

    def generate_events(self, campaign_ids, num_events=30):
        """Generate events for campaigns."""
        print(f"📊 Generating {num_events} events...")

        event_types = ["page_view", "button_click", "form_submit", "video_play", "scroll"]

        for i in range(num_events):
            campaign_id = random.choice(campaign_ids)

            # First create a click to get a click_id
            click_data = {
                "campaign_id": campaign_id,
                "ip_address": f"192.168.1.{random.randint(1, 255)}",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "referrer": f"https://example.com/campaign/{campaign_id}",
                "click_timestamp": datetime.now().isoformat()
            }

            try:
                click_response = requests.post(
                    f"{self.base_url}/clicks",
                    json=click_data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )

                if click_response.status_code in [200, 201]:
                    click_result = click_response.json()
                    click_id = click_result.get("click_id")

                    if click_id:
                        event_data = {
                            "click_id": click_id,
                            "event_type": random.choice(event_types),
                            "event_data": {"page": f"/campaign/{campaign_id}", "action": "click"},
                            "event_timestamp": datetime.now().isoformat()
                        }

                        event_response = requests.post(
                            f"{self.base_url}/v1/events",
                            json=event_data,
                            headers={"Content-Type": "application/json"},
                            timeout=5
                        )

                        if event_response.status_code in [200, 201]:
                            print(f"✅ Event {i+1} created for click {click_id}")
                        else:
                            print(f"❌ Event {i+1} failed: {event_response.status_code}")
            except Exception as e:
                print(f"❌ Event {i+1} error: {e}")

            time.sleep(0.1)

    def query_data(self, campaign_ids):
        """Query data in ways that should use indexes."""
        print("🔍 Querying data to trigger index usage...")

        # Query campaigns by status (should use idx_campaigns_status)
        try:
            response = requests.get(f"{self.base_url}/v1/campaigns?status=active")
            print(f"✅ Campaign status query: {response.status_code}")
        except Exception as e:
            print(f"❌ Campaign status query error: {e}")

        # Query clicks by campaign (should use idx_clicks_campaign_id)
        for campaign_id in campaign_ids[:3]:  # Test first 3 campaigns
            try:
                response = requests.get(f"{self.base_url}/v1/clicks?campaign_id={campaign_id}")
                print(f"✅ Clicks query for campaign {campaign_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Clicks query error for campaign {campaign_id}: {e}")

        # Query events by click_id (should use idx_events_click_id)
        try:
            response = requests.get(f"{self.base_url}/v1/events?click_id=test_click_001")
            print(f"✅ Events query: {response.status_code}")
        except Exception as e:
            print(f"❌ Events query error: {e}")

        # Query analytics (should use analytics indexes)
        for campaign_id in campaign_ids[:2]:
            try:
                response = requests.get(f"{self.base_url}/v1/campaigns/{campaign_id}/analytics")
                print(f"✅ Analytics query for campaign {campaign_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Analytics query error for campaign {campaign_id}: {e}")

    def get_index_stats_before_after(self):
        """Get index statistics before and after testing."""
        conn = None
        try:
            conn = self.container.get_db_connection()
            cursor = conn.cursor()

            # Get current index statistics
            cursor.execute('''
                SELECT
                    schemaname,
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY indexrelname
            ''')

            stats = cursor.fetchall()
            return stats
        finally:
            if conn:
                self.container.release_db_connection(conn)

    def run_comprehensive_test(self):
        """Run comprehensive index effectiveness test."""
        print("🧪 STARTING COMPREHENSIVE INDEX EFFECTIVENESS TEST")
        print("=" * 60)

        # Get baseline index stats
        print("📊 Getting baseline index statistics...")
        baseline_stats = self.get_index_stats_before_after()
        print(f"📊 Baseline: Found {len(baseline_stats)} indexes")

        # Start server
        if not self.start_server():
            print("❌ Failed to start server. Aborting test.")
            return

        try:
            # Get campaign IDs
            campaign_ids = self.get_campaign_ids()
            if not campaign_ids:
                print("❌ No campaigns found. Please run create_test_data.py first.")
                return

            print(f"📋 Found {len(campaign_ids)} campaigns for testing")

            # Generate test data
            self.generate_clicks(campaign_ids, num_clicks=20)
            self.generate_events(campaign_ids, num_events=15)

            # Query data to trigger index usage
            self.query_data(campaign_ids)

            # Wait a moment for statistics to update
            print("⏳ Waiting for index statistics to update...")
            time.sleep(2)

            # Get final index stats
            print("📊 Getting final index statistics...")
            final_stats = self.get_index_stats_before_after()

            # Analyze results
            self.analyze_index_usage(baseline_stats, final_stats)

        finally:
            self.stop_server()

    def analyze_index_usage(self, baseline_stats, final_stats):
        """Analyze index usage changes."""
        print("\n📈 INDEX USAGE ANALYSIS")
        print("=" * 60)

        # Create lookup dictionaries
        baseline_dict = {stat[1]: stat for stat in baseline_stats}  # index name -> stats
        final_dict = {stat[1]: stat for stat in final_stats}

        used_indexes = []
        still_unused = []

        for index_name, final_stat in final_dict.items():
            schema, name, final_scans, tup_read, tup_fetch, size = final_stat

            baseline_scans = 0
            if name in baseline_dict:
                baseline_scans = baseline_dict[name][2]

            scan_increase = final_scans - baseline_scans

            if scan_increase > 0:
                used_indexes.append((name, baseline_scans, final_scans, scan_increase, size))
                print(f"✅ USED: {schema}.{name}")
                print(f"   Scans: {baseline_scans} → {final_scans} (+{scan_increase})")
                print(f"   Size: {size}")
            elif final_scans == 0:
                still_unused.append((name, final_scans, size))
                print(f"❌ UNUSED: {schema}.{name}")
                print(f"   Scans: {final_scans}, Size: {size}")
            else:
                print(f"⚠️  MINIMAL: {schema}.{name}")
                print(f"   Scans: {final_scans}, Size: {size}")

        print(f"\n📊 SUMMARY:")
        print(f"   • Indexes that became used: {len(used_indexes)}")
        print(f"   • Indexes still unused: {len(still_unused)}")
        print(f"   • Total indexes analyzed: {len(final_dict)}")

        if used_indexes:
            print(f"\n🎯 SUCCESS: {len(used_indexes)} indexes are now being used!")
            print("   The database indexes are working correctly.")
        else:
            print(f"\n⚠️  WARNING: No indexes were used during testing.")
            print("   This may indicate application code is not using expected query patterns.")

        if still_unused:
            print(f"\n🧹 UNUSED INDEXES REMAINING: {len(still_unused)}")
            print("   Consider removing these indexes to save space:")
            for name, scans, size in still_unused:
                print(f"   - {name} ({size})")


def main():
    """Main entry point."""
    try:
        tester = IndexEffectivenessTester()
        tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
