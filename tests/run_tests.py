
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:37
# Last Updated: 2025-12-18T12:12:37
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test runner for Advertising Platform SDK

Run all tests with coverage reporting.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the test suite."""
    try:
        # Change to the SDK directory
        sdk_dir = Path(__file__).parent.parent / "advertising_platform_sdk"
        sys.path.insert(0, str(sdk_dir))

        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=advertising_platform_sdk",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ], cwd=Path(__file__).parent.parent)

        return result.returncode

    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)