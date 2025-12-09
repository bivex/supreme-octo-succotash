#!/usr/bin/env python3
"""Test runner script that properly sets up Python paths."""

import sys
import os
import pytest

# Add current directory and src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

if __name__ == "__main__":
    # Run pytest with the correct arguments
    sys.exit(pytest.main(["-v", "tests/unit/"]))
