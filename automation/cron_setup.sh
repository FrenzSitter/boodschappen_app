#!/bin/bash

# Cron Job Setup Script for CheckjeBon Import
# ===========================================
# This script sets up automated cron jobs for daily CheckjeBon imports

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_IMPORT_SCRIPT="$SCRIPT_DIR/daily_import.sh"
CRON_LOG_DIR="$PROJECT_DIR/logs/cron"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
log_info() {
    echo -e "${BLUE}INFO${NC}: $1"
}

log_success() {
    echo -e "${GREEN}SUCCESS${NC}: $1"
}

log_error() {
    echo -e "${RED}ERROR${NC}: $1"
}

log_warning() {
    echo -e "${YELLOW}WARNING${NC}: $1"
}

# Check if script exists
check_script() {
    if [ ! -f "$DAILY_IMPORT_SCRIPT" ]; then
        log_error "Daily import script not found: $DAILY_IMPORT_SCRIPT"
        exit 1
    fi
    
    if [ ! -x "$DAILY_IMPORT_SCRIPT" ]; then
        log_error "Daily import script is not executable: $DAILY_IMPORT_SCRIPT"
        exit 1
    fi
    
    log_info "Daily import script found and executable"
}

# Create cron log directory
setup_cron_logs() {
    mkdir -p "$CRON_LOG_DIR"
    chmod 755 "$CRON_LOG_DIR"
    log_info "Created cron log directory: $CRON_LOG_DIR"
}

# Generate cron job entries
generate_cron_entries() {
    local user=$(whoami)
    local cron_file="$SCRIPT_DIR/checkjebon_cron.conf"
    
    cat > "$cron_file" << EOF
# CheckjeBon Import Automation
# ============================
# Automated cron jobs for CheckjeBon data import
# Generated on: $(date)
# User: $user

# Set PATH to include standard locations
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# Daily import at 3:00 AM
0 3 * * * $DAILY_IMPORT_SCRIPT >> $CRON_LOG_DIR/daily_import_cron.log 2>&1

# Weekly health check on Sundays at 2:00 AM
0 2 * * 0 $DAILY_IMPORT_SCRIPT --health >> $CRON_LOG_DIR/health_check_cron.log 2>&1

# Monthly log cleanup on the 1st at 1:00 AM
0 1 1 * * find $PROJECT_DIR/logs -name "*.log" -mtime +30 -delete >> $CRON_LOG_DIR/cleanup_cron.log 2>&1

# Quarterly connectivity test on the 1st of every quarter at 1:30 AM
30 1 1 */3 * $DAILY_IMPORT_SCRIPT --test >> $CRON_LOG_DIR/connectivity_test_cron.log 2>&1

EOF
    
    log_info "Generated cron configuration: $cron_file"
    echo "Contents:"
    cat "$cron_file"
}

# Install cron job
install_cron() {
    local cron_file="$SCRIPT_DIR/checkjebon_cron.conf"
    
    log_info "Installing cron job..."
    
    # Backup existing crontab
    crontab -l > "$SCRIPT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Create new crontab with our entries
    (
        # Keep existing crontab entries (excluding our entries)
        crontab -l 2>/dev/null | grep -v "CheckjeBon\|daily_import.sh" || true
        
        # Add our entries
        cat "$cron_file"
    ) | crontab -
    
    if [ $? -eq 0 ]; then
        log_success "Cron job installed successfully"
    else
        log_error "Failed to install cron job"
        exit 1
    fi
}

# Remove cron job
remove_cron() {
    log_info "Removing CheckjeBon cron jobs..."
    
    # Backup existing crontab
    crontab -l > "$SCRIPT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Remove our entries
    crontab -l 2>/dev/null | grep -v "CheckjeBon\|daily_import.sh" | crontab -
    
    if [ $? -eq 0 ]; then
        log_success "CheckjeBon cron jobs removed successfully"
    else
        log_error "Failed to remove cron jobs"
        exit 1
    fi
}

# Show current cron jobs
show_cron() {
    log_info "Current cron jobs:"
    crontab -l 2>/dev/null || echo "No cron jobs found"
}

# Test cron job
test_cron() {
    log_info "Testing daily import script..."
    
    # Run with dry-run and test flags
    "$DAILY_IMPORT_SCRIPT" --dry-run --test
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Test completed successfully"
    else
        log_error "Test failed with exit code: $exit_code"
        exit 1
    fi
}

# Create systemd timer (alternative to cron)
create_systemd_timer() {
    local service_file="$SCRIPT_DIR/checkjebon-import.service"
    local timer_file="$SCRIPT_DIR/checkjebon-import.timer"
    
    # Create service file
    cat > "$service_file" << EOF
[Unit]
Description=CheckjeBon Data Import
After=network.target

[Service]
Type=oneshot
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
ExecStart=$DAILY_IMPORT_SCRIPT
StandardOutput=append:$CRON_LOG_DIR/systemd_import.log
StandardError=append:$CRON_LOG_DIR/systemd_import.log

[Install]
WantedBy=multi-user.target
EOF

    # Create timer file
    cat > "$timer_file" << EOF
[Unit]
Description=Run CheckjeBon Import Daily
Requires=checkjebon-import.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    log_info "Created systemd service and timer files:"
    log_info "  Service: $service_file"
    log_info "  Timer: $timer_file"
    
    echo ""
    echo "To install systemd timer (requires sudo):"
    echo "  sudo cp $service_file /etc/systemd/system/"
    echo "  sudo cp $timer_file /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable checkjebon-import.timer"
    echo "  sudo systemctl start checkjebon-import.timer"
}

# Create monitoring script
create_monitoring_script() {
    local monitor_script="$SCRIPT_DIR/monitor_imports.sh"
    
    cat > "$monitor_script" << 'EOF'
#!/bin/bash

# CheckjeBon Import Monitoring Script
# ===================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}CheckjeBon Import Monitoring${NC}"
echo "============================="

# Check last import status
if [ -f "$LOG_DIR/daily_import.log" ]; then
    echo ""
    echo -e "${BLUE}Last Import Status:${NC}"
    tail -n 20 "$LOG_DIR/daily_import.log" | grep -E "(SUCCESS|ERROR|Starting daily)"
    
    echo ""
    echo -e "${BLUE}Recent Import Statistics:${NC}"
    grep -A 10 "IMPORT SUMMARY" "$LOG_DIR/daily_import.log" | tail -n 15
fi

# Check error log
if [ -f "$LOG_DIR/import_errors.log" ]; then
    local error_count=$(wc -l < "$LOG_DIR/import_errors.log")
    if [ $error_count -gt 0 ]; then
        echo ""
        echo -e "${RED}Recent Errors (last 5):${NC}"
        tail -n 5 "$LOG_DIR/import_errors.log"
    else
        echo ""
        echo -e "${GREEN}No recent errors${NC}"
    fi
fi

# Check cron log
if [ -f "$LOG_DIR/cron/daily_import_cron.log" ]; then
    echo ""
    echo -e "${BLUE}Cron Job Status:${NC}"
    tail -n 10 "$LOG_DIR/cron/daily_import_cron.log"
fi

# Check disk usage
echo ""
echo -e "${BLUE}Disk Usage:${NC}"
df -h "$PROJECT_DIR"

# Check log file sizes
echo ""
echo -e "${BLUE}Log File Sizes:${NC}"
du -sh "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found"

# Check next cron run
echo ""
echo -e "${BLUE}Next Scheduled Run:${NC}"
if command -v crontab >/dev/null 2>&1; then
    crontab -l 2>/dev/null | grep daily_import.sh | head -1
else
    echo "Cron not available"
fi

echo ""
echo -e "${GREEN}Monitoring complete${NC}"
EOF
    
    chmod +x "$monitor_script"
    log_info "Created monitoring script: $monitor_script"
}

# Main function
main() {
    echo -e "${BLUE}CheckjeBon Cron Setup${NC}"
    echo "====================="
    
    case "${1:-}" in
        install)
            check_script
            setup_cron_logs
            generate_cron_entries
            install_cron
            create_monitoring_script
            log_success "Cron setup completed successfully"
            ;;
        remove)
            remove_cron
            ;;
        show)
            show_cron
            ;;
        test)
            test_cron
            ;;
        systemd)
            create_systemd_timer
            ;;
        monitor)
            create_monitoring_script
            "$SCRIPT_DIR/monitor_imports.sh"
            ;;
        *)
            echo "Usage: $0 {install|remove|show|test|systemd|monitor}"
            echo ""
            echo "Commands:"
            echo "  install  - Install cron jobs for daily imports"
            echo "  remove   - Remove CheckjeBon cron jobs"
            echo "  show     - Show current cron jobs"
            echo "  test     - Test the daily import script"
            echo "  systemd  - Create systemd timer files"
            echo "  monitor  - Create and run monitoring script"
            echo ""
            exit 1
            ;;
    esac
}

main "$@"