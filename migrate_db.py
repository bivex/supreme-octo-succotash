
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:07
# Last Updated: 2025-12-18T12:12:07
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Database migration script to create missing tables.
Automatically discovers repository classes and creates their tables.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import importlib
import inspect
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'supreme_octosuccotash_db',
    'user': 'app_user',
    'password': 'app_password'
}

def get_existing_tables(conn):
    """Get list of existing tables in the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def find_repository_files():
    """Find all PostgreSQL repository files."""
    repo_dir = Path(__file__).parent / 'src' / 'infrastructure' / 'repositories'
    return list(repo_dir.glob('postgres_*.py'))

def extract_table_info_from_file(file_path):
    """Extract table creation SQL from repository file."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Find CREATE TABLE statements - improved regex to handle nested parentheses
    import re

    # Split content to find cursor.execute blocks
    tables = {}
    indexes = {}

    # Find all cursor.execute() calls with CREATE TABLE
    execute_pattern = r'cursor\.execute\s*\(\s*"""(.*?)"""\s*\)'
    execute_matches = re.finditer(execute_pattern, content, re.DOTALL)

    for match in execute_matches:
        sql = match.group(1).strip()

        # Check if it's a CREATE TABLE statement
        if 'CREATE TABLE IF NOT EXISTS' in sql:
            # Extract table name
            table_match = re.search(r'CREATE TABLE IF NOT EXISTS\s+(\w+)', sql)
            if table_match:
                table_name = table_match.group(1)
                tables[table_name] = {
                    'name': table_name,
                    'definition': sql,
                    'file': file_path.name
                }

        # Check if it's a CREATE INDEX statement
        elif 'CREATE INDEX IF NOT EXISTS' in sql:
            index_match = re.search(r'ON\s+(\w+)', sql)
            if index_match:
                table_name = index_match.group(1)
                if table_name not in indexes:
                    indexes[table_name] = []
                indexes[table_name].append(sql)

    return tables, indexes

def create_missing_tables(conn, dry_run=False):
    """Create missing tables in the database."""
    print("=" * 80)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 80)
    print()

    # Get existing tables
    existing_tables = get_existing_tables(conn)
    print(f"📊 Existing tables ({len(existing_tables)}):")
    for table in sorted(existing_tables):
        print(f"  ✓ {table}")
    print()

    # Find all repository files
    repo_files = find_repository_files()
    print(f"🔍 Found {len(repo_files)} repository files")
    print()

    # Extract table definitions
    all_tables = {}
    all_indexes = {}

    for repo_file in repo_files:
        tables, indexes = extract_table_info_from_file(repo_file)
        all_tables.update(tables)
        all_indexes.update(indexes)

    # Find missing tables
    missing_tables = {
        name: info for name, info in all_tables.items()
        if name not in existing_tables
    }

    if not missing_tables:
        print("✅ All tables exist! No migration needed.")
        return

    print(f"⚠️  Missing tables ({len(missing_tables)}):")
    for table_name, info in sorted(missing_tables.items()):
        print(f"  ✗ {table_name} (from {info['file']})")
    print()

    if dry_run:
        print("DRY RUN MODE - Showing SQL that would be executed:")
        print("=" * 80)
        for table_name, info in sorted(missing_tables.items()):
            print(f"\n-- Table: {table_name}")
            print(info['definition'] + ";")

            # Show indexes for this table
            if table_name in all_indexes:
                for index_sql in all_indexes[table_name]:
                    print(index_sql + ";")
        print("=" * 80)
        return

    # Create missing tables
    cursor = conn.cursor()
    created_count = 0

    for table_name, info in sorted(missing_tables.items()):
        try:
            print(f"📝 Creating table: {table_name}...")

            # Execute CREATE TABLE
            cursor.execute(info['definition'])

            # Execute CREATE INDEX statements
            if table_name in all_indexes:
                for index_sql in all_indexes[table_name]:
                    cursor.execute(index_sql)

            conn.commit()
            created_count += 1
            print(f"  ✅ Created {table_name}")

        except Exception as e:
            print(f"  ❌ Error creating {table_name}: {e}")
            conn.rollback()

    cursor.close()

    print()
    print(f"✅ Migration complete! Created {created_count}/{len(missing_tables)} tables")

    # Show final table count
    final_tables = get_existing_tables(conn)
    print(f"📊 Total tables in database: {len(final_tables)}")

def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description='Database migration script')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--show-connections', action='store_true',
                       help='Show active database connections')
    args = parser.parse_args()

    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected!")
        print()

        if args.show_connections:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pid, usename, application_name, client_addr, state, query_start
                FROM pg_stat_activity
                WHERE datname = 'supreme_octosuccotash_db'
                ORDER BY query_start DESC
            """)
            connections = cursor.fetchall()
            print(f"📊 Active connections: {len(connections)}")
            for pid, user, app, addr, state, start in connections[:10]:
                print(f"  PID {pid}: {user} ({app}) - {state}")
            cursor.close()
            print()

        # Run migration
        create_missing_tables(conn, dry_run=args.dry_run)

        conn.close()

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
