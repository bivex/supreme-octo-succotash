#!/usr/bin/env python3
"""Create performance indexes with fresh connection."""

import psycopg2


def create_indexes():
    """Create performance indexes."""
    try:
        # Fresh connection
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='supreme_octosuccotash_db',
            user='app_user',
            password='app_password'
        )
        cursor = conn.cursor()

        print("🔧 Creating Performance Indexes")
        print("=" * 40)

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_clicks_campaign_created ON clicks (campaign_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_clicks_created_at ON clicks (created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_clicks_user_id ON clicks (user_id);",
            "CREATE INDEX IF NOT EXISTS idx_events_click_created ON events (click_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_events_created_at ON events (created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);",
            "CREATE INDEX IF NOT EXISTS idx_conversions_click ON conversions (click_id);",
            "CREATE INDEX IF NOT EXISTS idx_conversions_created ON conversions (created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_conversions_type ON conversions (conversion_type);",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns (status);",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_created ON campaigns (created_at DESC);",
        ]

        created = 0
        for sql in indexes:
            try:
                cursor.execute(sql)
                conn.commit()
                index_name = sql.split()[5]  # Extract index name
                print(f"✅ Created: {index_name}")
                created += 1
            except Exception as e:
                print(f"❌ Failed: {sql.split()[5]} - {e}")

        print(f"\n✅ Successfully created {created} indexes")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    create_indexes()
