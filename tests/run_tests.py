#!/usr/bin/env python3
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