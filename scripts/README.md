# Scripts Directory

This directory contains utility scripts for the Affiliate Marketing API project.

## Available Scripts

### clean_cache.bat
**Windows Batch script** for cleaning Python cache files.
- Removes all `__pycache__` directories recursively
- Removes all `.pyc`, `.pyo`, and `.pyd` files
- Use when you need to clear Python bytecode cache

**Usage:**
```batch
clean_cache.bat
```

### clean_cache.ps1
**PowerShell script** for cleaning Python cache files (recommended).
- Removes all `__pycache__` directories recursively
- Removes all `.pyc`, `.pyo`, and `.pyd` files
- Shows detailed output of removed files
- Automatically finds project root directory

**Usage:**
```powershell
.\scripts\clean_cache.ps1
```

### kill_port_5000.bat
**Windows Batch script** for killing processes listening on port 5000.
- Finds all processes listening on port 5000
- Terminates them forcefully
- Useful when server doesn't shut down cleanly

**Usage:**
```batch
scripts\kill_port_5000.bat
```

### kill_port_5000.ps1
**PowerShell script** for killing processes listening on port 5000 (recommended).
- Finds all processes listening on port 5000
- Terminates them forcefully
- Shows detailed output of terminated processes
- More reliable than batch version

**Usage:**
```powershell
.\scripts\kill_port_5000.ps1
```

### test_endpoints.py
**Python script** for testing all API endpoints.
- Tests health check, campaigns, clicks, and analytics endpoints
- Validates HTTP status codes and JSON responses
- Provides detailed test results and summary

**Usage:**
```bash
python scripts/test_endpoints.py
```

**Requirements:**
- Server must be running on `http://127.0.0.1:5000`
- Start server first: `python main_clean.py`

## Maintenance Notes

- Run `kill_port_5000.ps1` when server doesn't shut down cleanly and port 5000 is still occupied
- Run `clean_cache.ps1` when switching between Python versions
- Run `clean_cache.ps1` when moving/renaming files to avoid import issues
- Run `test_endpoints.py` after code changes to verify API functionality
