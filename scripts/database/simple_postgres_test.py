#!/usr/bin/env python3
"""
Simple test for PostgreSQL adapters.
"""

from src.infrastructure.repositories.postgres_ltv_repository import PostgresLTVRepository
from src.infrastructure.repositories.postgres_retention_repository import PostgresRetentionRepository
from src.infrastructure.repositories.postgres_form_repository import PostgresFormRepository

def test_basic_connection():
    """Test basic connection to PostgreSQL."""
    print("🧪 Testing PostgreSQL connection...")

    try:
        # Test LTV repository connection
        ltv_repo = PostgresLTVRepository()
        print("✅ PostgresLTVRepository connected successfully")

        # Test Retention repository connection
        retention_repo = PostgresRetentionRepository()
        print("✅ PostgresRetentionRepository connected successfully")

        # Test Form repository connection
        form_repo = PostgresFormRepository()
        print("✅ PostgresFormRepository connected successfully")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_connection()
    if success:
        print("\n🎉 All PostgreSQL adapters connected successfully!")
        print("Your DDD project now supports PostgreSQL!")
    else:
        print("\n❌ PostgreSQL adapter tests failed.")
        sys.exit(1)
