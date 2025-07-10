# Troubleshooting Guide

Comprehensive troubleshooting guide for the Price History System covering common issues, debugging procedures, and resolution steps.

## 🚨 Quick Diagnosis

### System Health Check
```bash
# Run comprehensive health check
./scripts/health-check.sh production

# Check all services status
docker-compose ps

# Check resource usage
docker stats --no-stream
```

### Common Issues Quick Fix
```bash
# Service won't start
docker-compose restart price-history-api

# Database connection issues
docker-compose exec price-history-api python3 -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Database OK')
"

# Clear cache
docker-compose exec redis redis-cli FLUSHALL
```

## 🔍 Diagnostic Tools

### Log Analysis
```bash
# Application logs
docker-compose logs price-history-api | tail -100

# Error logs only
docker-compose logs price-history-api | grep -i error

# Real-time monitoring
docker-compose logs -f price-history-api

# System logs
journalctl -u price-history-api -f
```

### Performance Monitoring
```bash
# Resource usage
htop
free -h
df -h

# Database performance
docker-compose exec price-history-api python3 -c "
import time
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
start = time.time()
result = client.table('products').select('id').limit(1).execute()
print(f'Query time: {time.time() - start:.3f}s')
"
```

### Network Diagnostics
```bash
# Port availability
netstat -tuln | grep :8000

# Connection testing
curl -v http://localhost:8000/health

# DNS resolution
nslookup your-domain.com
```

## 🚫 Common Issues and Solutions

### 1. Service Won't Start

#### Symptoms
- Container exits immediately
- Service shows as unhealthy
- Port binding failures

#### Diagnosis
```bash
# Check container logs
docker-compose logs price-history-api

# Check port conflicts
sudo lsof -i :8000

# Verify configuration
docker-compose config

# Check environment variables
docker-compose exec price-history-api env
```

#### Solutions
```bash
# Kill conflicting process
sudo kill -9 $(sudo lsof -t -i:8000)

# Fix configuration
docker-compose down
docker-compose up -d

# Check file permissions
sudo chown -R $(id -u):$(id -g) /opt/price-history
```

### 2. Database Connection Issues

#### Symptoms
- "Connection refused" errors
- Timeout errors
- Authentication failures

#### Diagnosis
```bash
# Test database connectivity
docker-compose exec price-history-api python3 -c "
from supabase import create_client
import os
try:
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    result = client.table('products').select('id').limit(1).execute()
    print('Database connection successful')
except Exception as e:
    print(f'Database error: {e}')
"

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

#### Solutions
```bash
# Verify credentials
# Check Supabase dashboard for correct URL and key

# Test network connectivity
curl -v $SUPABASE_URL/rest/v1/

# Restart service
docker-compose restart price-history-api
```

### 3. High Memory Usage

#### Symptoms
- Out of memory errors
- Slow performance
- Service crashes

#### Diagnosis
```bash
# Check memory usage
docker stats --no-stream
free -h
cat /proc/meminfo

# Check for memory leaks
docker-compose exec price-history-api python3 -c "
import psutil
import gc
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'Objects in memory: {len(gc.get_objects())}')
"
```

#### Solutions
```bash
# Increase memory limits
# Edit docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Clear cache
docker-compose exec redis redis-cli FLUSHALL

# Restart service
docker-compose restart price-history-api
```

### 4. Backup Failures

#### Symptoms
- Backup jobs fail
- Missing backup files
- Corrupted backups

#### Diagnosis
```bash
# Check backup logs
tail -f /opt/price-history/logs/backup.log

# Test backup manually
python3 -m backup.backup_manager backup --backup-id test_backup

# Check backup integrity
python3 -m backup.backup_manager verify --backup-id test_backup

# Check S3 connectivity
aws s3 ls s3://your-backup-bucket/
```

#### Solutions
```bash
# Fix permissions
sudo chown -R price-history:price-history /opt/price-history/backups

# Check disk space
df -h /opt/price-history/backups

# Test S3 credentials
aws s3 ls s3://your-backup-bucket/

# Restart backup service
docker-compose restart backup-service
```

### 5. Import Process Issues

#### Symptoms
- Import jobs fail
- Data not updating
- Partial imports

#### Diagnosis
```bash
# Check import logs
docker-compose logs price-history-import

# Check last import status
docker-compose exec price-history-api python3 -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
result = client.table('import_logs').select('*').order('created_at', desc=True).limit(1).execute()
print(result.data[0] if result.data else 'No import logs found')
"

# Test CheckjeBon API
curl -v https://api.checkjebon.nl/health
```

#### Solutions
```bash
# Restart import service
docker-compose restart price-history-import

# Run manual import
docker-compose exec price-history-import python3 -m import_checkjebon

# Check API credentials
# Verify CheckjeBon API key is valid
```

### 6. Monitoring Issues

#### Symptoms
- Grafana dashboards empty
- Prometheus not collecting metrics
- Alerts not firing

#### Diagnosis
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana datasource
curl -u admin:admin http://localhost:3000/api/datasources

# Test metrics endpoint
curl http://localhost:8000/metrics
```

#### Solutions
```bash
# Restart monitoring stack
docker-compose restart prometheus grafana

# Check configuration
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Verify network connectivity
docker-compose exec prometheus wget -O- http://price-history-api:8000/metrics
```

## 🔧 Performance Issues

### Slow API Response

#### Symptoms
- API responses > 5 seconds
- High CPU usage
- Memory leaks

#### Diagnosis
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Profile application
docker-compose exec price-history-api python3 -c "
import cProfile
import pstats
# Add profiling code here
"

# Check database queries
# Monitor slow queries in Supabase dashboard
```

#### Solutions
```bash
# Optimize database queries
# Add indexes where needed

# Increase cache TTL
# Edit .env file:
# CACHE_TTL=600

# Scale horizontally
# Edit docker-compose.yml:
# deploy:
#   replicas: 3
```

### Database Performance

#### Symptoms
- Slow queries
- Connection timeouts
- High database CPU

#### Diagnosis
```bash
# Check query performance
# Use Supabase dashboard to monitor slow queries

# Check connection pool
docker-compose exec price-history-api python3 -c "
import psycopg2
from psycopg2 import pool
# Check connection pool status
"
```

#### Solutions
```bash
# Optimize queries
# Add database indexes
# Use connection pooling
# Consider read replicas
```

## 🛠️ Debugging Procedures

### Enable Debug Mode

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart service
docker-compose restart price-history-api

# Monitor debug logs
docker-compose logs -f price-history-api
```

### Application Debugging

```bash
# Python debugging
docker-compose exec price-history-api python3 -c "
import pdb
import your_module
pdb.set_trace()
your_module.problematic_function()
"

# Interactive shell
docker-compose exec price-history-api python3 -i
```

### Database Debugging

```bash
# Direct database access
docker-compose exec price-history-api python3 -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
# Run diagnostic queries
"
```

## 📊 Monitoring and Alerting

### Check Alert Status

```bash
# Check Prometheus alerts
curl http://localhost:9090/api/v1/alerts

# Check Alertmanager
curl http://localhost:9093/api/v1/alerts

# Test email notifications
python3 -c "
import smtplib
from email.mime.text import MIMEText
# Test email configuration
"
```

### Custom Metrics

```bash
# Check custom metrics
curl http://localhost:8000/metrics | grep price_history

# Add custom metrics
# Edit metrics_exporter.py
```

## 🔄 Recovery Procedures

### Service Recovery

```bash
# Graceful restart
docker-compose restart price-history-api

# Force restart
docker-compose kill price-history-api
docker-compose up -d price-history-api

# Full system restart
docker-compose down
docker-compose up -d
```

### Data Recovery

```bash
# Restore from backup
python3 -m backup.backup_manager restore --backup-id backup_20241209_120000

# Partial restore
python3 -m backup.backup_manager restore --backup-id backup_20241209_120000 --tables products,price_history

# Database repair
# Use Supabase dashboard for database maintenance
```

### Disaster Recovery

```bash
# Full disaster recovery
python3 -m backup.disaster_recovery recover --disaster-type database_failure

# Manual recovery steps
# 1. Assess damage
# 2. Restore from backup
# 3. Verify data integrity
# 4. Restart services
# 5. Monitor system
```

## 📝 Incident Response

### Incident Classification

- **Critical**: System down, data loss
- **High**: Performance degradation, partial outage
- **Medium**: Non-critical features affected
- **Low**: Minor issues, cosmetic problems

### Response Procedures

```bash
# 1. Immediate response
./scripts/health-check.sh production
docker-compose logs price-history-api | tail -50

# 2. Assess impact
# Check monitoring dashboards
# Verify service functionality

# 3. Implement fix
# Apply quick fixes
# Monitor system response

# 4. Post-incident
# Document lessons learned
# Update procedures
```

## 📞 Escalation Procedures

### Level 1 Support
- Check logs and basic diagnostics
- Restart services if needed
- Apply known fixes

### Level 2 Support
- Deep debugging
- Database issues
- Configuration problems

### Level 3 Support
- Code changes required
- Infrastructure changes
- Vendor support needed

## 🔍 Log Analysis

### Log Locations
```bash
# Application logs
/opt/price-history/logs/application.log

# Import logs
/opt/price-history/logs/import.log

# Backup logs
/opt/price-history/logs/backup.log

# System logs
/var/log/syslog
journalctl -u price-history-api
```

### Log Analysis Tools
```bash
# Search for errors
grep -i error /opt/price-history/logs/application.log

# Filter by date
grep "2024-12-09" /opt/price-history/logs/application.log

# Count occurrences
grep -c "error" /opt/price-history/logs/application.log

# Real-time monitoring
tail -f /opt/price-history/logs/application.log | grep -i error
```

## 🎯 Prevention Measures

### Monitoring Setup
- Comprehensive health checks
- Proactive alerting
- Performance monitoring
- Log analysis

### Maintenance Tasks
- Regular backups
- System updates
- Performance tuning
- Security patches

### Documentation
- Keep troubleshooting guide updated
- Document all incidents
- Maintain runbooks
- Train team members

## 📋 Troubleshooting Checklist

### Before Escalating
- [ ] Checked service logs
- [ ] Verified configuration
- [ ] Tested basic functionality
- [ ] Checked system resources
- [ ] Reviewed recent changes

### During Incident
- [ ] Documented symptoms
- [ ] Collected diagnostic data
- [ ] Implemented temporary fixes
- [ ] Monitored system response
- [ ] Communicated with stakeholders

### After Resolution
- [ ] Documented solution
- [ ] Updated procedures
- [ ] Implemented preventive measures
- [ ] Conducted post-mortem
- [ ] Updated monitoring

---

For additional support, contact the development team or refer to the deployment guide for detailed configuration information.