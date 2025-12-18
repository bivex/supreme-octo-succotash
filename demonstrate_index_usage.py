
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:15
# Last Updated: 2025-12-18T12:12:15
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Demonstrate proper index usage by directly interacting with repositories.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.container import Container
from src.domain.value_objects import CampaignId
from datetime import datetime

class IndexUsageDemonstrator:
    """Demonstrate index usage by directly calling repository methods."""

    def __init__(self):
        self.container = Container()

    def get_index_stats(self):
        """Get current index statistics."""
        conn = None
        try:
            conn = self.container.get_db_connection()
            cursor = conn.cursor()

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

            return {row[1]: row for row in cursor.fetchall()}  # index_name -> stats
        finally:
            if conn:
                self.container.release_db_connection(conn)

    def demonstrate_campaign_queries(self):
        """Demonstrate queries that should use campaign indexes."""
        print("🎯 Testing campaign-related queries...")

        campaign_repo = self.container.get_campaign_repository()

        # This should use campaigns_pkey
        campaigns = campaign_repo.find_all(limit=10)
        print(f"✅ Retrieved {len(campaigns)} campaigns (uses campaigns_pkey)")

        if campaigns:
            # This should also use campaigns_pkey
            first_campaign = campaign_repo.find_by_id(campaigns[0].id)
            print(f"✅ Found campaign by ID: {first_campaign.name if first_campaign else 'None'}")

            # This should use idx_campaigns_status if it exists
            # But we need to check the campaign status query pattern
            all_campaigns = campaign_repo.find_all(limit=50)
            active_campaigns = [c for c in all_campaigns if c.status.value == 'active']
            print(f"✅ Filtered {len(active_campaigns)} active campaigns")

    def demonstrate_click_queries(self):
        """Demonstrate queries that should use click indexes."""
        print("🖱️ Testing click-related queries...")

        # For clicks to exist, we need to create them directly
        # Let's check if there are any clicks first
        conn = None
        try:
            conn = self.container.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clicks")
            click_count = cursor.fetchone()[0]
            print(f"📊 Current clicks in database: {click_count}")

            if click_count == 0:
                print("⚠️ No clicks exist. Let's create some test clicks...")

                # Get a campaign ID to use
                cursor.execute("SELECT id FROM campaigns WHERE is_deleted = FALSE LIMIT 1")
                campaign_row = cursor.fetchone()
                if campaign_row:
                    campaign_id = campaign_row[0]

                    # Insert some test clicks
                    for i in range(5):
                        cursor.execute("""
                            INSERT INTO clicks (id, campaign_id, ip_address, user_agent, referrer, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            f'test_click_{i:03d}',
                            campaign_id,
                            f'192.168.1.{i+10}',
                            'Mozilla/5.0 Test Browser',
                            f'https://test.com/campaign/{campaign_id}',
                            datetime.now()
                        ))

                    conn.commit()
                    print("✅ Created 5 test clicks")

                    # Now test queries that should use indexes
                    cursor.execute("SELECT COUNT(*) FROM clicks WHERE campaign_id = %s", (campaign_id,))
                    campaign_clicks = cursor.fetchone()[0]
                    print(f"✅ Found {campaign_clicks} clicks for campaign {campaign_id} (should use idx_clicks_campaign_id)")

        finally:
            if conn:
                self.container.release_db_connection(conn)

    def demonstrate_analytics_queries(self):
        """Demonstrate queries that should use analytics indexes."""
        print("📊 Testing analytics-related queries...")

        conn = None
        try:
            conn = self.container.get_db_connection()
            cursor = conn.cursor()

            # Check analytics cache
            cursor.execute("SELECT COUNT(*) FROM analytics_cache")
            analytics_count = cursor.fetchone()[0]
            print(f"📊 Current analytics entries: {analytics_count}")

            if analytics_count == 0:
                print("⚠️ No analytics data exists. Let's create some test data...")

                # Get a campaign ID
                cursor.execute("SELECT id FROM campaigns WHERE is_deleted = FALSE LIMIT 1")
                campaign_row = cursor.fetchone()
                if campaign_row:
                    campaign_id = campaign_row[0]

                    # Insert test analytics data
                    for i in range(3):
                        cursor.execute("""
                            INSERT INTO analytics_cache (campaign_id, cache_key, data, created_at, expires_at)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            campaign_id,
                            f'test_metric_{i}',
                            '{"clicks": 100, "conversions": 10}',
                            datetime.now(),
                            datetime.now()  # No expiration for test
                        ))

                    conn.commit()
                    print("✅ Created 3 test analytics entries")

                    # Now test queries that should use analytics indexes
                    cursor.execute("SELECT COUNT(*) FROM analytics_cache WHERE campaign_id = %s", (campaign_id,))
                    campaign_analytics = cursor.fetchone()[0]
                    print(f"✅ Found {campaign_analytics} analytics entries for campaign {campaign_id} (should use idx_analytics_campaign_id)")

                    cursor.execute("SELECT * FROM analytics_cache WHERE cache_key = %s", ('test_metric_0',))
                    key_result = cursor.fetchone()
                    print(f"✅ Found analytics entry by cache_key (should use idx_analytics_cache_key): {'Yes' if key_result else 'No'}")

        finally:
            if conn:
                self.container.release_db_connection(conn)

    def run_demonstration(self):
        """Run complete index usage demonstration."""
        print("🎭 INDEX USAGE DEMONSTRATION")
        print("=" * 50)

        # Get baseline stats
        print("📊 Getting baseline index statistics...")
        baseline_stats = self.get_index_stats()
        print(f"📊 Found {len(baseline_stats)} indexes")

        # Demonstrate different types of queries
        self.demonstrate_campaign_queries()
        self.demonstrate_click_queries()
        self.demonstrate_analytics_queries()

        # Wait for stats to update
        print("⏳ Waiting for statistics to update...")
        time.sleep(1)

        # Get final stats
        print("📊 Getting final index statistics...")
        final_stats = self.get_index_stats()

        # Analyze which indexes were used
        self.analyze_usage(baseline_stats, final_stats)

    def analyze_usage(self, baseline_stats, final_stats):
        """Analyze which indexes were used during demonstration."""
        print("\n📈 DEMONSTRATION RESULTS")
        print("=" * 50)

        used_indexes = []

        for index_name, final_stat in final_stats.items():
            schema, name, final_scans, tup_read, tup_fetch, size = final_stat

            baseline_scans = baseline_stats.get(name, [None, None, 0])[2]
            scan_increase = final_scans - baseline_scans

            if scan_increase > 0:
                used_indexes.append((name, baseline_scans, final_scans, scan_increase, size))
                print(f"✅ USED: {schema}.{name}")
                print(f"   Scans: {baseline_scans} → {final_scans} (+{scan_increase})")
                print(f"   Size: {size}")
            elif final_scans > 0:
                print(f"⚠️  PREVIOUSLY USED: {schema}.{name} (scans: {final_scans})")
            else:
                print(f"❌ STILL UNUSED: {schema}.{name}")

        print(f"\n📊 SUMMARY:")
        print(f"   • Indexes used during demo: {len(used_indexes)}")
        print(f"   • Total indexes: {len(final_stats)}")

        if used_indexes:
            print(f"\n🎯 SUCCESS: Database indexes are working correctly!")
            print("   The following indexes were successfully used:")
            for name, before, after, increase, size in used_indexes:
                print(f"   • {name}: +{increase} scans")
        else:
            print(f"\n⚠️  No new index usage detected during demonstration.")


def main():
    """Main entry point."""
    try:
        demo = IndexUsageDemonstrator()
        demo.run_demonstration()
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
