#!/usr/bin/env python3
"""Enable pg_stat_statements extension in PostgreSQL."""

import psycopg2


def enable_pg_stat_statements():
    """Enable pg_stat_statements extension."""

    try:
        # Connect as app_user first to check current state
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='supreme_octosuccotash_db',
            user='app_user',
            password='app_password'
        )
        cursor = conn.cursor()

        print("🔧 Enabling pg_stat_statements extension...")

        # Try to create the extension
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
            conn.commit()
            print("✅ pg_stat_statements extension created successfully!")

        except Exception as e:
            print(f"❌ Failed to create extension with app_user: {e}")
            print("💡 This requires superuser privileges. Please run in psql as postgres:")
            print("   psql -U postgres -d supreme_octosuccotash_db")
            print("   CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")

            # Try with postgres user if possible
            try:
                conn.close()
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='supreme_octosuccotash_db',
                    user='postgres',
                    password='postgres'  # Try default postgres password
                )
                cursor = conn.cursor()
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
                conn.commit()
                print("✅ pg_stat_statements extension created with postgres user!")

            except Exception as e2:
                print(f"❌ Also failed with postgres user: {e2}")
                print("💡 Alternative: Use pgAdmin to create the extension")
                print("   1. Open pgAdmin")
                print("   2. Connect to supreme_octosuccotash_db")
                print("   3. Right-click Extensions > Create > pg_stat_statements")

        # Verify the extension was created
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements';")
        if cursor.fetchone():
            print("✅ pg_stat_statements extension is now ENABLED!")

            # Test it works
            cursor.execute("""
                SELECT count(*) as total_tracked_queries
                FROM pg_stat_statements;
            """)

            result = cursor.fetchone()
            print(f"📊 Extension is working - tracking {result[0] if result else 0} queries")

        else:
            print("❌ pg_stat_statements extension is still not enabled")

        conn.close()

    except Exception as e:
        print(f"❌ Connection or setup failed: {e}")


if __name__ == "__main__":
    enable_pg_stat_statements()
