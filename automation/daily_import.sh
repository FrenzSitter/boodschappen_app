#!/bin/bash

# CheckjeBon Daily Import Script
# ==============================
# Automated daily import wrapper for CheckjeBon data to Supabase
# This script handles environment setup, execution, logging, and notifications

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMPORT_SCRIPT="$PROJECT_DIR/supabase_import.py"
VALIDATION_SCRIPT="$SCRIPT_DIR/data_validation.py"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
CONFIG_FILE="$PROJECT_DIR/.env"
LOCK_FILE="/tmp/checkjebon_import.lock"

# Logging configuration
LOG_FILE="$LOG_DIR/daily_import.log"
ERROR_LOG="$LOG_DIR/import_errors.log"
SUCCESS_LOG="$LOG_DIR/import_success.log"
RETENTION_DAYS=30

# Email configuration (optional)
EMAIL_ENABLED=${EMAIL_ENABLED:-false}
EMAIL_TO=${EMAIL_TO:-"admin@example.com"}
EMAIL_FROM=${EMAIL_FROM:-"noreply@checkjebon.local"}
EMAIL_SUBJECT="CheckjeBon Import Status"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${RED}ERROR${NC}: $1" | tee -a "$LOG_FILE" >> "$ERROR_LOG"
}

log_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${GREEN}SUCCESS${NC}: $1" | tee -a "$LOG_FILE" >> "$SUCCESS_LOG"
}

log_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${YELLOW}WARNING${NC}: $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${BLUE}INFO${NC}: $1" | tee -a "$LOG_FILE"
}

# Check if script is already running
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local lock_pid=$(cat "$LOCK_FILE")
        if kill -0 "$lock_pid" 2>/dev/null; then
            log_error "Import script is already running (PID: $lock_pid)"
            exit 1
        else
            log_warning "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

# Remove lock file on exit
cleanup() {
    rm -f "$LOCK_FILE"
    log_info "Cleanup completed"
}

# Setup directories
setup_directories() {
    log_info "Setting up directories..."
    
    # Create log directory if it doesn't exist
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        log_info "Created log directory: $LOG_DIR"
    fi
    
    # Create logs directory structure
    mkdir -p "$LOG_DIR/archive"
    
    # Set proper permissions
    chmod 755 "$LOG_DIR"
    chmod 644 "$LOG_DIR"/*.log 2>/dev/null || true
}

# Load environment variables
load_environment() {
    log_info "Loading environment variables..."
    
    # Load from .env file if it exists
    if [ -f "$CONFIG_FILE" ]; then
        log_info "Loading configuration from $CONFIG_FILE"
        source "$CONFIG_FILE"
    else
        log_warning "No .env file found at $CONFIG_FILE"
    fi
    
    # Check required environment variables
    if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
        log_error "Required environment variables not set:"
        log_error "  SUPABASE_URL: ${SUPABASE_URL:-'NOT SET'}"
        log_error "  SUPABASE_KEY: ${SUPABASE_KEY:+SET}"
        return 1
    fi
    
    log_info "Environment variables loaded successfully"
    return 0
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            log_error "Failed to create virtual environment"
            return 1
        fi
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    if [ $? -ne 0 ]; then
        log_error "Failed to activate virtual environment"
        return 1
    fi
    
    log_info "Virtual environment activated"
    
    # Update pip and install requirements
    pip install --upgrade pip > /dev/null 2>&1
    
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        log_info "Installing/updating Python dependencies..."
        pip install -r "$PROJECT_DIR/requirements.txt" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log_error "Failed to install Python dependencies"
            return 1
        fi
    fi
    
    log_info "Python environment setup complete"
    return 0
}

# Test database connectivity
test_connectivity() {
    log_info "Testing database connectivity..."
    
    # Use the import script with dry-run to test connectivity
    python "$IMPORT_SCRIPT" --dry-run --batch-size=1 > /dev/null 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_info "Database connectivity test passed"
        return 0
    else
        log_error "Database connectivity test failed"
        return 1
    fi
}

# Run the import process
run_import() {
    log_info "Starting CheckjeBon data import..."
    
    local start_time=$(date +%s)
    local temp_log=$(mktemp)
    
    # Run the import script with proper logging
    python "$IMPORT_SCRIPT" --verbose 2>&1 | tee "$temp_log"
    local exit_code=${PIPESTATUS[0]}
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Parse import statistics from output
    local stats=$(grep -A 10 "IMPORT SUMMARY" "$temp_log" | tail -n +2)
    
    if [ $exit_code -eq 0 ]; then
        log_success "Import completed successfully in ${duration}s"
        if [ -n "$stats" ]; then
            log_info "Import statistics:"
            echo "$stats" | while read -r line; do
                [ -n "$line" ] && log_info "  $line"
            done
        fi
        
        # Append to success log
        echo "$(date '+%Y-%m-%d %H:%M:%S') - SUCCESS - Duration: ${duration}s" >> "$SUCCESS_LOG"
        echo "$stats" >> "$SUCCESS_LOG"
        echo "---" >> "$SUCCESS_LOG"
        
    else
        log_error "Import failed with exit code: $exit_code"
        log_error "Duration: ${duration}s"
        
        # Extract error messages
        local errors=$(grep -i "error\|failed" "$temp_log")
        if [ -n "$errors" ]; then
            log_error "Error details:"
            echo "$errors" | while read -r line; do
                [ -n "$line" ] && log_error "  $line"
            done
        fi
        
        # Send failure notification
        send_failure_notification "$exit_code" "$duration" "$errors"
    fi
    
    # Clean up temp file
    rm -f "$temp_log"
    
    return $exit_code
}

# Run data validation after import
run_data_validation() {
    log_info "Starting post-import data validation..."
    
    local start_time=$(date +%s)
    local temp_log=$(mktemp)
    
    # Run data validation script
    python "$VALIDATION_SCRIPT" 2>&1 | tee "$temp_log"
    local exit_code=${PIPESTATUS[0]}
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        log_success "Data validation completed successfully in ${duration}s"
        
        # Extract validation summary
        local validation_summary=$(grep -A 5 "All validations passed\|Validation completed" "$temp_log" | tail -n 5)
        if [ -n "$validation_summary" ]; then
            log_info "Validation summary:"
            echo "$validation_summary" | while read -r line; do
                [ -n "$line" ] && log_info "  $line"
            done
        fi
        
    elif [ $exit_code -eq 1 ]; then
        log_error "Data validation failed with critical issues"
        
        # Extract validation errors
        local validation_errors=$(grep -i "FAIL\|ERROR" "$temp_log")
        if [ -n "$validation_errors" ]; then
            log_error "Validation errors:"
            echo "$validation_errors" | while read -r line; do
                [ -n "$line" ] && log_error "  $line"
            done
        fi
        
        # Send validation failure notification
        send_validation_failure_notification "$exit_code" "$duration" "$validation_errors"
        
    else
        log_warning "Data validation completed with warnings"
        
        # Extract validation warnings
        local validation_warnings=$(grep -i "WARN" "$temp_log")
        if [ -n "$validation_warnings" ]; then
            log_warning "Validation warnings:"
            echo "$validation_warnings" | while read -r line; do
                [ -n "$line" ] && log_warning "  $line"
            done
        fi
    fi
    
    # Clean up temp file
    rm -f "$temp_log"
    
    return $exit_code
}

# Send validation failure notification
send_validation_failure_notification() {
    local exit_code=$1
    local duration=$2
    local errors=$3
    
    if [ "$EMAIL_ENABLED" = "true" ]; then
        log_info "Sending validation failure notification email..."
        
        local email_body=$(cat <<EOF
CheckjeBon Data Validation Failure Report
========================================

Date: $(date)
Exit Code: $exit_code
Duration: ${duration}s
Host: $(hostname)

Validation Errors:
$errors

Health Report: $LOG_DIR/health_reports/health_report_$(date +%Y-%m-%d).html

Please investigate and resolve the data quality issues.
EOF
        )
        
        # Send email using system mail command
        if command -v mail >/dev/null 2>&1; then
            echo "$email_body" | mail -s "CheckjeBon Data Validation FAILURE" "$EMAIL_TO"
            log_info "Validation failure notification sent to $EMAIL_TO"
        elif command -v sendmail >/dev/null 2>&1; then
            (
                echo "To: $EMAIL_TO"
                echo "From: $EMAIL_FROM"
                echo "Subject: CheckjeBon Data Validation FAILURE"
                echo ""
                echo "$email_body"
            ) | sendmail "$EMAIL_TO"
            log_info "Validation failure notification sent via sendmail"
        else
            log_warning "No mail system available for validation notifications"
        fi
    fi
}

# Send failure notification
send_failure_notification() {
    local exit_code=$1
    local duration=$2
    local errors=$3
    
    if [ "$EMAIL_ENABLED" = "true" ]; then
        log_info "Sending failure notification email..."
        
        local email_body=$(cat <<EOF
CheckjeBon Import Failure Report
===============================

Date: $(date)
Exit Code: $exit_code
Duration: ${duration}s
Host: $(hostname)

Error Details:
$errors

Log File: $LOG_FILE
Error Log: $ERROR_LOG

Please investigate and resolve the issue.
EOF
        )
        
        # Send email using system mail command
        if command -v mail >/dev/null 2>&1; then
            echo "$email_body" | mail -s "$EMAIL_SUBJECT - FAILURE" "$EMAIL_TO"
            log_info "Failure notification sent to $EMAIL_TO"
        elif command -v sendmail >/dev/null 2>&1; then
            (
                echo "To: $EMAIL_TO"
                echo "From: $EMAIL_FROM"
                echo "Subject: $EMAIL_SUBJECT - FAILURE"
                echo ""
                echo "$email_body"
            ) | sendmail "$EMAIL_TO"
            log_info "Failure notification sent via sendmail"
        else
            log_warning "No mail system available for notifications"
        fi
    fi
}

# Rotate log files
rotate_logs() {
    log_info "Rotating log files..."
    
    # Archive old logs
    local archive_date=$(date -d "-${RETENTION_DAYS} days" +%Y%m%d)
    
    # Compress and move old logs
    for log_file in "$LOG_FILE" "$ERROR_LOG" "$SUCCESS_LOG"; do
        if [ -f "$log_file" ]; then
            # Check if log file is older than retention period
            if [ $(stat -c %Y "$log_file") -lt $(date -d "-${RETENTION_DAYS} days" +%s) ]; then
                log_info "Archiving old log: $(basename "$log_file")"
                gzip -c "$log_file" > "$LOG_DIR/archive/$(basename "$log_file").${archive_date}.gz"
                > "$log_file"  # Truncate the file
            fi
        fi
    done
    
    # Remove very old archived logs (older than 90 days)
    find "$LOG_DIR/archive" -name "*.gz" -mtime +90 -delete 2>/dev/null || true
    
    log_info "Log rotation completed"
}

# Generate daily report
generate_report() {
    log_info "Generating daily report..."
    
    local report_file="$LOG_DIR/daily_report_$(date +%Y%m%d).txt"
    
    cat > "$report_file" << EOF
CheckjeBon Daily Import Report
=============================
Date: $(date)
Host: $(hostname)

Recent Import Results:
EOF
    
    # Add last 5 successful imports
    if [ -f "$SUCCESS_LOG" ]; then
        echo "" >> "$report_file"
        echo "Recent Successful Imports:" >> "$report_file"
        tail -n 20 "$SUCCESS_LOG" | grep "SUCCESS" | tail -n 5 >> "$report_file"
    fi
    
    # Add recent errors
    if [ -f "$ERROR_LOG" ]; then
        echo "" >> "$report_file"
        echo "Recent Errors:" >> "$report_file"
        tail -n 20 "$ERROR_LOG" | grep "ERROR" | tail -n 5 >> "$report_file"
    fi
    
    # Add system information
    echo "" >> "$report_file"
    echo "System Information:" >> "$report_file"
    echo "  Disk Usage: $(df -h "$PROJECT_DIR" | tail -1 | awk '{print $5 " used"}')" >> "$report_file"
    echo "  Memory Usage: $(free -m | grep "Mem:" | awk '{print $3"/"$2" MB"}')" >> "$report_file"
    echo "  Python Version: $(python3 --version)" >> "$report_file"
    
    log_info "Daily report generated: $report_file"
}

# Health check
health_check() {
    log_info "Running health check..."
    
    local health_status=0
    
    # Check if import script exists
    if [ ! -f "$IMPORT_SCRIPT" ]; then
        log_error "Import script not found: $IMPORT_SCRIPT"
        health_status=1
    fi
    
    # Check if virtual environment is working
    if ! source "$VENV_DIR/bin/activate" 2>/dev/null; then
        log_error "Virtual environment not working"
        health_status=1
    fi
    
    # Check disk space
    local disk_usage=$(df "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Disk usage is high: ${disk_usage}%"
        health_status=1
    fi
    
    # Check log file sizes
    local log_size=$(du -sm "$LOG_DIR" 2>/dev/null | cut -f1)
    if [ "$log_size" -gt 100 ]; then
        log_warning "Log directory is large: ${log_size}MB"
    fi
    
    if [ $health_status -eq 0 ]; then
        log_info "Health check passed"
    else
        log_error "Health check failed"
    fi
    
    return $health_status
}

# Main execution
main() {
    # Setup signal handling
    trap cleanup EXIT
    
    # Start logging
    log_info "==============================================="
    log_info "Starting daily CheckjeBon import process"
    log_info "Script: $0"
    log_info "PID: $$"
    log_info "Project Directory: $PROJECT_DIR"
    log_info "==============================================="
    
    # Check for lock file
    check_lock
    
    # Setup directories
    setup_directories
    
    # Load environment
    if ! load_environment; then
        log_error "Failed to load environment"
        exit 1
    fi
    
    # Setup Python environment
    if ! setup_python_env; then
        log_error "Failed to setup Python environment"
        exit 1
    fi
    
    # Run health check
    if ! health_check; then
        log_error "Health check failed"
        exit 1
    fi
    
    # Test connectivity
    if ! test_connectivity; then
        log_error "Connectivity test failed"
        exit 1
    fi
    
    # Run the import
    if run_import; then
        log_success "Daily import completed successfully"
        import_exit_code=0
        
        # Run data validation after successful import
        log_info "Running post-import data validation..."
        if run_data_validation; then
            log_success "Data validation passed"
            exit_code=0
        else
            log_error "Data validation failed - import data may have quality issues"
            exit_code=1
        fi
    else
        log_error "Daily import failed"
        exit_code=1
        
        # Skip validation if import failed
        log_info "Skipping data validation due to import failure"
    fi
    
    # Rotate logs
    rotate_logs
    
    # Generate report
    generate_report
    
    log_info "Daily import process finished with exit code: $exit_code"
    log_info "==============================================="
    
    exit $exit_code
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --test         Run connectivity test only"
        echo "  --health       Run health check only"
        echo "  --dry-run      Run import in dry-run mode"
        echo "  --force        Force run even if lock file exists"
        echo ""
        exit 0
        ;;
    --test)
        setup_directories
        load_environment
        setup_python_env
        test_connectivity
        exit $?
        ;;
    --health)
        setup_directories
        load_environment
        setup_python_env
        health_check
        exit $?
        ;;
    --dry-run)
        log_info "Running in dry-run mode"
        IMPORT_SCRIPT="$IMPORT_SCRIPT --dry-run"
        main
        ;;
    --force)
        rm -f "$LOCK_FILE"
        main
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac