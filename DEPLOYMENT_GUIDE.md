# Price History System Deployment Guide

Complete deployment guide for the Price History Tracking System with Docker, monitoring, backup, and CI/CD pipeline setup.

## 🚀 Quick Start

### Development Environment

```bash
# Clone repository
git clone https://github.com/yourorg/price-history-system.git
cd price-history-system

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Run tests
docker-compose -f docker-compose.dev.yml run test-runner
```

### Production Environment

```bash
# Setup production environment
cp .env.example .env.production
# Edit .env.production with production values

# Deploy to production
./scripts/deployment.sh production -t latest

# Verify deployment
./scripts/health-check.sh production
```

## 📋 Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 50GB minimum, 100GB recommended
- **Network**: Port 8000 (API), 3000 (Grafana), 9090 (Prometheus)

### External Dependencies

- **Supabase**: Database and authentication
- **Redis**: Caching (optional but recommended)
- **SMTP Server**: Email notifications
- **S3 Bucket**: Backup storage (optional)

### Required Tools

```bash
# Install required tools
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin curl jq bc

# Install AWS CLI (for S3 backups)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

## 🔧 Configuration

### Environment Variables

Create environment files for each environment:

#### `.env.production`
```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-production-service-key

# Cache
REDIS_URL=redis://redis:6379
CACHE_TTL=300

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=alerts@yourcompany.com
EMAIL_PASSWORD=your-app-password
ALERT_RECIPIENTS=admin@yourcompany.com,ops@yourcompany.com

# Backup
S3_BUCKET=your-backup-bucket
S3_ACCESS_KEY=your-s3-access-key
S3_SECRET_KEY=your-s3-secret-key
BACKUP_RETENTION_DAYS=30

# Monitoring
GRAFANA_PASSWORD=your-secure-password
```

#### `.env.staging`
```bash
# Staging configuration (similar to production but with staging values)
ENVIRONMENT=staging
SUPABASE_URL=https://your-staging-project.supabase.co
# ... other staging-specific values
```

### Docker Compose Configuration

The system uses different compose files for different environments:

- `docker-compose.yml` - Production
- `docker-compose.dev.yml` - Development
- `docker-compose.staging.yml` - Staging

### SSL/TLS Configuration

For production deployments, configure SSL certificates:

```bash
# Using Let's Encrypt with Nginx
sudo certbot --nginx -d api.yourcompany.com
```

## 🏗️ Deployment Architecture

### Services Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Load Balancer  │    │   API Gateway   │    │  Price History  │
│    (Nginx)      │───▶│    (Optional)   │───▶│      API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │   Supabase      │
                       │    (Cache)      │◀───│  (Database)     │
                       └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │    Grafana      │    │  Backup Service │
│  (Metrics)      │───▶│  (Dashboard)    │    │      (S3)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Network Configuration

```yaml
# docker-compose.yml network section
networks:
  price-history-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 📦 Deployment Methods

### Method 1: Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Monitor deployment
docker-compose logs -f price-history-api

# Check service status
docker-compose ps
```

### Method 2: Automated Script

```bash
# Deploy with automation script
./scripts/deployment.sh production -t v1.2.3

# Rollback if needed
./scripts/deployment.sh production --rollback
```

### Method 3: CI/CD Pipeline

The system includes GitHub Actions workflows for automated deployment:

```yaml
# Triggers:
# - Push to main branch → Production deployment
# - Push to develop branch → Staging deployment
# - Pull request → Testing and security scans
```

## 🗄️ Database Setup

### Supabase Schema

The system requires specific database tables. Run the schema creation:

```sql
-- Create tables (executed automatically during deployment)
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    brand TEXT,
    size_text TEXT,
    category_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Additional tables: supermarkets, categories, price_history, etc.
-- See database/schema.sql for complete schema
```

### Database Migrations

```bash
# Run migrations manually
./scripts/migrate.sh production

# Check migration status
./scripts/migrate.sh production --status
```

## 🔍 Monitoring Setup

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'price-history-api'
    static_configs:
      - targets: ['price-history-api:8000']
```

### Grafana Dashboard

1. **Access Grafana**: `http://localhost:3000`
2. **Default credentials**: admin/admin (change immediately)
3. **Import dashboard**: Upload `monitoring/grafana/dashboards/price_history_dashboard.json`

### Alert Configuration

```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourcompany.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
```

## 💾 Backup Configuration

### Automated Backups

```bash
# Setup backup cron job
crontab -e

# Add backup job (daily at 2 AM)
0 2 * * * /opt/price-history/scripts/backup.sh
```

### Manual Backup Operations

```bash
# Create manual backup
python3 -m backup.backup_manager backup --backup-id manual_$(date +%Y%m%d)

# List available backups
python3 -m backup.backup_manager list

# Restore from backup
python3 -m backup.backup_manager restore --backup-id backup_20241209_120000
```

### S3 Backup Configuration

```bash
# Configure AWS credentials
aws configure
# or use IAM roles for EC2 instances

# Test S3 connectivity
aws s3 ls s3://your-backup-bucket
```

## 🔐 Security Configuration

### SSL/TLS Setup

```bash
# Generate SSL certificate
sudo certbot --nginx -d api.yourcompany.com

# Setup auto-renewal
sudo crontab -e
0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 8000/tcp # API (if directly exposed)
sudo ufw enable
```

### Security Scanning

```bash
# Run security scan
docker run --rm -v $(pwd):/app -w /app \
  aquasec/trivy:latest fs --exit-code 1 .

# Container security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image price-history-api:latest
```

## 📊 Performance Optimization

### Resource Limits

```yaml
# docker-compose.yml
services:
  price-history-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(price_date);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
```

### Caching Strategy

```bash
# Redis configuration
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🔄 CI/CD Pipeline

### GitHub Actions Setup

1. **Configure secrets** in GitHub repository settings:
   ```
   SUPABASE_URL
   SUPABASE_KEY
   SUPABASE_TEST_URL
   SUPABASE_TEST_KEY
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   SLACK_WEBHOOK_URL
   ```

2. **Pipeline stages**:
   - **Test**: Unit tests, integration tests, security scans
   - **Build**: Docker image build and push
   - **Deploy**: Automated deployment to staging/production
   - **Verify**: Health checks and smoke tests

### Manual Pipeline Triggers

```bash
# Trigger deployment manually
gh workflow run ci-cd.yml --ref main

# Check workflow status
gh run list --workflow=ci-cd.yml
```

## 🆘 Disaster Recovery

### Backup Strategy

- **Daily backups** with 30-day retention
- **Weekly full backups** with 90-day retention
- **Monthly archives** with 1-year retention
- **Offsite storage** in S3 with cross-region replication

### Recovery Procedures

```bash
# Quick recovery from backup
python3 -m backup.backup_manager restore --backup-id latest

# Disaster recovery assessment
python3 -m backup.disaster_recovery assess --symptoms '{"database_unreachable": true}'

# Execute recovery plan
python3 -m backup.disaster_recovery recover --disaster-type database_failure
```

### RTO/RPO Targets

- **RTO (Recovery Time Objective)**: 30 minutes
- **RPO (Recovery Point Objective)**: 1 hour
- **Data Loss Tolerance**: Maximum 2 hours

## 🔧 Maintenance

### Regular Maintenance Tasks

```bash
# Weekly maintenance (automated)
0 1 * * 0 /opt/price-history/scripts/maintenance.sh

# Monthly tasks
- Update dependencies
- Review logs
- Clean up old data
- Performance analysis
```

### Log Management

```bash
# Setup log rotation
sudo nano /etc/logrotate.d/price-history

# Log rotation configuration
/opt/price-history/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 price-history price-history
}
```

### Health Monitoring

```bash
# Setup health check cron
*/5 * * * * /opt/price-history/scripts/health-check.sh production

# Monitor system resources
watch -n 1 'docker stats --no-stream'
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  price-history-api:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 30s
      restart_policy:
        condition: on-failure
```

### Load Balancing

```nginx
# nginx.conf
upstream price_history_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://price_history_api;
    }
}
```

### Database Scaling

```sql
-- Read replicas for reporting
CREATE SUBSCRIPTION price_history_replica
CONNECTION 'host=replica.db.com port=5432 user=replica'
PUBLICATION price_history_pub;
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs
docker-compose logs price-history-api

# Check configuration
docker-compose config

# Verify environment variables
docker-compose exec price-history-api env
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
docker-compose exec price-history-api python3 -c "
from supabase import create_client
client = create_client('$SUPABASE_URL', '$SUPABASE_KEY')
print('Database connected successfully')
"
```

#### 3. High Memory Usage
```bash
# Monitor memory usage
docker stats --no-stream

# Check for memory leaks
docker-compose exec price-history-api python3 -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

#### 4. Backup Failures
```bash
# Check backup logs
tail -f /opt/price-history/logs/backup.log

# Test backup manually
python3 -m backup.backup_manager backup --backup-id test_backup

# Verify backup integrity
python3 -m backup.backup_manager verify --backup-id test_backup
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services
docker-compose restart price-history-api
```

### Support Contacts

- **Technical Issues**: tech-support@yourcompany.com
- **Infrastructure**: ops@yourcompany.com
- **Security**: security@yourcompany.com

## 📚 Additional Resources

### Documentation Links

- [API Documentation](./API_README.md)
- [Monitoring Guide](./MONITORING_README.md)
- [Backup Strategy](./backup/README.md)
- [Development Guide](./DEVELOPMENT.md)

### External Resources

- [Docker Documentation](https://docs.docker.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

## 🔄 Version History

- **v1.0.0**: Initial deployment setup
- **v1.1.0**: Added monitoring and alerting
- **v1.2.0**: Enhanced backup and disaster recovery
- **v1.3.0**: CI/CD pipeline implementation

For questions or support, please contact the development team or create an issue in the project repository.