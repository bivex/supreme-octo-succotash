#!/bin/bash

# Restarter script for main_clean.py
# Cleans all PIDs from file and restarts the application

set -e  # Exit on any error

echo "========================================"
echo "  Main Clean Server Restarter"
echo "========================================"
echo

PID_FILE="main_clean.pid"

# Function to kill all interfering server instances
kill_all_servers() {
    echo "Checking for interfering server instances..."

    # Find all python3 main_clean.py processes
    PIDS=$(ps aux | grep "python3 main_clean.py" | grep -v grep | awk '{print $2}')

    if [ -n "$PIDS" ]; then
        echo "Found running server instances, killing them..."
        for pid in $PIDS; do
            echo "  Killing PID: $pid"
            kill -9 "$pid" 2>/dev/null || true
        done
        echo "✓ All interfering servers killed"
        sleep 1
    else
        echo "✓ No interfering servers found"
    fi
}

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

# Function to clean up hanging database connections
cleanup_db_connections() {
    echo
    echo "Cleaning up hanging database connections..."

    # Database credentials
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_NAME="supreme_octosuccotash_db"
    DB_USER="app_user"
    DB_PASS="app_password"

    # Terminate all connections except the current one
    TERMINATED=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null)

    if [ -n "$TERMINATED" ] && [ "$TERMINATED" -gt 0 ]; then
        echo "Found $TERMINATED hanging connections, terminating them..."
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
            > /dev/null 2>&1
        echo "✓ Terminated $TERMINATED hanging database connections"
    else
        echo "✓ No hanging connections found"
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
kill_all_servers
cleanup_processes
cleanup_db_connections
start_application