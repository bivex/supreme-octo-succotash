#!/usr/bin/env python3
"""
Clean all database tables by truncating them.
"""

import psycopg2

def clean_database():
    """Clean all tables in the database."""
    print("🧹 Cleaning database tables...")
    print("=" * 40)

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password"
        )
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        tables = cursor.fetchall()

        if not tables:
            print("❌ No tables found in database")
            return False

        print(f"Found {len(tables)} tables to clean:")

        # Truncate all tables
        truncated = 0
        for (table_name,) in tables:
            try:
                cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE')
                print(f"✅ Truncated: {table_name}")
                truncated += 1
            except Exception as e:
                print(f"❌ Failed to truncate {table_name}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n🎉 Successfully cleaned {truncated} tables!")
        return True

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = clean_database()
    if not success:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Check database connection parameters")
        print("3. Verify user permissions")
        exit(1)
