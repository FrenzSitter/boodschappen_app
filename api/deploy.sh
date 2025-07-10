#!/bin/bash

# CheckjeBon API Deployment Script
# ================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="checkjebon-api"
DOCKER_IMAGE="checkjebon-api:latest"

# Utility functions
log_info() {
    echo -e "${BLUE}INFO${NC}: $1"
}

log_success() {
    echo -e "${GREEN}SUCCESS${NC}: $1"
}

log_warning() {
    echo -e "${YELLOW}WARNING${NC}: $1"
}

log_error() {
    echo -e "${RED}ERROR${NC}: $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Check environment variables
check_environment() {
    log_info "Checking environment variables..."
    
    if [ -z "$SUPABASE_URL" ]; then
        log_error "SUPABASE_URL environment variable is not set"
        exit 1
    fi
    
    if [ -z "$SUPABASE_KEY" ]; then
        log_error "SUPABASE_KEY environment variable is not set"
        exit 1
    fi
    
    log_success "Environment variables check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    cd "$SCRIPT_DIR"
    
    # Build image
    docker build -t "$DOCKER_IMAGE" .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Docker image build failed"
        exit 1
    fi
}

# Deploy with Docker Compose
deploy_compose() {
    log_info "Deploying with Docker Compose..."
    
    cd "$SCRIPT_DIR"
    
    # Stop existing containers
    docker-compose down
    
    # Start new containers
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log_success "Docker Compose deployment successful"
    else
        log_error "Docker Compose deployment failed"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Wait for container to start
    sleep 10
    
    # Check API health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API health check passed"
            return 0
        fi
        
        log_info "Waiting for API to start... ($i/30)"
        sleep 2
    done
    
    log_error "API health check failed"
    return 1
}

# Show logs
show_logs() {
    log_info "Showing container logs..."
    docker-compose logs --tail=50 -f
}

# Show status
show_status() {
    log_info "Container status:"
    docker-compose ps
    
    echo ""
    log_info "API endpoints:"
    echo "  • Health: http://localhost:8000/health"
    echo "  • Docs: http://localhost:8000/docs"
    echo "  • API: http://localhost:8000"
}

# Cleanup
cleanup() {
    log_info "Cleaning up..."
    
    # Remove stopped containers
    docker-compose down --remove-orphans
    
    # Remove unused images
    docker system prune -f
    
    log_success "Cleanup completed"
}

# Main function
main() {
    echo -e "${BLUE}CheckjeBon API Deployment${NC}"
    echo "=========================="
    
    case "${1:-}" in
        build)
            check_dependencies
            build_image
            ;;
        deploy)
            check_dependencies
            check_environment
            build_image
            deploy_compose
            health_check
            show_status
            ;;
        up)
            check_dependencies
            check_environment
            deploy_compose
            health_check
            show_status
            ;;
        down)
            docker-compose down
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        health)
            health_check
            ;;
        cleanup)
            cleanup
            ;;
        *)
            echo "Usage: $0 {build|deploy|up|down|logs|status|health|cleanup}"
            echo ""
            echo "Commands:"
            echo "  build   - Build Docker image"
            echo "  deploy  - Full deployment (build + up + health check)"
            echo "  up      - Start containers"
            echo "  down    - Stop containers"
            echo "  logs    - Show container logs"
            echo "  status  - Show container status"
            echo "  health  - Check API health"
            echo "  cleanup - Clean up containers and images"
            echo ""
            echo "Environment variables required:"
            echo "  SUPABASE_URL - Your Supabase project URL"
            echo "  SUPABASE_KEY - Your Supabase API key"
            echo ""
            exit 1
            ;;
    esac
}

main "$@"