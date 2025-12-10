#!/usr/bin/env python3
"""
Simple test for PostgreSQL adapters.
"""

import sys
import os
sys.path.insert(0, 'src')

# Import directly to avoid module issues
import importlib.util

def load_module_from_file(name, filepath):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load modules directly
ltv_module = load_module_from_file("postgres_ltv", "src/infrastructure/repositories/postgres_ltv_repository.py")
retention_module = load_module_from_file("postgres_retention", "src/infrastructure/repositories/postgres_retention_repository.py")
form_module = load_module_from_file("postgres_form", "src/infrastructure/repositories/postgres_form_repository.py")

PostgresLTVRepository = ltv_module.PostgresLTVRepository
PostgresRetentionRepository = retention_module.PostgresRetentionRepository
PostgresFormRepository = form_module.PostgresFormRepository

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
