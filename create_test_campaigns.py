#!/usr/bin/env python3
"""
Script to create test campaigns with landing pages and offers.
"""

import psycopg2
from datetime import datetime, timedelta
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'supreme_octosuccotash_db',
    'user': 'app_user',
    'password': 'app_password'
}

def create_test_campaigns(count=10):
    """Create test campaigns with landing pages and offers."""

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("=" * 80)
        print(f"Creating {count} test campaigns...")
        print("=" * 80)
        print()

        created_campaigns = 0
        created_landings = 0
        created_offers = 0

        for i in range(1, count + 1):
            campaign_id = f"camp_{9000 + i}"

            # Create campaign
            try:
                cursor.execute("""
                    INSERT INTO campaigns (
                        id, name, description, status, cost_model,
                        payout_amount, payout_currency,
                        safe_page_url, offer_page_url,
                        daily_budget_amount, daily_budget_currency,
                        total_budget_amount, total_budget_currency,
                        start_date, end_date,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        updated_at = EXCLUDED.updated_at
                """, (
                    campaign_id,
                    f"Test Campaign {9000 + i}",
                    f"Auto-generated test campaign #{i}",
                    "active",
                    "cpa",
                    10.00 + i,  # Incremental payout
                    "USD",
                    f"https://example.com/safe/{campaign_id}",
                    f"https://example.com/offer/{campaign_id}",
                    100.00,
                    "USD",
                    1000.00,
                    "USD",
                    datetime.now(),
                    datetime.now() + timedelta(days=30),
                    datetime.now(),
                    datetime.now()
                ))
                created_campaigns += 1
                print(f"✓ Campaign {campaign_id} created")
            except Exception as e:
                print(f"✗ Campaign {campaign_id} error: {e}")

            # Create 2-3 landing pages per campaign
            num_landings = 2 if i % 2 == 0 else 3
            for j in range(1, num_landings + 1):
                landing_id = f"{40 + (i-1)*3 + j}"
                try:
                    cursor.execute("""
                        INSERT INTO landing_pages (
                            id, campaign_id, name, url, page_type,
                            weight, is_active, is_control,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        landing_id,
                        campaign_id,
                        f"Landing Page {j} for {campaign_id}",
                        f"https://example.com/lp/{campaign_id}/{j}",
                        "direct" if j == 1 else "presell",
                        100 if j == 1 else 50,  # First landing has higher weight
                        True,
                        j == 1,  # First landing is control
                        datetime.now(),
                        datetime.now()
                    ))
                    created_landings += 1
                except Exception as e:
                    print(f"  ✗ Landing {landing_id} error: {e}")

            # Create 1-2 offers per campaign
            num_offers = 1 if i % 3 == 0 else 2
            for k in range(1, num_offers + 1):
                offer_id = f"{20 + (i-1)*2 + k}"
                try:
                    cursor.execute("""
                        INSERT INTO offers (
                            id, campaign_id, name, url, offer_type,
                            payout_amount, payout_currency,
                            is_active, weight,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        offer_id,
                        campaign_id,
                        f"Offer {k} for {campaign_id}",
                        f"https://example.com/offers/{campaign_id}/{k}",
                        "cpa",
                        10.00 + i + k,
                        "USD",
                        True,
                        100 if k == 1 else 80,
                        datetime.now(),
                        datetime.now()
                    ))
                    created_offers += 1
                except Exception as e:
                    print(f"  ✗ Offer {offer_id} error: {e}")

        # Commit all changes
        conn.commit()

        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✓ Campaigns created: {created_campaigns}")
        print(f"✓ Landing pages created: {created_landings}")
        print(f"✓ Offers created: {created_offers}")
        print()

        # Show what was created
        cursor.execute("SELECT id, name, status FROM campaigns ORDER BY id")
        campaigns = cursor.fetchall()

        print(f"Total campaigns in database: {len(campaigns)}")
        print()
        print("Campaigns list:")
        for camp_id, camp_name, status in campaigns:
            print(f"  • {camp_id} - {camp_name} ({status})")

        cursor.close()
        conn.close()

        print()
        print("✅ Done!")

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def show_stats():
    """Show current database statistics."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print()
        print("=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)

        # Count campaigns
        cursor.execute("SELECT count(*) FROM campaigns")
        campaign_count = cursor.fetchone()[0]
        print(f"Campaigns: {campaign_count}")

        # Count landing pages
        cursor.execute("SELECT count(*) FROM landing_pages")
        landing_count = cursor.fetchone()[0]
        print(f"Landing pages: {landing_count}")

        # Count offers
        cursor.execute("SELECT count(*) FROM offers")
        offer_count = cursor.fetchone()[0]
        print(f"Offers: {offer_count}")

        # Count clicks
        cursor.execute("SELECT count(*) FROM clicks")
        click_count = cursor.fetchone()[0]
        print(f"Clicks: {click_count}")

        # Count conversions
        cursor.execute("SELECT count(*) FROM conversions")
        conversion_count = cursor.fetchone()[0]
        print(f"Conversions: {conversion_count}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error getting stats: {e}")

def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Create test campaigns')
    parser.add_argument('-c', '--count', type=int, default=10,
                       help='Number of campaigns to create (default: 10)')
    parser.add_argument('-s', '--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--clean', action='store_true',
                       help='Clean all test campaigns (camp_9*)')

    args = parser.parse_args()

    if args.clean:
        print("Cleaning test campaigns...")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Delete test data
            cursor.execute("DELETE FROM landing_pages WHERE campaign_id LIKE 'camp_9%'")
            deleted_landings = cursor.rowcount

            cursor.execute("DELETE FROM offers WHERE campaign_id LIKE 'camp_9%'")
            deleted_offers = cursor.rowcount

            cursor.execute("DELETE FROM clicks WHERE campaign_id LIKE 'camp_9%'")
            deleted_clicks = cursor.rowcount

            cursor.execute("DELETE FROM campaigns WHERE id LIKE 'camp_9%'")
            deleted_campaigns = cursor.rowcount

            conn.commit()

            print(f"✓ Deleted {deleted_campaigns} campaigns")
            print(f"✓ Deleted {deleted_landings} landing pages")
            print(f"✓ Deleted {deleted_offers} offers")
            print(f"✓ Deleted {deleted_clicks} clicks")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error cleaning: {e}")
            sys.exit(1)

    elif args.stats:
        show_stats()

    else:
        create_test_campaigns(args.count)
        show_stats()

if __name__ == '__main__':
    main()
