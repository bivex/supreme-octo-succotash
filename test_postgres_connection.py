#!/usr/bin/env python3
"""
Test basic PostgreSQL connection.
"""

import psycopg2

def test_connection():
    """Test basic PostgreSQL connection."""
    print("🧪 Testing PostgreSQL connection...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password",
            client_encoding='utf8'
        )

        # Create cursor
        cur = conn.cursor()

        # Test query
        cur.execute("SELECT version();")
        result = cur.fetchone()
        print("✅ PostgreSQL connected successfully!")
        print(f"Version: {result[0][:50]}...")

        # Test creating a simple table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert test data
        cur.execute("INSERT INTO test_connection (message) VALUES (%s)", ("PostgreSQL adapters ready!",))

        # Query data
        cur.execute("SELECT * FROM test_connection ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        print(f"✅ Test data inserted: ID={row[0]}, Message='{row[1]}'")

        conn.commit()
        cur.close()
        conn.close()

        print("\n🎉 PostgreSQL is working perfectly!")
        print("Your DDD project can now use PostgreSQL as the database.")
        return True

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if not success:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Check that database 'supreme_octosuccotash_db' exists")
        print("3. Verify user 'app_user' has permissions")
        exit(1)
