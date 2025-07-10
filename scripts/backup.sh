#!/bin/bash

# Automated Backup Script for Price History System
# ===============================================

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/price-history/backups"
LOG_FILE="/opt/price-history/logs/backup.log"
RETENTION_DAYS=30
S3_BUCKET="${S3_BUCKET:-}"
NOTIFICATION_EMAIL="${ALERT_RECIPIENTS:-}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    send_alert "Backup Failed" "$1"
    exit 1
}

# Send alert notification
send_alert() {
    local subject="$1"
    local message="$2"
    
    if [ -n "$NOTIFICATION_EMAIL" ]; then
        python3 -c "
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
email_from = os.getenv('EMAIL_FROM', '')
email_password = os.getenv('EMAIL_PASSWORD', '')

if email_from and email_password:
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = '$NOTIFICATION_EMAIL'
    msg['Subject'] = 'Price History Backup: $subject'
    
    body = '''
    Backup Alert: $subject
    
    $message
    
    Time: $(date)
    Host: $(hostname)
    '''
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_from, email_password)
        server.send_message(msg)
        server.quit()
        print('Alert sent successfully')
    except Exception as e:
        print(f'Failed to send alert: {e}')
"
    fi
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Start backup process
log "Starting backup process..."

# Set backup ID
BACKUP_ID="daily_$(date +%Y%m%d_%H%M%S)"

# Run Python backup
log "Running Python backup manager..."
cd /opt/price-history

if python3 -m backup.backup_manager backup --backup-id "$BACKUP_ID"; then
    log "Python backup completed successfully"
else
    error_exit "Python backup failed"
fi

# Get backup file path
BACKUP_FILE="$BACKUP_DIR/${BACKUP_ID}.json.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "Backup file not found: $BACKUP_FILE"
fi

# Get backup size
BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
log "Backup size: $BACKUP_SIZE"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    log "Uploading backup to S3..."
    
    if aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/price-history-backups/${BACKUP_ID}.json.gz" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256; then
        log "S3 upload completed successfully"
    else
        log "WARNING: S3 upload failed"
    fi
fi

# Verify backup integrity
log "Verifying backup integrity..."
if python3 -m backup.backup_manager verify --backup-id "$BACKUP_ID"; then
    log "Backup verification passed"
else
    error_exit "Backup verification failed"
fi

# Cleanup old backups
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.json.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*_metadata.json" -mtime +$RETENTION_DAYS -delete

# Cleanup old S3 backups
if [ -n "$S3_BUCKET" ]; then
    log "Cleaning up old S3 backups..."
    
    CUTOFF_DATE=$(date -d "-$RETENTION_DAYS days" +%Y-%m-%d)
    
    aws s3 ls "s3://$S3_BUCKET/price-history-backups/" | while read -r line; do
        DATE=$(echo "$line" | awk '{print $1}')
        FILE=$(echo "$line" | awk '{print $4}')
        
        if [[ "$DATE" < "$CUTOFF_DATE" ]]; then
            log "Deleting old S3 backup: $FILE"
            aws s3 rm "s3://$S3_BUCKET/price-history-backups/$FILE"
        fi
    done
fi

# Generate backup report
log "Generating backup report..."
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "*.json.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

REPORT="
Backup Report - $(date)
====================

Backup ID: $BACKUP_ID
Backup Size: $BACKUP_SIZE
Total Backups: $TOTAL_BACKUPS
Total Storage: $TOTAL_SIZE
S3 Upload: $([ -n "$S3_BUCKET" ] && echo "Yes" || echo "No")
Retention: $RETENTION_DAYS days

Backup Location: $BACKUP_FILE
Log File: $LOG_FILE

Status: SUCCESS
"

log "Backup completed successfully"
log "$REPORT"

# Send success notification if configured
if [ "${SEND_SUCCESS_NOTIFICATIONS:-false}" = "true" ]; then
    send_alert "Backup Completed Successfully" "$REPORT"
fi

exit 0