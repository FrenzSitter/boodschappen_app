# CheckjeBon Automation System

This directory contains the complete automation system for daily CheckjeBon data imports with monitoring, logging, and notifications.

## 🚀 Quick Start

```bash
# 1. Set up environment
./setup_environment.sh setup

# 2. Test the system
./daily_import.sh --test

# 3. Install automation
./cron_setup.sh install

# 4. Monitor the system
./monitor_system.sh
```

## 📁 File Structure

```
automation/
├── daily_import.sh              # Main automation script
├── cron_setup.sh               # Cron job configuration
├── setup_environment.sh        # Environment setup
├── email_notifications.py      # Email notification system
├── monitor_system.sh           # System monitoring
├── checkjebon-import.service   # systemd service file
├── checkjebon-import.timer     # systemd timer file
├── INSTALLATION_GUIDE.md       # Platform-specific installation
└── README.md                   # This file
```

## 🛠️ Components

### 1. Daily Import Script (`daily_import.sh`)

The main automation script that:
- Manages Python virtual environment
- Handles locking to prevent concurrent runs
- Provides comprehensive logging
- Sends failure notifications
- Rotates log files
- Includes health checks

**Usage:**
```bash
./daily_import.sh              # Normal run
./daily_import.sh --dry-run     # Test without changes
./daily_import.sh --test        # Connectivity test only
./daily_import.sh --health      # Health check only
./daily_import.sh --force       # Ignore lock file
```

### 2. Cron Setup (`cron_setup.sh`)

Manages cron job installation and configuration:
- Installs daily import at 3:00 AM
- Sets up weekly health checks
- Configures log cleanup
- Creates monitoring scripts

**Usage:**
```bash
./cron_setup.sh install    # Install cron jobs
./cron_setup.sh remove     # Remove cron jobs
./cron_setup.sh show       # Show current jobs
./cron_setup.sh test       # Test the script
./cron_setup.sh systemd    # Create systemd files
./cron_setup.sh monitor    # Run monitoring
```

### 3. Environment Setup (`setup_environment.sh`)

Interactive environment configuration:
- Sets up Supabase credentials
- Configures email notifications
- Validates environment variables
- Tests database connectivity

**Usage:**
```bash
./setup_environment.sh setup      # Interactive setup
./setup_environment.sh validate   # Validate config
./setup_environment.sh test       # Test connection
./setup_environment.sh show       # Show config
./setup_environment.sh backup     # Backup config
```

### 4. Email Notifications (`email_notifications.py`)

Email notification system for:
- Import failures with error details
- Success notifications with statistics
- Test emails for configuration validation
- HTML and plain text formats

**Usage:**
```bash
python email_notifications.py test --to admin@example.com
python email_notifications.py failure --to admin@example.com --exit-code 1
python email_notifications.py success --to admin@example.com --duration 60
```

### 5. System Monitoring (`monitor_system.sh`)

Comprehensive system monitoring:
- Disk usage and log file sizes
- Import status and error tracking
- Cron job status verification
- Python environment validation
- Database connectivity testing
- System resource monitoring

**Usage:**
```bash
./monitor_system.sh           # Full monitoring
./monitor_system.sh --disk    # Disk usage only
./monitor_system.sh --import  # Import status only
./monitor_system.sh --report  # Generate report
./monitor_system.sh --daemon  # Run continuously
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Optional - Email Notifications
EMAIL_ENABLED=true
EMAIL_TO=admin@example.com
EMAIL_FROM=noreply@checkjebon.local
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# Optional - Import Settings
IMPORT_BATCH_SIZE=50
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

### Cron Schedule

Default cron schedule:
```cron
# Daily import at 3:00 AM
0 3 * * * /path/to/daily_import.sh

# Weekly health check on Sundays at 2:00 AM
0 2 * * 0 /path/to/daily_import.sh --health

# Monthly log cleanup on the 1st at 1:00 AM
0 1 1 * * find /path/to/logs -name "*.log" -mtime +30 -delete
```

## 📊 Monitoring and Logging

### Log Files

- `logs/daily_import.log` - Main import log
- `logs/import_errors.log` - Error-only log
- `logs/import_success.log` - Success-only log
- `logs/monitoring.log` - Monitoring log
- `logs/cron/` - Cron job logs

### Monitoring Features

- **Real-time status**: Current import status
- **Error tracking**: Error count and details
- **Performance metrics**: Import duration and rates
- **Resource monitoring**: Disk, memory, CPU usage
- **Alert system**: Email notifications for failures

### Health Checks

Automated health checks include:
- Database connectivity
- Python environment integrity
- Cron job status
- Log file sizes
- System resources
- Environment variables

## 🔒 Security

### Best Practices

1. **Environment Variables**: Never store credentials in code
2. **File Permissions**: Restrict access to logs and config files
3. **Network Security**: Use HTTPS for all connections
4. **Regular Updates**: Keep dependencies updated
5. **Monitoring**: Monitor for unusual activity

### File Permissions

```bash
# Set proper permissions
chmod 600 .env                    # Environment file
chmod 755 automation/*.sh         # Scripts
chmod 644 logs/*.log              # Log files
chmod 700 logs/                   # Log directory
```

## 🚨 Troubleshooting

### Common Issues

1. **Cron job not running**
   ```bash
   # Check cron service
   systemctl status cron
   
   # Check cron logs
   tail -f /var/log/cron
   
   # Test manually
   ./daily_import.sh --test
   ```

2. **Database connection failed**
   ```bash
   # Test connection
   ./setup_environment.sh test
   
   # Check environment
   ./setup_environment.sh validate
   ```

3. **Email not sending**
   ```bash
   # Test email config
   python email_notifications.py test --to your@email.com
   
   # Check SMTP settings
   grep EMAIL .env
   ```

4. **High disk usage**
   ```bash
   # Check log sizes
   ./monitor_system.sh --logs
   
   # Clean old logs
   find logs/ -name "*.log" -mtime +30 -delete
   ```

### Debug Commands

```bash
# Full system check
./monitor_system.sh

# Verbose import test
./daily_import.sh --dry-run --verbose

# Environment validation
./setup_environment.sh validate

# Manual import test
python ../supabase_import.py --dry-run --verbose
```

## 📈 Performance Optimization

### Tuning Parameters

- **Batch Size**: Adjust `IMPORT_BATCH_SIZE` for performance
- **Timeout**: Increase timeouts for slow connections
- **Memory**: Monitor memory usage for large datasets
- **Disk**: Regular log cleanup to prevent disk full

### Monitoring Metrics

- **Import Duration**: Target < 60 seconds
- **Success Rate**: Target > 95%
- **Error Rate**: Target < 5%
- **Disk Usage**: Keep < 80%

## 🔄 Maintenance

### Daily Tasks
- Automated import at 3:00 AM
- Error monitoring and alerting
- Log rotation and cleanup

### Weekly Tasks
- Health check verification
- Performance review
- Disk usage monitoring

### Monthly Tasks
- Log file cleanup
- Dependency updates
- Security review

## 📚 Documentation

- [Installation Guide](INSTALLATION_GUIDE.md) - Platform-specific setup
- [Import README](../IMPORT_README.md) - Import system documentation
- [Import Summary](../SUPABASE_IMPORT_SUMMARY.md) - Technical overview

## 🤝 Support

For issues or questions:

1. Check the monitoring dashboard
2. Review log files for errors
3. Run system diagnostics
4. Test components individually
5. Verify configuration settings

## 🔮 Future Enhancements

Planned improvements:
- Web dashboard for monitoring
- Slack/Teams notifications
- Multi-supermarket support
- Real-time data updates
- Advanced analytics
- Container deployment
- Kubernetes support

## 📋 Checklist

Before going live:

- [ ] Environment variables configured
- [ ] Database connectivity tested
- [ ] Cron jobs installed
- [ ] Email notifications working
- [ ] Log rotation configured
- [ ] Monitoring alerts set up
- [ ] File permissions secured
- [ ] Backup procedures in place
- [ ] Documentation updated
- [ ] Team trained on system

## 🎯 Success Metrics

Target KPIs:
- **Uptime**: 99.9%
- **Success Rate**: >95%
- **Import Duration**: <60s
- **Error Resolution**: <2h
- **Disk Usage**: <80%
- **Memory Usage**: <80%

This automation system provides a robust, production-ready solution for daily CheckjeBon data imports with comprehensive monitoring, alerting, and maintenance capabilities.