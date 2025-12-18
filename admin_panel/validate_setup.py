
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Validation script for Advertising Platform Admin Panel setup
"""

import sys
import importlib

MIN_PYTHON_MAJOR_VERSION = 3
MIN_PYTHON_MINOR_VERSION = 8

def check_dependency(module_name, package_name=None):
    """Check if a dependency is available."""
    if package_name is None:
        package_name = module_name

    try:
        importlib.import_module(module_name)
        print(f"✓ {package_name} is available")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT available")
        return False

def validate_setup():
    """Validate the admin panel setup."""
    print("Validating Advertising Platform Admin Panel setup...")
    print("=" * 50)

    # Check Python version
    python_version = sys.version_info
    if python_version >= (MIN_PYTHON_MAJOR_VERSION, MIN_PYTHON_MINOR_VERSION):
        print(f"✓ Python {python_version.major}.{python_version.minor} is supported")
    else:
        print(f"✗ Python {python_version.major}.{python_version.minor} is not supported (requires 3.8+)")
        return False

    print()

    # Check core dependencies
    dependencies = [
        ('PyQt6', 'PyQt6'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv'),
        ('qasync', 'qasync'),
    ]

    all_ok = True
    for module, package in dependencies:
        if not check_dependency(module, package):
            all_ok = False

    print()

    # Check Advertising Platform SDK
    try:
        import advertising_platform_sdk
        print("✓ Advertising Platform SDK is available")
    except ImportError:
        print("✗ Advertising Platform SDK is NOT available")
        print("  Please ensure it's installed: pip install -e advertising_platform_sdk/")
        all_ok = False

    print()

    # Check imports from SDK
    try:
        from advertising_platform_sdk.client import AdvertisingPlatformClient
        from advertising_platform_sdk.exceptions import APIError
        print("✓ SDK imports work correctly")
    except ImportError as e:
        print(f"✗ SDK imports failed: {e}")
        all_ok = False

    print()

    if all_ok:
        print("🎉 All validations passed! The admin panel is ready to run.")
        print()
        print("To start the admin panel:")
        print("  python main.py")
        print("  # or")
        print("  python run.py")
    else:
        print("❌ Some validations failed. Please install missing dependencies.")

    return all_ok

if __name__ == "__main__":
    success = validate_setup()
    sys.exit(0 if success else 1)