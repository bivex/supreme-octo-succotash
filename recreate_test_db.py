#!/usr/bin/env python3
"""
Recreate the test database to fix corruption issues.
"""
import sys
import os
import psycopg2
from psycopg2 import sql

# Set test database environment variables
os.environ.setdefault("DB_NAME", "test_supreme_octo_succotash")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")

def recreate_test_database():
    """Recreate the test database."""
    try:
        # Connect to postgres database to manage other databases
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="test_user",
            password="test_password"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Drop and recreate the test database
        print("Dropping test database if it exists...")
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier("test_supreme_octo_succotash")
        ))

        print("Creating new test database...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier("test_supreme_octo_succotash")
        ))

        cursor.close()
        conn.close()

        print("✅ Test database recreated successfully!")

    except Exception as e:
        print(f"❌ Failed to recreate test database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    recreate_test_database()
