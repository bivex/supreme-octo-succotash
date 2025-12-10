#!/usr/bin/env python3
"""
Python Source Files Merger

Combines all Python source files from a directory into a single text file
for analysis, documentation, or archival purposes.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set


@dataclass
class MergeConfig:
    """Configuration for the file merger."""
    root_dir: str = "."
    output_file: str = "merged_python_sources.txt"
    skip_dirs: Set[str] = None
    skip_files: Set[str] = None
    skip_extensions: Set[str] = None
    skip_patterns: Set[str] = None

    def __post_init__(self):
        if self.skip_dirs is None:
            self.skip_dirs = {
                "__pycache__", ".venv", "venv", ".env", "node_modules",
                ".git", ".cursor", ".vscode", ".idea",
                "build", "dist", ".pytest_cache", ".mypy_cache",
                ".tox", ".coverage", "htmlcov", "docs",
                "scripts", "tests", "migrations"
            }

        if self.skip_files is None:
            self.skip_files = {
                "merge_python_files.py",  # This merge script
                "setup.py", "conftest.py"
            }

        if self.skip_extensions is None:
            self.skip_extensions = {".pyc"}

        if self.skip_patterns is None:
            self.skip_patterns = {".bak", ".tmp", ".log"}


class PythonFileMerger:
    """Handles merging Python source files into a single output file."""

    def __init__(self, config: MergeConfig):
        self.config = config
        self.root_path = Path(config.root_dir).resolve()

    def validate_root_directory(self) -> bool:
        """Validate that the root directory exists."""
        if not self.root_path.exists():
            print(f"Error: Directory '{self.config.root_dir}' does not exist")
            return False

        if not self.root_path.is_dir():
            print(f"Error: '{self.config.root_dir}' is not a directory")
            return False

        return True

    def should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped based on configuration."""
        # Check if file is in skipped directories
        for part in file_path.parts:
            if part in self.config.skip_dirs:
                return True

        # Check if filename is in skip list
        if file_path.name in self.config.skip_files:
            return True

        # Check file extension
        if file_path.suffix in self.config.skip_extensions:
            return True

        # Check patterns (files starting with dot or ending with patterns)
        if file_path.name.startswith('.'):
            return True

        for pattern in self.config.skip_patterns:
            if file_path.name.endswith(pattern):
                return True

        return False

    def find_python_files(self) -> List[Path]:
        """Find all Python files that should be included in the merge."""
        python_files = []

        for py_file in self.root_path.rglob("*.py"):
            if not self.should_skip_file(py_file):
                python_files.append(py_file)

        # Sort for consistent output
        python_files.sort()
        return python_files

    def read_file_content(self, file_path: Path) -> str:
        """Read file content with fallback encoding support."""
        encodings_to_try = ['utf-8', 'cp1251', 'latin1']

        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    if encoding != 'utf-8':
                        content = f"--- File read with {encoding.upper()} encoding ---\n{content}"
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return f"--- File read error: {e} ---\n"

        return "--- ERROR: Could not read file with any supported encoding ---\n"

    def write_header(self, outfile, python_files: List[Path]) -> None:
        """Write the header information to the output file."""
        outfile.write("PYTHON SOURCE FILES MERGER\n")
        outfile.write("=" * 50 + "\n\n")
        outfile.write(f"Files combined: {len(python_files)}\n")
        outfile.write(f"Root directory: {self.root_path}\n")
        outfile.write(f"Output file: {Path(self.config.output_file).resolve()}\n\n")

        # Write exclusion information
        outfile.write("EXCLUDED DIRECTORIES:\n")
        dirs_str = ", ".join(sorted(self.config.skip_dirs))
        outfile.write(f"- {dirs_str}\n\n")

        outfile.write("EXCLUDED FILES:\n")
        files_str = ", ".join(sorted(self.config.skip_files))
        outfile.write(f"- {files_str}\n")

        exts_str = ", ".join(f"*{ext}" for ext in sorted(self.config.skip_extensions))
        outfile.write(f"- {exts_str}\n")

        patterns_str = ", ".join(f"*{pat}" for pat in sorted(self.config.skip_patterns))
        outfile.write(f"- {patterns_str}, files starting with .\n\n")

        outfile.write("=" * 50 + "\n\n")

    def write_file_content(self, outfile, file_path: Path, index: int) -> None:
        """Write a single file's content to the output file."""
        relative_path = file_path.relative_to(self.root_path)
        file_size = file_path.stat().st_size

        # Write file header
        outfile.write(f"[{index:3d}] {'='*10} {relative_path} {'='*10}\n")
        outfile.write(f"Full path: {file_path}\n")
        outfile.write(f"Size: {file_size} bytes\n\n")

        # Write file content
        content = self.read_file_content(file_path)
        outfile.write(content)
        outfile.write("\n\n")

        # Write file footer
        outfile.write(f"{'='*20} END OF FILE {relative_path} {'='*20}\n\n\n")

    def merge_files(self) -> bool:
        """Main merge operation."""
        if not self.validate_root_directory():
            return False

        python_files = self.find_python_files()

        if not python_files:
            print("No Python files found matching the criteria")
            return False

        print(f"Found {len(python_files)} Python files to merge")
        print(f"Output will be written to: {Path(self.config.output_file).resolve()}")

        try:
            with open(self.config.output_file, 'w', encoding='utf-8') as outfile:
                self.write_header(outfile, python_files)

                for i, py_file in enumerate(python_files, 1):
                    if i % 10 == 0 or i == len(python_files):
                        print(f"Processing file {i}/{len(python_files)}: {py_file.name}")

                    self.write_file_content(outfile, py_file, i)

            print("\nSuccessfully merged all files!")
            print(f"Total files processed: {len(python_files)}")
            print(f"Output file: {Path(self.config.output_file).resolve()}")

            return True

        except Exception as e:
            print(f"Error during merge operation: {e}")
            return False


def parse_arguments() -> MergeConfig:
    """Parse command line arguments into configuration."""
    config = MergeConfig()

    if len(sys.argv) > 1:
        config.root_dir = sys.argv[1]

    if len(sys.argv) > 2:
        config.output_file = sys.argv[2]

    return config


def main():
    """Main entry point."""
    print("Python Source Files Merger")
    print("=" * 40)

    config = parse_arguments()

    print(f"Root directory: {config.root_dir}")
    print(f"Output file: {config.output_file}")
    print("-" * 40)

    merger = PythonFileMerger(config)
    success = merger.merge_files()

    if not success:
        print("\nMerge operation failed")
        sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
