#!/bin/bash

# Health Check Script for Price History System
# ============================================

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-production}"
TIMEOUT=60
MAX_ATTEMPTS=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Get base URL based on environment
get_base_url() {
    case "$ENVIRONMENT" in
        staging)
            echo "https://staging.yourapp.com"
            ;;
        production)
            echo "https://api.yourapp.com"
            ;;
        local)
            echo "http://localhost:8000"
            ;;
        *)
            error "Unknown environment: $ENVIRONMENT"
            ;;
    esac
}

# Check API health endpoint
check_api_health() {
    local base_url="$1"
    local endpoint="$base_url/health"
    
    log "Checking API health: $endpoint"
    
    local response
    if response=$(curl -s -f "$endpoint" --max-time "$TIMEOUT" 2>/dev/null); then
        if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
            success "API health check passed"
            return 0
        else
            error "API health check failed: Invalid response"
        fi
    else
        error "API health check failed: Connection error"
    fi
}

# Check database connectivity
check_database() {
    local base_url="$1"
    local endpoint="$base_url/health"
    
    log "Checking database connectivity..."
    
    local response
    if response=$(curl -s -f "$endpoint" --max-time "$TIMEOUT" 2>/dev/null); then
        local db_status
        if db_status=$(echo "$response" | jq -r '.data.database' 2>/dev/null); then
            if [[ "$db_status" == "connected" ]]; then
                success "Database connectivity check passed"
                return 0
            else
                error "Database connectivity check failed: $db_status"
            fi
        else
            error "Database connectivity check failed: Unable to parse response"
        fi
    else
        error "Database connectivity check failed: Connection error"
    fi
}

# Check cache connectivity
check_cache() {
    local base_url="$1"
    local endpoint="$base_url/health"
    
    log "Checking cache connectivity..."
    
    local response
    if response=$(curl -s -f "$endpoint" --max-time "$TIMEOUT" 2>/dev/null); then
        local cache_status
        if cache_status=$(echo "$response" | jq -r '.data.cache' 2>/dev/null); then
            if [[ "$cache_status" == "connected" ]]; then
                success "Cache connectivity check passed"
                return 0
            else
                warn "Cache connectivity check failed: $cache_status"
                return 1
            fi
        else
            warn "Cache connectivity check failed: Unable to parse response"
            return 1
        fi
    else
        warn "Cache connectivity check failed: Connection error"
        return 1
    fi
}

# Check critical API endpoints
check_critical_endpoints() {
    local base_url="$1"
    local endpoints=(
        "/health"
        "/products/search?q=test&limit=1"
        "/analytics/price-trends?days=7"
    )
    
    log "Checking critical API endpoints..."
    
    for endpoint in "${endpoints[@]}"; do
        local url="$base_url$endpoint"
        log "Testing endpoint: $endpoint"
        
        local response_code
        if response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time "$TIMEOUT" 2>/dev/null); then
            if [[ "$response_code" == "200" ]]; then
                success "Endpoint $endpoint: OK"
            else
                error "Endpoint $endpoint: HTTP $response_code"
            fi
        else
            error "Endpoint $endpoint: Connection failed"
        fi
    done
}

# Check response times
check_response_times() {
    local base_url="$1"
    local endpoint="$base_url/health"
    
    log "Checking response times..."
    
    local response_time
    if response_time=$(curl -s -o /dev/null -w "%{time_total}" "$endpoint" --max-time "$TIMEOUT" 2>/dev/null); then
        local response_ms
        response_ms=$(echo "$response_time * 1000" | bc)
        
        if (( $(echo "$response_time < 1.0" | bc -l) )); then
            success "Response time: ${response_ms}ms (excellent)"
        elif (( $(echo "$response_time < 3.0" | bc -l) )); then
            success "Response time: ${response_ms}ms (good)"
        elif (( $(echo "$response_time < 5.0" | bc -l) )); then
            warn "Response time: ${response_ms}ms (acceptable)"
        else
            error "Response time: ${response_ms}ms (too slow)"
        fi
    else
        error "Response time check failed"
    fi
}

# Check service availability with retries
check_service_availability() {
    local base_url="$1"
    local attempt=1
    
    log "Checking service availability with retries..."
    
    while [[ $attempt -le $MAX_ATTEMPTS ]]; do
        log "Attempt $attempt/$MAX_ATTEMPTS..."
        
        if curl -s -f "$base_url/health" --max-time "$TIMEOUT" > /dev/null 2>&1; then
            success "Service is available"
            return 0
        fi
        
        if [[ $attempt -lt $MAX_ATTEMPTS ]]; then
            log "Service not available, retrying in 5 seconds..."
            sleep 5
        fi
        
        ((attempt++))
    done
    
    error "Service is not available after $MAX_ATTEMPTS attempts"
}

# Check data freshness
check_data_freshness() {
    local base_url="$1"
    
    log "Checking data freshness..."
    
    # This would typically query a specific endpoint that returns data age
    # For now, we'll use a mock check
    local response
    if response=$(curl -s -f "$base_url/analytics/price-trends?days=1" --max-time "$TIMEOUT" 2>/dev/null); then
        if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
            success "Data freshness check passed"
            return 0
        else
            warn "Data freshness check failed: No recent data"
            return 1
        fi
    else
        warn "Data freshness check failed: Connection error"
        return 1
    fi
}

# Check monitoring endpoints
check_monitoring() {
    local base_url="$1"
    
    log "Checking monitoring endpoints..."
    
    # Check metrics endpoint
    local metrics_url="$base_url/metrics"
    if curl -s -f "$metrics_url" --max-time "$TIMEOUT" > /dev/null 2>&1; then
        success "Metrics endpoint is accessible"
    else
        warn "Metrics endpoint is not accessible"
    fi
    
    # Check if Prometheus is scraping
    if command -v prometheus > /dev/null 2>&1; then
        log "Prometheus is available"
    else
        warn "Prometheus is not available"
    fi
}

# Check load balancer health
check_load_balancer() {
    local base_url="$1"
    
    log "Checking load balancer health..."
    
    # Check if we can reach the service through load balancer
    local response_code
    if response_code=$(curl -s -o /dev/null -w "%{http_code}" "$base_url/health" --max-time "$TIMEOUT" 2>/dev/null); then
        if [[ "$response_code" == "200" ]]; then
            success "Load balancer health check passed"
            return 0
        else
            error "Load balancer health check failed: HTTP $response_code"
        fi
    else
        error "Load balancer health check failed: Connection error"
    fi
}

# Check SSL certificate
check_ssl() {
    local base_url="$1"
    
    if [[ "$base_url" == https://* ]]; then
        log "Checking SSL certificate..."
        
        local domain
        domain=$(echo "$base_url" | sed 's|https://||' | sed 's|/.*||')
        
        local expiry_date
        if expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2); then
            local expiry_epoch
            expiry_epoch=$(date -d "$expiry_date" +%s)
            local current_epoch
            current_epoch=$(date +%s)
            local days_until_expiry
            days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [[ $days_until_expiry -gt 30 ]]; then
                success "SSL certificate is valid for $days_until_expiry days"
            elif [[ $days_until_expiry -gt 7 ]]; then
                warn "SSL certificate expires in $days_until_expiry days"
            else
                error "SSL certificate expires in $days_until_expiry days"
            fi
        else
            error "SSL certificate check failed"
        fi
    else
        log "Skipping SSL check for non-HTTPS URL"
    fi
}

# Generate health report
generate_health_report() {
    local base_url="$1"
    local report_file="/tmp/health_report_$(date +%Y%m%d_%H%M%S).json"
    
    log "Generating health report..."
    
    local health_data
    health_data=$(curl -s -f "$base_url/health" --max-time "$TIMEOUT" 2>/dev/null || echo '{}')
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$ENVIRONMENT",
    "base_url": "$base_url",
    "health_data": $health_data,
    "checks": {
        "api_health": "$(check_api_health "$base_url" && echo "pass" || echo "fail")",
        "database": "$(check_database "$base_url" && echo "pass" || echo "fail")",
        "cache": "$(check_cache "$base_url" && echo "pass" || echo "fail")"
    }
}
EOF
    
    success "Health report generated: $report_file"
}

# Main health check function
main() {
    log "Starting health check for $ENVIRONMENT environment..."
    
    local base_url
    base_url=$(get_base_url)
    
    log "Base URL: $base_url"
    
    # Required checks (must pass)
    check_service_availability "$base_url"
    check_api_health "$base_url"
    check_database "$base_url"
    check_critical_endpoints "$base_url"
    check_response_times "$base_url"
    
    # Optional checks (warnings only)
    check_cache "$base_url" || true
    check_data_freshness "$base_url" || true
    check_monitoring "$base_url" || true
    check_load_balancer "$base_url" || true
    check_ssl "$base_url" || true
    
    # Generate report
    generate_health_report "$base_url" || true
    
    success "Health check completed successfully for $ENVIRONMENT!"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    error "jq is required but not installed"
fi

# Check if bc is installed
if ! command -v bc &> /dev/null; then
    error "bc is required but not installed"
fi

# Run main function
main "$@"