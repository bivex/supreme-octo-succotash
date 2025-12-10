#!/usr/bin/env python3
"""
Development runner with hot reload support
"""

import subprocess
import sys
import os

def run_with_fallback():
    """Run server with reload, fallback to normal mode if watchdog not available."""
    try:
        # Try to run with reload
        result = subprocess.run([sys.executable, 'main_clean.py', '--reload'],
                              check=False, capture_output=True, text=True)
        return result.returncode
    except KeyboardInterrupt:
        print("\nDevelopment server stopped")
        return 0
    except Exception as e:
        print(f"Error running with reload: {e}")
        print("Falling back to normal mode...")
        return subprocess.run([sys.executable, 'main_clean.py']).returncode

if __name__ == "__main__":
    exit_code = run_with_fallback()
    sys.exit(exit_code)
