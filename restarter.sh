#!/bin/bash

# Restarter script for main_clean.py
# Cleans all PIDs from file and restarts the application

set -e  # Exit on any error

echo "========================================"
echo "  Main Clean Server Restarter"
echo "========================================"
echo

PID_FILE="main_clean.pid"

# Function to clean up processes
cleanup_processes() {
    if [ -f "$PID_FILE" ]; then
        echo "Cleaning up existing processes..."
        while IFS= read -r pid; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo "Stopping process with PID: $pid"
                kill "$pid" 2>/dev/null || true
                # Wait a bit for graceful shutdown
                sleep 2
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    echo "Force killing process with PID: $pid"
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
        echo "✓ All processes cleaned up"
    else
        echo "No existing PID file found"
    fi
}

# Function to start the application
start_application() {
    echo
    echo "Starting main_clean.py..."

    # Start the application in background and capture PID
    python3 main_clean.py &
    APP_PID=$!

    # Save PID to file
    echo "$APP_PID" > "$PID_FILE"
    echo "✓ Application started with PID: $APP_PID"
    echo "✓ PID saved to: $PID_FILE"

    echo
    echo "Application is running. Press Ctrl+C to stop."

    # Wait for the application process
    wait "$APP_PID"
}

# Function to handle cleanup on script exit
cleanup_on_exit() {
    echo
    echo "Received interrupt signal. Cleaning up..."
    cleanup_processes
    exit 0
}

# Set up signal handlers
trap cleanup_on_exit INT TERM

# Main execution
cleanup_processes
start_application