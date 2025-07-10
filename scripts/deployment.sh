#!/bin/bash

# Deployment Script for Price History System
# ==========================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/deployment.log"

# Default values
ENVIRONMENT=""
IMAGE_TAG=""
ROLLBACK=false
DRY_RUN=false
FORCE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] ENVIRONMENT

Deploy the Price History System to specified environment.

ARGUMENTS:
    ENVIRONMENT     Target environment (staging|production)

OPTIONS:
    -t, --tag TAG       Docker image tag to deploy
    -r, --rollback      Rollback to previous version
    -d, --dry-run       Show what would be done without executing
    -f, --force         Force deployment without confirmation
    -h, --help          Show this help message

EXAMPLES:
    $0 staging -t v1.2.3
    $0 production --rollback
    $0 staging --dry-run -t latest

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -r|--rollback)
                ROLLBACK=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                ;;
            *)
                if [[ -z "$ENVIRONMENT" ]]; then
                    ENVIRONMENT="$1"
                else
                    error "Multiple environments specified"
                fi
                shift
                ;;
        esac
    done
    
    # Validate environment
    if [[ -z "$ENVIRONMENT" ]]; then
        error "Environment is required"
    fi
    
    if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
        error "Environment must be 'staging' or 'production'"
    fi
    
    # Validate image tag for non-rollback deployments
    if [[ "$ROLLBACK" == false && -z "$IMAGE_TAG" ]]; then
        error "Image tag is required for deployment (use --tag)"
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running"
    fi
    
    # Check if required files exist
    local compose_file="docker-compose.${ENVIRONMENT}.yml"
    if [[ ! -f "$compose_file" ]]; then
        error "Compose file not found: $compose_file"
    fi
    
    # Check if environment file exists
    local env_file=".env.${ENVIRONMENT}"
    if [[ ! -f "$env_file" ]]; then
        error "Environment file not found: $env_file"
    fi
    
    # Check if required environment variables are set
    local required_vars=("SUPABASE_URL" "SUPABASE_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable not set: $var"
        fi
    done
    
    # Check database connectivity
    log "Checking database connectivity..."
    if ! python3 -c "
import os
from supabase import create_client
try:
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    client.table('products').select('id').limit(1).execute()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
        error "Database connectivity check failed"
    fi
    
    success "Pre-deployment checks passed"
}

# Database migration
run_migrations() {
    log "Running database migrations..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would run database migrations"
        return
    fi
    
    # Run migrations script
    if [[ -f "$SCRIPT_DIR/migrate.sh" ]]; then
        "$SCRIPT_DIR/migrate.sh" "$ENVIRONMENT"
    else
        warn "Migration script not found, skipping migrations"
    fi
    
    success "Database migrations completed"
}

# Backup current state
backup_current_state() {
    log "Creating backup of current state..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would create backup"
        return
    fi
    
    # Create backup
    local backup_id="pre_deploy_$(date +%Y%m%d_%H%M%S)"
    
    if python3 -m backup.backup_manager backup --backup-id "$backup_id"; then
        success "Backup created: $backup_id"
        echo "$backup_id" > /tmp/last_backup_id
    else
        error "Failed to create backup"
    fi
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    local compose_file="docker-compose.${ENVIRONMENT}.yml"
    
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would deploy with compose file: $compose_file"
        log "[DRY RUN] Would use image tag: $IMAGE_TAG"
        return
    fi
    
    # Update image tag in compose file
    if [[ -n "$IMAGE_TAG" ]]; then
        sed -i "s|image: .*price-history.*|image: ghcr.io/yourorg/price-history:$IMAGE_TAG|g" "$compose_file"
    fi
    
    # Deploy using Docker Compose
    export COMPOSE_FILE="$compose_file"
    export ENVIRONMENT
    
    log "Pulling latest images..."
    docker-compose -f "$compose_file" pull
    
    log "Starting services..."
    docker-compose -f "$compose_file" up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    if ! health_check; then
        error "Health check failed after deployment"
    fi
    
    success "Application deployed successfully"
}

# Health check
health_check() {
    log "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "http://localhost:8000/health" > /dev/null; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would rollback deployment"
        return
    fi
    
    # Get previous image tag
    local previous_tag
    if [[ -f "/tmp/previous_image_tag" ]]; then
        previous_tag=$(cat /tmp/previous_image_tag)
        log "Rolling back to previous image: $previous_tag"
    else
        warn "No previous image tag found, using latest backup"
        
        # Restore from backup
        if [[ -f "/tmp/last_backup_id" ]]; then
            local backup_id=$(cat /tmp/last_backup_id)
            log "Restoring from backup: $backup_id"
            
            python3 -m backup.backup_manager restore --backup-id "$backup_id"
        else
            error "No backup found for rollback"
        fi
        return
    fi
    
    # Deploy previous version
    IMAGE_TAG="$previous_tag"
    deploy_application
    
    success "Rollback completed"
}

# Post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would run post-deployment tasks"
        return
    fi
    
    # Update monitoring dashboards
    if [[ -f "$SCRIPT_DIR/update-dashboards.sh" ]]; then
        "$SCRIPT_DIR/update-dashboards.sh" "$ENVIRONMENT"
    fi
    
    # Send notification
    send_notification "success" "Deployment completed successfully"
    
    success "Post-deployment tasks completed"
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
        log "No Slack webhook URL configured, skipping notification"
        return
    fi
    
    local color="good"
    local icon=":white_check_mark:"
    
    if [[ "$status" == "error" ]]; then
        color="danger"
        icon=":x:"
    elif [[ "$status" == "warning" ]]; then
        color="warning"
        icon=":warning:"
    fi
    
    local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$icon Price History Deployment - $ENVIRONMENT",
            "text": "$message",
            "fields": [
                {
                    "title": "Environment",
                    "value": "$ENVIRONMENT",
                    "short": true
                },
                {
                    "title": "Image Tag",
                    "value": "$IMAGE_TAG",
                    "short": true
                },
                {
                    "title": "Deployed By",
                    "value": "${USER:-unknown}",
                    "short": true
                },
                {
                    "title": "Timestamp",
                    "value": "$(date)",
                    "short": true
                }
            ]
        }
    ]
}
EOF
)
    
    curl -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$SLACK_WEBHOOK_URL" || true
}

# Cleanup
cleanup() {
    log "Cleaning up..."
    
    # Remove temporary files
    rm -f /tmp/previous_image_tag
    rm -f /tmp/last_backup_id
    
    # Cleanup old Docker images
    docker system prune -f || true
    
    success "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting deployment to $ENVIRONMENT..."
    
    # Confirmation prompt
    if [[ "$FORCE" == false && "$DRY_RUN" == false ]]; then
        echo -n "Are you sure you want to deploy to $ENVIRONMENT? (y/N): "
        read -r confirmation
        if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
            log "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Store current image tag for rollback
    if [[ "$ROLLBACK" == false ]]; then
        docker-compose -f "docker-compose.${ENVIRONMENT}.yml" images | grep price-history | awk '{print $3}' > /tmp/previous_image_tag 2>/dev/null || true
    fi
    
    # Execute deployment steps
    if [[ "$ROLLBACK" == true ]]; then
        rollback_deployment
    else
        pre_deployment_checks
        backup_current_state
        run_migrations
        deploy_application
        post_deployment_tasks
    fi
    
    cleanup
    
    success "Deployment to $ENVIRONMENT completed successfully!"
}

# Error handling
trap 'error "Deployment failed at line $LINENO"' ERR

# Main execution
cd "$PROJECT_DIR"
parse_args "$@"
main