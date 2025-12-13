#!/bin/bash

# Telegram Bot Auto Restarter with localhost.run Tunnel
# This script automatically sets up SSH tunnel and runs the bot in webhook mode

set -e  # Exit on any error

echo "========================================="
echo "  Telegram Bot Auto Restarter"
echo "  with localhost.run Tunnel"
echo "========================================="
echo

cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -i :$port >/dev/null 2>&1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tulpn 2>/dev/null | grep ":$port " >/dev/null
    else
        # Fallback: try to bind to the port
        (echo >/dev/tcp/localhost/$port) >/dev/null 2>&1
    fi
}

# Function to kill process on port
kill_process_on_port() {
    local port=$1
    local pids=""

    # Method 1: Use lsof
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -ti :$port 2>/dev/null)
    fi

    # Method 2: Use netstat/ss if lsof not available or no results
    if [ -z "$pids" ]; then
        if command -v ss >/dev/null 2>&1; then
            pids=$(ss -tulpn | grep ":$port " | awk '{print $7}' | cut -d',' -f1 | cut -d'=' -f2 | tr '\n' ' ')
        elif command -v netstat >/dev/null 2>&1; then
            pids=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | tr '\n' ' ')
        fi
    fi

    # Kill all found PIDs
    for pid in $pids; do
        if [ ! -z "$pid" ] && [ "$pid" != "-" ]; then
            echo "Killing process $pid on port $port"
            kill -TERM $pid 2>/dev/null && sleep 1
            if kill -0 $pid 2>/dev/null; then
                echo "Force killing process $pid"
                kill -9 $pid 2>/dev/null
            fi
        fi
    done

    # Wait and verify
    sleep 2
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    echo "Please create .env file with BOT_TOKEN and other settings"
    echo "Example:"
    echo "BOT_TOKEN=your_bot_token_here"
    echo "ADMIN_IDS=[123456789]"
    echo "TRACKER_DOMAIN=your-tracker-domain.com"
    echo "LANDING_URL=https://your-domain.com/landing"
    exit 1
fi

print_status ".env file found"

# Load environment variables from .env file
set -a
source .env
set +a

# Check if BOT_TOKEN is set
if [ -z "$BOT_TOKEN" ]; then
    print_error "BOT_TOKEN not found in .env file!"
    echo "Please add BOT_TOKEN=your_actual_token to .env file"
    exit 1
fi

print_status "BOT_TOKEN configured (${BOT_TOKEN:0:10}...)"

# Set default port or use from environment
PORT=${PORT:-3000}
print_info "Using port: $PORT"

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ]; then
    print_warning "SSH key not found. Generating new key..."
    ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""
    print_status "SSH key generated"
fi

# Function to kill all interfering bot instances
kill_all_bots() {
    print_info "Checking for interfering bot instances..."

    # Find all python3 bot.py processes
    local PIDS=$(ps aux | grep "python3 bot.py" | grep -v grep | awk '{print $2}')

    if [ -n "$PIDS" ]; then
        print_warning "Found running bot instances, killing them..."
        for pid in $PIDS; do
            echo "  Killing bot PID: $pid"
            kill -9 "$pid" 2>/dev/null || true
        done
        print_status "All interfering bots killed"
        sleep 1
    else
        print_status "No interfering bots found"
    fi

    # Also kill any orphaned SSH tunnels to localhost.run
    local TUNNEL_PIDS=$(ps aux | grep "ssh.*localhost.run" | grep -v grep | awk '{print $2}')
    if [ -n "$TUNNEL_PIDS" ]; then
        print_warning "Found orphaned SSH tunnels, killing them..."
        for pid in $TUNNEL_PIDS; do
            echo "  Killing tunnel PID: $pid"
            kill -9 "$pid" 2>/dev/null || true
        done
        print_status "All orphaned tunnels killed"
    fi
}

# Function to cleanup on exit
cleanup() {
    print_info "Cleaning up..."
    # Kill background processes
    if [ ! -z "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID 2>/dev/null || true
    fi
    if [ ! -z "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Kill any interfering instances before starting
kill_all_bots

print_info "Setting up localhost.run tunnel..."

# Start SSH tunnel in background and capture output
exec 3< <(ssh -o StrictHostKeyChecking=no -R 80:localhost:3000 ssh.localhost.run 2>&1)
TUNNEL_PID=$!

# Wait for tunnel to establish and extract URL
TUNNEL_URL=""
TIMEOUT=30
COUNTER=0

while [ $COUNTER -lt $TIMEOUT ]; do
    if read -t 1 -u 3 line; then
        echo "$line"
        # Look for the tunnel URL in the output
        if [[ $line =~ https://([a-zA-Z0-9]+\.lhr\.life) ]]; then
            TUNNEL_URL="https://${BASH_REMATCH[1]}"
            print_status "Tunnel URL detected: $TUNNEL_URL"
            break
        fi
    fi
    COUNTER=$((COUNTER + 1))
done

if [ -z "$TUNNEL_URL" ]; then
    print_error "Failed to establish tunnel or extract URL within $TIMEOUT seconds"
    cleanup
    exit 1
fi

print_status "Tunnel established successfully"

# Wait a moment for tunnel to be fully ready
sleep 2

# Check and free up port if needed
if is_port_in_use $PORT; then
    print_warning "Port $PORT is already in use. Attempting to free it..."
    kill_process_on_port $PORT
    if is_port_in_use $PORT; then
        print_error "Could not free port $PORT."
        # Try alternative ports
        for alt_port in 3001 3002 8000 8080; do
            if ! is_port_in_use $alt_port; then
                print_info "Trying alternative port: $alt_port"
                PORT=$alt_port
                break
            fi
        done

        if is_port_in_use $PORT; then
            print_error "All attempted ports are in use. Please manually free up ports 3000, 3001, 3002, 8000, or 8080 and try again."
            cleanup
            exit 1
        fi
    fi
    print_status "Using port $PORT"
fi

print_info "Starting Telegram bot in webhook mode..."
print_info "Webhook URL: $TUNNEL_URL/webhook"

# Start the bot
python3 bot.py --mode webhook --webhook-url "$TUNNEL_URL/webhook" --port $PORT &
BOT_PID=$!

print_status "Bot started (PID: $BOT_PID)"
print_info "Tunnel PID: $TUNNEL_PID"
echo
print_info "Press Ctrl+C to stop both tunnel and bot"
echo

# Wait for processes
wait $BOT_PID

# Cleanup
cleanup
