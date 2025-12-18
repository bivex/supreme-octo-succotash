# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:34
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Single-process version of the application for Intel Advisor threading analysis."""

import os

# Force single process mode for threading analysis
os.environ['WORKERS'] = '1'

# Import the main application
from src.main import create_app


def run_single_process_app():
    """Run the application in single process mode for threading analysis."""
    print("🚀 Starting application in single-process mode for Intel Advisor analysis...")

    import socketify
    app = create_app()

    print("🎯 Single-process server ready for Intel Advisor threading analysis")
    print("📊 Monitoring threads: cache monitor, connection pool monitor, upholder scheduler")

    # Use compatible listen options for current socketify version
    listen_options = socketify.AppListenOptions(
        port=5000,
        host="127.0.0.1",
    )

    def on_listen(config):
        print(f"✅ Server listening on {config.host}:{config.port}")
        print("🔬 Run your load tests now while Intel Advisor collects threading data")
        print("🛑 Press Ctrl+C to stop")

    try:
        app.listen(listen_options, on_listen)
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")


if __name__ == "__main__":
    run_single_process_app()
