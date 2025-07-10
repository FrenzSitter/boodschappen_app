#!/bin/bash

# CheckjeBon System Monitoring Script
# ===================================
# Comprehensive monitoring script for CheckjeBon import system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
MONITORING_LOG="$LOG_DIR/monitoring.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
ALERT_THRESHOLD_ERRORS=5
ALERT_THRESHOLD_DISK_USAGE=85
ALERT_THRESHOLD_LOG_SIZE=100  # MB
HEALTH_CHECK_INTERVAL=3600    # seconds

# Utility functions
log_monitor() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$MONITORING_LOG"
}

status_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

status_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

status_error() {
    echo -e "${RED}✗${NC} $1"
}

status_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# System information
show_system_info() {
    echo -e "${PURPLE}System Information${NC}"
    echo "=================="
    echo "Hostname: $(hostname)"
    echo "OS: $(uname -s) $(uname -r)"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "User: $(whoami)"
    echo "PWD: $(pwd)"
    echo "Date: $(date)"
    echo ""
}

# Check disk usage
check_disk_usage() {
    echo -e "${PURPLE}Disk Usage Check${NC}"
    echo "================"
    
    local usage=$(df "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    local available=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $4}')
    
    if [ "$usage" -gt "$ALERT_THRESHOLD_DISK_USAGE" ]; then
        status_error "Disk usage is critical: ${usage}% (Available: $available)"
        log_monitor "ALERT: High disk usage: ${usage}%"
        return 1
    elif [ "$usage" -gt 70 ]; then
        status_warning "Disk usage is high: ${usage}% (Available: $available)"
        log_monitor "WARNING: High disk usage: ${usage}%"
    else
        status_ok "Disk usage is normal: ${usage}% (Available: $available)"
    fi
    
    # Show detailed disk usage
    echo ""
    echo "Detailed disk usage:"
    df -h "$PROJECT_DIR"
    echo ""
    
    return 0
}

# Check log file sizes
check_log_sizes() {
    echo -e "${PURPLE}Log File Size Check${NC}"
    echo "==================="
    
    local total_size=0
    local alert_triggered=false
    
    if [ -d "$LOG_DIR" ]; then
        echo "Log directory: $LOG_DIR"
        echo ""
        
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                local size_mb=$(du -m "$log_file" 2>/dev/null | cut -f1)
                local size_human=$(du -h "$log_file" 2>/dev/null | cut -f1)
                local filename=$(basename "$log_file")
                
                if [ "$size_mb" -gt "$ALERT_THRESHOLD_LOG_SIZE" ]; then
                    status_error "$filename: $size_human (exceeds ${ALERT_THRESHOLD_LOG_SIZE}MB)"
                    alert_triggered=true
                elif [ "$size_mb" -gt 50 ]; then
                    status_warning "$filename: $size_human"
                else
                    status_ok "$filename: $size_human"
                fi
                
                total_size=$((total_size + size_mb))
            fi
        done
        
        echo ""
        echo "Total log size: ${total_size}MB"
        
        if [ "$alert_triggered" = true ]; then
            log_monitor "ALERT: Large log files detected"
            return 1
        fi
    else
        status_warning "Log directory not found: $LOG_DIR"
    fi
    
    return 0
}

# Check import status
check_import_status() {
    echo -e "${PURPLE}Import Status Check${NC}"
    echo "==================="
    
    local main_log="$LOG_DIR/daily_import.log"
    local error_log="$LOG_DIR/import_errors.log"
    local success_log="$LOG_DIR/import_success.log"
    
    # Check last import
    if [ -f "$main_log" ]; then
        local last_import=$(grep "Starting daily CheckjeBon import" "$main_log" | tail -1)
        if [ -n "$last_import" ]; then
            status_info "Last import started: $last_import"
        fi
        
        local last_success=$(grep "SUCCESS" "$main_log" | tail -1)
        local last_error=$(grep "ERROR" "$main_log" | tail -1)
        
        if [ -n "$last_success" ]; then
            status_ok "Last success: $last_success"
        fi
        
        if [ -n "$last_error" ]; then
            status_error "Last error: $last_error"
        fi
    else
        status_warning "Main log file not found: $main_log"
    fi
    
    # Check error count
    if [ -f "$error_log" ]; then
        local error_count=$(wc -l < "$error_log" 2>/dev/null || echo 0)
        local recent_errors=$(tail -n 24 "$error_log" 2>/dev/null | wc -l)
        
        if [ "$recent_errors" -gt "$ALERT_THRESHOLD_ERRORS" ]; then
            status_error "High error count in last 24 hours: $recent_errors"
            log_monitor "ALERT: High error count: $recent_errors"
            return 1
        elif [ "$recent_errors" -gt 0 ]; then
            status_warning "Recent errors: $recent_errors"
        else
            status_ok "No recent errors"
        fi
        
        echo "Total errors: $error_count"
    fi
    
    # Check success count
    if [ -f "$success_log" ]; then
        local success_count=$(grep "SUCCESS" "$success_log" 2>/dev/null | wc -l)
        status_info "Total successful imports: $success_count"
    fi
    
    return 0
}

# Check cron job status
check_cron_status() {
    echo -e "${PURPLE}Cron Job Status${NC}"
    echo "==============="
    
    # Check if cron is running
    if systemctl is-active --quiet cron 2>/dev/null || systemctl is-active --quiet crond 2>/dev/null; then
        status_ok "Cron service is running"
    else
        status_error "Cron service is not running"
        return 1
    fi
    
    # Check if our cron job is installed
    local cron_jobs=$(crontab -l 2>/dev/null | grep -c "daily_import.sh")
    if [ "$cron_jobs" -gt 0 ]; then
        status_ok "CheckjeBon cron job is installed ($cron_jobs entries)"
        echo ""
        echo "Cron schedule:"
        crontab -l 2>/dev/null | grep "daily_import.sh"
    else
        status_warning "CheckjeBon cron job not found"
    fi
    
    # Check cron logs
    local cron_log="$LOG_DIR/cron/daily_import_cron.log"
    if [ -f "$cron_log" ]; then
        local last_cron_run=$(tail -1 "$cron_log" 2>/dev/null)
        if [ -n "$last_cron_run" ]; then
            status_info "Last cron run: $last_cron_run"
        fi
    fi
    
    return 0
}

# Check Python environment
check_python_env() {
    echo -e "${PURPLE}Python Environment Check${NC}"
    echo "======================="
    
    local venv_dir="$PROJECT_DIR/venv"
    
    # Check if virtual environment exists
    if [ -d "$venv_dir" ]; then
        status_ok "Virtual environment exists: $venv_dir"
    else
        status_error "Virtual environment not found: $venv_dir"
        return 1
    fi
    
    # Test virtual environment
    if source "$venv_dir/bin/activate" 2>/dev/null; then
        status_ok "Virtual environment can be activated"
        
        # Check Python version
        local python_version=$(python --version 2>/dev/null)
        echo "Python version: $python_version"
        
        # Check installed packages
        local package_count=$(pip list 2>/dev/null | wc -l)
        echo "Installed packages: $package_count"
        
        # Check key dependencies
        local deps=("requests" "supabase" "python-dateutil")
        for dep in "${deps[@]}"; do
            if pip show "$dep" >/dev/null 2>&1; then
                status_ok "$dep is installed"
            else
                status_error "$dep is not installed"
            fi
        done
        
        deactivate 2>/dev/null
    else
        status_error "Cannot activate virtual environment"
        return 1
    fi
    
    return 0
}

# Check environment variables
check_environment() {
    echo -e "${PURPLE}Environment Variables Check${NC}"
    echo "=========================="
    
    local env_file="$PROJECT_DIR/.env"
    
    if [ -f "$env_file" ]; then
        status_ok "Environment file exists: $env_file"
        source "$env_file"
    else
        status_error "Environment file not found: $env_file"
        return 1
    fi
    
    # Check required variables
    local required_vars=("SUPABASE_URL" "SUPABASE_KEY")
    local missing_vars=0
    
    for var in "${required_vars[@]}"; do
        if [ -n "${!var}" ]; then
            status_ok "$var is set"
        else
            status_error "$var is not set"
            missing_vars=$((missing_vars + 1))
        fi
    done
    
    # Check optional variables
    local optional_vars=("EMAIL_ENABLED" "IMPORT_BATCH_SIZE" "LOG_LEVEL")
    for var in "${optional_vars[@]}"; do
        if [ -n "${!var}" ]; then
            status_info "$var = ${!var}"
        fi
    done
    
    if [ $missing_vars -gt 0 ]; then
        log_monitor "ALERT: Missing required environment variables: $missing_vars"
        return 1
    fi
    
    return 0
}

# Check database connectivity
check_database() {
    echo -e "${PURPLE}Database Connectivity Check${NC}"
    echo "=========================="
    
    # Test database connection using the import script
    if "$PROJECT_DIR/automation/daily_import.sh" --test >/dev/null 2>&1; then
        status_ok "Database connection successful"
    else
        status_error "Database connection failed"
        log_monitor "ALERT: Database connection failed"
        return 1
    fi
    
    return 0
}

# Check system resources
check_system_resources() {
    echo -e "${PURPLE}System Resources Check${NC}"
    echo "======================"
    
    # Memory usage
    local memory_info=$(free -m 2>/dev/null)
    if [ -n "$memory_info" ]; then
        local memory_usage=$(echo "$memory_info" | grep "Mem:" | awk '{printf "%.1f", ($3/$2)*100}')
        echo "Memory usage: ${memory_usage}%"
        
        if (( $(echo "$memory_usage > 90" | bc -l) )); then
            status_error "High memory usage: ${memory_usage}%"
        elif (( $(echo "$memory_usage > 80" | bc -l) )); then
            status_warning "High memory usage: ${memory_usage}%"
        else
            status_ok "Memory usage normal: ${memory_usage}%"
        fi
    fi
    
    # CPU load
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    if [ -n "$load_avg" ]; then
        echo "Load average: $load_avg"
        if (( $(echo "$load_avg > 5" | bc -l 2>/dev/null) )); then
            status_warning "High load average: $load_avg"
        else
            status_ok "Load average normal: $load_avg"
        fi
    fi
    
    # Process count
    local process_count=$(ps aux | wc -l)
    echo "Running processes: $process_count"
    
    return 0
}

# Generate monitoring report
generate_report() {
    local report_file="$LOG_DIR/monitoring_report_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "Generating monitoring report..."
    
    {
        echo "CheckjeBon System Monitoring Report"
        echo "==================================="
        echo "Generated: $(date)"
        echo "Host: $(hostname)"
        echo ""
        
        # Run all checks and capture output
        show_system_info
        check_disk_usage
        check_log_sizes
        check_import_status
        check_cron_status
        check_python_env
        check_environment
        check_database
        check_system_resources
        
    } > "$report_file" 2>&1
    
    echo "Report saved to: $report_file"
    return 0
}

# Send alert if issues found
send_alert() {
    local alert_message="$1"
    local alert_level="$2"
    
    log_monitor "ALERT [$alert_level]: $alert_message"
    
    # Send email if configured
    if [ "$EMAIL_ENABLED" = "true" ] && [ -n "$EMAIL_TO" ]; then
        python3 "$PROJECT_DIR/automation/email_notifications.py" failure \
            --to "$EMAIL_TO" \
            --exit-code 1 \
            --duration 0 \
            --error-details "$alert_message" \
            --log-file "$MONITORING_LOG"
    fi
}

# Main monitoring function
run_monitoring() {
    echo -e "${BLUE}CheckjeBon System Monitoring${NC}"
    echo "============================"
    echo "Started: $(date)"
    echo ""
    
    log_monitor "Starting system monitoring"
    
    local checks_failed=0
    local total_checks=0
    
    # Run all checks
    local checks=(
        "System Info:show_system_info"
        "Disk Usage:check_disk_usage"
        "Log Sizes:check_log_sizes"
        "Import Status:check_import_status"
        "Cron Status:check_cron_status"
        "Python Environment:check_python_env"
        "Environment Variables:check_environment"
        "Database Connectivity:check_database"
        "System Resources:check_system_resources"
    )
    
    for check in "${checks[@]}"; do
        local check_name=$(echo "$check" | cut -d: -f1)
        local check_function=$(echo "$check" | cut -d: -f2)
        
        echo ""
        if ! $check_function; then
            checks_failed=$((checks_failed + 1))
            log_monitor "CHECK FAILED: $check_name"
        else
            log_monitor "CHECK PASSED: $check_name"
        fi
        total_checks=$((total_checks + 1))
    done
    
    # Summary
    echo ""
    echo -e "${PURPLE}Monitoring Summary${NC}"
    echo "=================="
    echo "Total checks: $total_checks"
    echo "Passed: $((total_checks - checks_failed))"
    echo "Failed: $checks_failed"
    
    if [ $checks_failed -eq 0 ]; then
        status_ok "All checks passed"
        log_monitor "All monitoring checks passed"
    else
        status_error "$checks_failed checks failed"
        log_monitor "Monitoring completed with $checks_failed failures"
        send_alert "System monitoring found $checks_failed issues" "WARNING"
    fi
    
    echo ""
    echo "Completed: $(date)"
    log_monitor "Monitoring completed"
    
    return $checks_failed
}

# Command line interface
main() {
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    case "${1:-}" in
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help, -h      Show this help message"
            echo "  --report        Generate monitoring report"
            echo "  --disk          Check disk usage only"
            echo "  --logs          Check log sizes only"
            echo "  --import        Check import status only"
            echo "  --cron          Check cron status only"
            echo "  --python        Check Python environment only"
            echo "  --env           Check environment variables only"
            echo "  --database      Check database connectivity only"
            echo "  --resources     Check system resources only"
            echo "  --daemon        Run in daemon mode"
            echo ""
            ;;
        --report)
            generate_report
            ;;
        --disk)
            check_disk_usage
            ;;
        --logs)
            check_log_sizes
            ;;
        --import)
            check_import_status
            ;;
        --cron)
            check_cron_status
            ;;
        --python)
            check_python_env
            ;;
        --env)
            check_environment
            ;;
        --database)
            check_database
            ;;
        --resources)
            check_system_resources
            ;;
        --daemon)
            echo "Starting monitoring daemon..."
            while true; do
                run_monitoring > /dev/null 2>&1
                sleep $HEALTH_CHECK_INTERVAL
            done
            ;;
        "")
            run_monitoring
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

# Load environment if available
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

main "$@"