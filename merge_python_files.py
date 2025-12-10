#!/usr/bin/env python3
"""
Python source files merger - combines all .py files into one txt file
"""

import os
import sys
from pathlib import Path

def merge_python_files(root_dir=".", output_file="merged_python_sources.txt"):
    """
    Combines all .py files from the specified directory into one txt file

    Args:
        root_dir (str): Root directory for file search
        output_file (str): Name of output file
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"Error: Directory {root_dir} does not exist")
        return False

    # Directories and files to exclude
    skip_dirs = {
        "__pycache__", ".venv", "venv", ".env", "node_modules",
        ".git", ".cursor", ".vscode", ".idea",
        "build", "dist", ".pytest_cache", ".mypy_cache",
        ".tox", ".coverage", "htmlcov", "docs", ".git",
        ".cursor", "scripts", "tests", "migrations"
    }

    skip_files = {
        "merge_python_files.py",  # This merge script
        "setup.py", "conftest.py"
    }

    # Collect all .py files
    python_files = []
    for py_file in root_path.rglob("*.py"):
        # Skip unwanted directories (check only immediate parents)
        skip_file = False
        for part in py_file.parts:
            if part in skip_dirs:
                skip_file = True
                break

        if skip_file:
            continue

        # Skip unwanted files
        if py_file.name in skip_files:
            continue

        # Skip files with .pyc extension
        if py_file.suffix == '.pyc':
            continue

        # Skip temporary files and backups
        if py_file.name.startswith('.') or py_file.name.endswith(('.bak', '.tmp', '.log')):
            continue

        python_files.append(py_file)

    if not python_files:
        print("No .py files found")
        return False

    print(f"Found {len(python_files)} Python files")

    # Debug: show first 10 files
    print("First 10 found files:")
    for i, f in enumerate(python_files[:10]):
        print(f"  {i+1}. {f}")
    print()

    # Sort files by path for consistency
    python_files.sort()

    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write("PYTHON SOURCE FILES MERGER\n")
            outfile.write("=" * 50 + "\n\n")
            outfile.write(f"Files combined: {len(python_files)}\n")
            outfile.write(f"Root directory: {root_path.absolute()}\n")
            outfile.write(f"Generated: {Path(output_file).absolute()}\n\n")
            outfile.write("EXCLUDED DIRECTORIES:\n")
            outfile.write("- __pycache__, .venv, venv, .env, node_modules\n")
            outfile.write("- .git, .cursor, .vscode, .idea\n")
            outfile.write("- build, dist, .pytest_cache, .mypy_cache, .tox\n")
            outfile.write("- .coverage, htmlcov, docs, scripts, tests, migrations\n\n")
            outfile.write("EXCLUDED FILES:\n")
            outfile.write("- merge_python_files.py, setup.py, conftest.py\n")
            outfile.write("- *.pyc, *.bak, *.tmp, *.log, files starting with .\n\n")
            outfile.write("=" * 50 + "\n\n")

            for i, py_file in enumerate(python_files, 1):
                relative_path = py_file.relative_to(root_path)

                outfile.write(f"[{i:3d}] {'='*10} {relative_path} {'='*10}\n")
                outfile.write(f"Full path: {py_file.absolute()}\n")
                outfile.write(f"Size: {py_file.stat().st_size} bytes\n\n")

                try:
                    with open(py_file, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(content)
                        outfile.write("\n\n")
                except UnicodeDecodeError:
                    # If file is not UTF-8, try other encodings
                    try:
                        with open(py_file, 'r', encoding='cp1251') as infile:
                            content = infile.read()
                            outfile.write(f"--- File read with CP1251 encoding ---\n")
                            outfile.write(content)
                            outfile.write("\n\n")
                    except UnicodeDecodeError:
                        outfile.write(f"--- ERROR: Could not read file with UTF-8 or CP1251 encodings ---\n\n")
                except Exception as e:
                    outfile.write(f"--- File read error: {e} ---\n\n")

                outfile.write(f"{'='*20} END OF FILE {relative_path} {'='*20}\n\n\n")

        print(f"Successfully combined {len(python_files)} files into {output_file}")
        print(f"Output file: {Path(output_file).absolute()}")
        return True

    except Exception as e:
        print(f"Error creating file: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "merged_python_sources.txt"

    print("Python Source Files Merger")
    print(f"Directory: {root_dir}")
    print(f"Output file: {output_file}")
    print("-" * 40)

    success = merge_python_files(root_dir, output_file)

    if success:
        print("\nDone!")
    else:
        print("\nAn error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main()
