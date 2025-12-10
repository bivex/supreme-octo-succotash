#!/usr/bin/env python3
"""
PostgreSQL database setup script for DDD project.
Creates the database, user, and tables for the application.
"""

import psycopg2
from psycopg2 import sql


def setup_database():
    """Set up PostgreSQL database for the DDD project."""

    # PostgreSQL superuser credentials (change these for your setup)
    SUPERUSER_HOST = "localhost"
    SUPERUSER_PORT = 5432
    SUPERUSER_DB = "postgres"  # Connect to default postgres database
    SUPERUSER_USER = "postgres"
    SUPERUSER_PASSWORD = "postgres"

    # Application database settings
    APP_DB_NAME = "supreme_octosuccotash_db"
    APP_USER = "app_user"
    APP_PASSWORD = "app_password"

    print("🚀 Setting up PostgreSQL database for DDD project...")

    try:
        # Connect as superuser
        print("📡 Connecting to PostgreSQL as superuser...")
        conn = psycopg2.connect(
            host=SUPERUSER_HOST,
            port=SUPERUSER_PORT,
            database=SUPERUSER_DB,
            user=SUPERUSER_USER,
            password=SUPERUSER_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (APP_DB_NAME,))
        if cursor.fetchone():
            print(f"⚠️  Database '{APP_DB_NAME}' already exists. Skipping creation.")
        else:
            # Create database
            print(f"📦 Creating database '{APP_DB_NAME}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(APP_DB_NAME)
            ))
            print(f"✅ Database '{APP_DB_NAME}' created successfully!")

        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (APP_USER,))
        if cursor.fetchone():
            print(f"⚠️  User '{APP_USER}' already exists. Skipping creation.")
        else:
            # Create user
            print(f"👤 Creating user '{APP_USER}'...")
            cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                sql.Identifier(APP_USER)
            ), [APP_PASSWORD])
            print(f"✅ User '{APP_USER}' created successfully!")

        # Grant permissions
        print(f"🔑 Granting permissions to '{APP_USER}' on database '{APP_DB_NAME}'...")
        cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(APP_DB_NAME),
            sql.Identifier(APP_USER)
        ))

        cursor.close()
        conn.close()

        print("\n🎉 Database setup completed!")
        print(f"   Database: {APP_DB_NAME}")
        print(f"   User: {APP_USER}")
        print(f"   Password: {APP_PASSWORD}")
        print("\n📝 Next steps:")
        print("   1. Run: python test_postgres_adapters.py")
        print("   2. Your DDD application is ready to use PostgreSQL!")

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure PostgreSQL service is running")
        print("   2. Check your superuser credentials")
        print("   3. Verify PostgreSQL is accepting connections")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = setup_database()
    if not success:
        exit(1)
