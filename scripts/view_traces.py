
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
Script to view and analyze saved async traces.
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime
import webbrowser

def list_trace_files():
    """List all trace files in the traces directory."""
    traces_dir = Path("traces")
    if not traces_dir.exists():
        print("❌ Traces directory not found. Run server with --async-trace first.")
        return []

    files = []
    for pattern in ["*.html", "*.json"]:
        files.extend(traces_dir.glob(pattern))

    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

def analyze_trace_file(filepath):
    """Analyze a single trace file."""
    if filepath.suffix == ".html":
        print(f"🌐 HTML file: {filepath}")
        print("   Open in browser to view interactive visualization")
    elif filepath.suffix == ".json":
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            timestamp = datetime.fromtimestamp(data['timestamp'])
            task_name = data['current_task_name']
            frames_count = len(data['frames'])

            print(f"📄 JSON file: {filepath}")
            print(f"   Timestamp: {timestamp}")
            print(f"   Current task: {task_name}")
            print(f"   Frames in stack: {frames_count}")

            # Show task creation points
            task_frames = [f for f in data['frames'] if f.get('task_name')]
            if task_frames:
                print(f"   Task boundaries: {len(task_frames)}")
                for frame in task_frames[:3]:  # Show first 3
                    task_name = frame.get('task_name', 'unknown')
                    func_name = frame.get('name', 'unknown')
                    print(f"     • {func_name} → {task_name}")
                if len(task_frames) > 3:
                    print(f"     ... and {len(task_frames) - 3} more")

        except Exception as e:
            print(f"❌ Error reading JSON file: {e}")

def open_in_browser(filepath):
    """Open HTML file in default browser."""
    if filepath.suffix == ".html":
        try:
            webbrowser.open(str(filepath))
            print(f"🌐 Opened {filepath} in browser")
        except Exception as e:
            print(f"❌ Failed to open in browser: {e}")
    else:
        print("❌ Not an HTML file")

def main():
    """Main function."""
    print("🔍 Async Trace Viewer")
    print("=" * 50)

    files = list_trace_files()

    if not files:
        print("📭 No trace files found.")
        print("💡 Run the server with --async-trace to generate trace files:")
        print("   python main_clean.py --async-trace")
        return

    print(f"📂 Found {len(files)} trace files:")
    print()

    for i, filepath in enumerate(files, 1):
        print(f"{i}. ", end="")
        analyze_trace_file(filepath)
        print()

    print("Commands:")
    print("  open <number>  - Open HTML file in browser")
    print("  show <number>  - Show detailed JSON info")
    print("  q              - Quit")

    while True:
        try:
            cmd = input("\nEnter command: ").strip().lower()

            if cmd == 'q':
                break

            if cmd.startswith('open '):
                idx = int(cmd.split()[1]) - 1
                if 0 <= idx < len(files):
                    open_in_browser(files[idx])
                else:
                    print("❌ Invalid file number")

            elif cmd.startswith('show '):
                idx = int(cmd.split()[1]) - 1
                if 0 <= idx < len(files):
                    print(f"\n📋 Detailed info for {files[idx]}:")
                    analyze_trace_file(files[idx])
                else:
                    print("❌ Invalid file number")

            else:
                print("❓ Unknown command. Use 'open <number>', 'show <number>', or 'q'")

        except (ValueError, IndexError):
            print("❌ Invalid command format")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
