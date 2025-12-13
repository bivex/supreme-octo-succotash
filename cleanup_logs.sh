#!/bin/bash

# Log Cleanup Script for Supreme Octo Succotash Project
# This script manages log files across the application and telegram bot

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Log directories and files
LOG_FILES=(
    "$PROJECT_ROOT/app.log"
    "$PROJECT_ROOT/server.log"
    "$PROJECT_ROOT/telegram_landing_bot/logs/bot.log"
)

LOG_DIRS=(
    "$PROJECT_ROOT/telegram_landing_bot/logs"
)

# Default settings
MAX_LOG_SIZE_MB=10  # Rotate logs larger than 10MB
MAX_BACKUP_AGE_DAYS=30  # Delete backups older than 30 days
DRY_RUN=false
FULL_CLEANUP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Show usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Log cleanup script for the Supreme Octo Succotash project.

OPTIONS:
    -s, --max-size MB       Maximum log file size in MB before rotation (default: $MAX_LOG_SIZE_MB)
    -a, --max-age DAYS      Maximum age in days for backup files before deletion (default: $MAX_BACKUP_AGE_DAYS)
    -f, --full              Full cleanup: rotate all non-empty logs and delete all backups
    -d, --dry-run           Show what would be done without making changes
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Run cleanup with default settings
    $0 -s 5 -a 7            # Rotate logs > 5MB, delete backups > 7 days old
    $0 --full               # Full cleanup: rotate all logs and delete all backups
    $0 --dry-run            # Preview what would be cleaned up

LOG FILES MANAGED:
    - app.log (main application log)
    - server.log (server startup log)
    - telegram_landing_bot/logs/bot.log (telegram bot log)

BACKUP STRATEGY:
    - Rotates logs when they exceed size limit
    - Creates timestamped backups (e.g., bot.log.2025-12-13_12-00-00)
    - Removes backups older than specified age
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--max-size)
                MAX_LOG_SIZE_MB="$2"
                shift 2
                ;;
            -a|--max-age)
                MAX_BACKUP_AGE_DAYS="$2"
                shift 2
                ;;
            -f|--full)
                FULL_CLEANUP=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Get file size in MB
get_file_size_mb() {
    local file="$1"
    if [[ -f "$file" ]]; then
        # Use du to get size in KB, then convert to MB
        echo "$(($(du -k "$file" | cut -f1) / 1024))"
    else
        echo "0"
    fi
}

# Rotate a log file if it exceeds the size limit
rotate_log() {
    local log_file="$1"
    local base_name=$(basename "$log_file")
    local dir_name=$(dirname "$log_file")

    if [[ ! -f "$log_file" ]]; then
        log_info "Log file does not exist: $log_file"
        return 0
    fi

    local size_mb=$(get_file_size_mb "$log_file")

    # For full cleanup, rotate any non-empty file
    # Otherwise, rotate only if file exceeds size limit
    local should_rotate=false
    if [[ "$FULL_CLEANUP" == "true" ]] && [[ -s "$log_file" ]]; then
        # File exists and is not empty
        should_rotate=true
    elif (( $(echo "$size_mb > $MAX_LOG_SIZE_MB" | bc -l) )); then
        should_rotate=true
    fi

    if [[ "$should_rotate" == "true" ]]; then
        local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
        local backup_file="${dir_name}/${base_name}.${timestamp}"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would rotate $log_file (${size_mb}MB) to $backup_file"
        else
            log_info "Rotating $log_file (${size_mb}MB) to $backup_file"
            mv "$log_file" "$backup_file"

            # Create new empty log file with proper permissions
            touch "$log_file"
            chmod 644 "$log_file"

            log_success "Rotated $log_file to $backup_file"
        fi
    else
        log_info "Log file $log_file (${size_mb}MB) is within size limit"
    fi
}

# Clean up old backup files
cleanup_old_backups() {
    local log_dir="$1"

    if [[ ! -d "$log_dir" ]]; then
        log_warn "Log directory does not exist: $log_dir"
        return 0
    fi

    log_info "Checking for old backup files in $log_dir"

    # Find backup files older than MAX_BACKUP_AGE_DAYS
    local old_backups=$(find "$log_dir" -name "*.log.*" -type f -mtime +$MAX_BACKUP_AGE_DAYS 2>/dev/null || true)

    if [[ -z "$old_backups" ]]; then
        log_info "No old backup files found in $log_dir"
        return 0
    fi

    local count=$(echo "$old_backups" | wc -l | tr -d ' ')

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would delete $count old backup files in $log_dir:"
        echo "$old_backups" | while read -r file; do
            echo "  - $file"
        done
    else
        log_info "Deleting $count old backup files in $log_dir"
        echo "$old_backups" | while read -r file; do
            log_info "Removing $file"
            rm -f "$file"
        done
        log_success "Cleaned up $count old backup files"
    fi
}

# Show current log status
show_status() {
    echo
    log_info "Current Log Status:"
    echo "===================="

    for log_file in "${LOG_FILES[@]}"; do
        if [[ -f "$log_file" ]]; then
            local size_mb=$(get_file_size_mb "$log_file")
            local last_modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$log_file" 2>/dev/null || echo "unknown")
            printf "  %-35s %6s MB  Modified: %s\n" "$(basename "$log_file")" "$size_mb" "$last_modified"
        else
            printf "  %-35s %6s MB  (file does not exist)\n" "$(basename "$log_file")" "0"
        fi
    done

    echo
    log_info "Backup Files:"
    echo "=============="

    for log_dir in "${LOG_DIRS[@]}"; do
        if [[ -d "$log_dir" ]]; then
            local backup_count=$(find "$log_dir" -name "*.log.*" -type f 2>/dev/null | wc -l | tr -d ' ')
            local total_backup_size=$(find "$log_dir" -name "*.log.*" -type f -exec du -k {} \; 2>/dev/null | awk '{sum += $1} END {print sum/1024 " MB"}' || echo "0 MB")

            if [[ "$backup_count" -gt 0 ]]; then
                printf "  %-35s %3d files  %s\n" "$(basename "$log_dir")/" "$backup_count" "$total_backup_size"
            else
                printf "  %-35s %3d files  %s\n" "$(basename "$log_dir")/" "0" "0 MB"
            fi
        fi
    done
    echo
}

# Main cleanup function
cleanup_logs() {
    log_info "Starting log cleanup process"
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi

    if [[ "$FULL_CLEANUP" == "true" ]]; then
        log_info "FULL CLEANUP MODE - Will rotate all non-empty logs and delete all backups"
        MAX_LOG_SIZE_MB=0  # Rotate any file > 0 bytes
        MAX_BACKUP_AGE_DAYS=0  # Delete all backups
    fi

    echo "Settings:"
    echo "  - Max log size: ${MAX_LOG_SIZE_MB}MB"
    echo "  - Max backup age: ${MAX_BACKUP_AGE_DAYS} days"
    echo

    # Show current status
    show_status

    # Rotate large log files
    log_info "Checking log file sizes..."
    for log_file in "${LOG_FILES[@]}"; do
        rotate_log "$log_file"
    done

    # Clean up old backups
    log_info "Cleaning up old backup files..."
    for log_dir in "${LOG_DIRS[@]}"; do
        cleanup_old_backups "$log_dir"
    done

    # Show final status
    if [[ "$DRY_RUN" == "false" ]]; then
        echo
        log_info "Final Status:"
        show_status
    fi

    log_success "Log cleanup completed successfully"
}

# Main execution
main() {
    parse_args "$@"

    # Validate inputs
    if ! [[ "$MAX_LOG_SIZE_MB" =~ ^[0-9]+$ ]] || [[ "$MAX_LOG_SIZE_MB" -le 0 ]]; then
        log_error "Invalid max size: $MAX_LOG_SIZE_MB. Must be a positive integer."
        exit 1
    fi

    if ! [[ "$MAX_BACKUP_AGE_DAYS" =~ ^[0-9]+$ ]] || [[ "$MAX_BACKUP_AGE_DAYS" -lt 0 ]]; then
        log_error "Invalid max age: $MAX_BACKUP_AGE_DAYS. Must be a non-negative integer."
        exit 1
    fi

    cleanup_logs
}

# Run main function with all arguments
main "$@"