#!/usr/bin/env python3
"""
Fix PostgreSQL permissions for the app_user to create tables.
"""

import psycopg2


def fix_permissions():
    """Fix permissions for the app_user."""

    # PostgreSQL superuser credentials
    SUPERUSER_HOST = "localhost"
    SUPERUSER_PORT = 5432
    SUPERUSER_DB = "supreme_octosuccotash_db"  # Connect to our app database
    SUPERUSER_USER = "postgres"
    SUPERUSER_PASSWORD = "postgres"

    # Application settings
    APP_USER = "app_user"

    print("🔧 Fixing PostgreSQL permissions for app_user...")

    try:
        # Connect as superuser to the app database
        print("📡 Connecting to database as superuser...")
        conn = psycopg2.connect(
            host=SUPERUSER_HOST,
            port=SUPERUSER_PORT,
            database=SUPERUSER_DB,
            user=SUPERUSER_USER,
            password=SUPERUSER_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Grant schema permissions
        print("🔑 Granting schema permissions...")
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {APP_USER}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {APP_USER}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {APP_USER}")

        # Grant future permissions
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {APP_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {APP_USER}")

        cursor.close()
        conn.close()

        print("✅ Permissions fixed successfully!")
        print(f"User {APP_USER} can now create tables in the database.")

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = fix_permissions()
    if not success:
        exit(1)
