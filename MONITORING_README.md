# Price History Monitoring System

Comprehensive monitoring system for CheckjeBon price history import process with automated alerts, reporting, and maintenance capabilities.

## 🚀 Features

- **Data Freshness Monitoring**: Track import timeliness and data completeness
- **Price Change Detection**: Identify unusual price movements and potential errors
- **Data Quality Checks**: Validate price ranges, duplicates, and consistency
- **Performance Monitoring**: Track import times, query performance, and storage
- **Automated Reporting**: Daily, weekly, and monthly reports with insights
- **Data Maintenance**: Archive old data, cleanup orphans, optimize performance
- **Email Notifications**: Automated alerts and report delivery
- **Dashboard Integration**: Export metrics for Grafana, Prometheus, and custom dashboards

## 📋 Requirements

- Python 3.8+
- Supabase database with price history schema
- SMTP server for email notifications (optional)
- Redis for caching (optional)

## 🔧 Installation

```bash
pip install -r requirements.txt
```

Additional dependencies for monitoring:
- `numpy>=1.24.0`
- `pandas>=2.0.0`
- `smtplib` (built-in)

## 🎯 Quick Start

```python
from monitoring_system import create_monitor

# Create monitor with default configuration
monitor = create_monitor(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-supabase-key"
)

# Run complete monitoring suite
result = monitor.run_full_monitoring()

print(f"System Health: {result['overall_health_percentage']:.1f}%")
print(f"Alerts: {result['alerts_triggered']}")
```

## 📊 Core Components

### 1. Data Freshness Monitoring

Monitor data import timeliness and completeness:

```python
# Check data freshness
freshness_result = monitor.check_data_freshness()

print(f"Hours since import: {freshness_result['hours_since_import']}")
print(f"Supermarket coverage: {freshness_result['supermarket_coverage']['coverage_percentage']:.1f}%")
```

**Monitored Metrics**:
- Time since last import
- Daily record counts
- Supermarket coverage
- Data completeness by category

**Alerts Triggered**:
- Import overdue (>25 hours by default)
- Low daily record count
- Missing supermarket data

### 2. Price Change Detection

Identify unusual price movements and data anomalies:

```python
# Detect price anomalies
anomaly_result = monitor.detect_price_anomalies(days=1)

print(f"Extreme changes: {len(anomaly_result['anomalies']['extreme_changes'])}")
print(f"Price errors: {len(anomaly_result['anomalies']['price_errors'])}")
```

**Detection Features**:
- Extreme price changes (>200% by default)
- Unrealistic price values (<€0.01 or >€1000)
- High volatility products
- Missing prices for existing products

**Alert Types**:
- Price spike detection
- Price drop alerts
- Data validation errors
- Volatility warnings

### 3. Data Quality Checks

Comprehensive data validation and quality scoring:

```python
# Run quality checks
quality_result = monitor.run_data_quality_checks()

print(f"Quality score: {quality_result['overall_quality_score']:.1f}%")

# Individual checks
for check_name, result in quality_result['checks'].items():
    print(f"{check_name}: {result['issue_count']} issues")
```

**Quality Checks**:
- Duplicate record detection
- Data consistency validation
- Completeness assessment
- Referential integrity verification

**Quality Score Calculation**:
- 100 points base score
- Deductions for duplicates, inconsistencies, missing data
- Weighted by issue severity

### 4. Performance Monitoring

Track system performance and resource usage:

```python
# Monitor performance
performance_result = monitor.monitor_performance()

metrics = performance_result['metrics']
print(f"Import duration: {metrics['import_performance']['avg_duration_minutes']:.1f} min")
print(f"Query time: {metrics['query_performance']['avg_query_time']:.3f} sec")
```

**Performance Metrics**:
- Import processing rate (records/minute)
- Database query response times
- Storage usage and growth
- Error rates and trends

**Performance Alerts**:
- Slow import processing
- Long query response times
- High storage growth
- Elevated error rates

### 5. Automated Reporting

Generate comprehensive reports automatically:

```python
# Generate reports
daily_report = monitor.generate_daily_report()
weekly_report = monitor.generate_weekly_report()
monthly_report = monitor.generate_monthly_report()

# Send report via email
monitor.send_report_notification(daily_report)
```

**Report Types**:

#### Daily Import Summary
- Import status and statistics
- Records processed and errors
- Price changes detected
- Immediate recommendations

#### Weekly Price Trends
- Price movement analysis
- Volatility assessment
- Significant changes summary
- Market trend insights

#### Monthly Data Health
- Overall system health score
- Data quality trends
- Performance analytics
- Strategic recommendations

### 6. Data Maintenance

Automated data maintenance and optimization:

```python
# Run maintenance operations
maintenance_result = monitor.run_data_maintenance()

operations = maintenance_result['operations']
print(f"Records archived: {operations['archive_operations']['records_identified']}")
print(f"Orphans cleaned: {operations['cleanup_operations']['total_records_cleaned']}")
```

**Maintenance Operations**:
- Archive old price history (>2 years by default)
- Clean up orphaned records
- Optimize database performance
- Validate backup integrity

**Optimization Features**:
- Update table statistics
- Rebuild indexes
- Vacuum tables (PostgreSQL)
- Analyze query performance

## ⚙️ Configuration

Configure monitoring behavior with `MonitoringConfig`:

```python
from monitoring_system import MonitoringConfig, create_monitor

config = MonitoringConfig(
    # Data freshness thresholds
    max_import_age_hours=25,
    min_daily_records=1000,
    expected_supermarkets=11,
    
    # Price change thresholds
    max_price_change_percentage=200.0,
    price_volatility_threshold=50.0,
    min_price_value=0.01,
    max_price_value=1000.0,
    
    # Data quality thresholds
    max_duplicate_percentage=1.0,
    min_product_coverage=90.0,
    max_missing_data_percentage=5.0,
    
    # Performance thresholds
    max_import_duration_minutes=120,
    max_query_time_seconds=30.0,
    max_error_rate_percentage=5.0,
    
    # Email configuration
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    email_from="monitoring@yourcompany.com",
    email_password="your-app-password",
    alert_recipients=["admin@yourcompany.com"],
    report_recipients=["management@yourcompany.com"]
)

monitor = create_monitor(supabase_url, supabase_key, config)
```

## 📧 Email Notifications

Automated email alerts and reports:

### Alert Notifications

```python
# Configure email settings
config = MonitoringConfig(
    email_from="alerts@yourcompany.com",
    email_password="your-app-password",
    alert_recipients=["admin@yourcompany.com", "ops@yourcompany.com"]
)

# Alerts are sent automatically based on severity
monitor = create_monitor(supabase_url, supabase_key, config)
result = monitor.run_full_monitoring()  # Sends alerts if triggered
```

**Alert Severity Levels**:
- **Critical**: System failures, database connectivity issues
- **High**: Data freshness problems, extreme price changes
- **Medium**: Data quality issues, performance degradation
- **Low**: Minor inconsistencies, trend notifications

### Report Delivery

```python
# Generate and send reports
daily_report = monitor.generate_daily_report()
success = monitor.send_report_notification(daily_report)
```

**Email Features**:
- HTML formatted emails with styling
- Severity-based alert grouping
- Comprehensive report summaries
- Actionable recommendations

## 📈 Dashboard Integration

Export metrics for popular monitoring dashboards:

### Prometheus Metrics

```python
from monitoring_dashboard import create_dashboard_metrics

dashboard = create_dashboard_metrics(supabase_url, supabase_key)

# Export Prometheus format
prometheus_metrics = dashboard.export_prometheus_metrics()
print(prometheus_metrics)
```

**Sample Prometheus Output**:
```
# HELP price_history_system_health Overall system health percentage
# TYPE price_history_system_health gauge
price_history_system_health_score{status="healthy"} 95.5
price_history_data_freshness{status="healthy"} 2.1
price_history_processing_rate{unit="records/min"} 150.2
```

### Grafana Dashboard

```python
# Export Grafana dashboard configuration
grafana_config = dashboard.export_grafana_dashboard()

# Import into Grafana or save as JSON
with open('price_history_dashboard.json', 'w') as f:
    json.dump(grafana_config, f, indent=2)
```

**Dashboard Panels**:
- System health score gauge
- Data quality score gauge
- Import volume trends
- Response time graphs
- Alert summaries

### Custom Dashboard JSON

```python
# Export as JSON for custom dashboards
json_metrics = dashboard.export_json_metrics()
metrics_data = json.loads(json_metrics)

# Use with custom visualization tools
```

## 🔍 Dashboard Metrics

Real-time metrics for operational dashboards:

### System Health KPIs

```python
dashboard = create_dashboard_metrics(supabase_url, supabase_key)
metrics = dashboard.get_dashboard_metrics()

# System health metrics
for metric in metrics['system_health']:
    print(f"{metric.name}: {metric.value} {metric.unit} ({metric.status})")
```

**Key Metrics**:
- Overall system health score (0-100%)
- Data freshness (hours since last import)
- Database connectivity status
- API response times

### Data Quality KPIs

**Metrics Included**:
- Data quality score (0-100%)
- Record completeness percentage
- Duplicate record count
- Invalid price count

### Performance KPIs

**Metrics Tracked**:
- Processing rate (records/minute)
- Average query time (milliseconds)
- Storage usage (GB)
- Error rate percentage

### Import Status KPIs

**Real-time Tracking**:
- Today's import count
- Supermarket coverage percentage
- Price changes detected (24h)
- Products updated (24h)

## 🛠️ Advanced Usage

### Custom Alert Rules

```python
# Create custom monitoring logic
def check_custom_business_rules(monitor):
    # Get price trends
    from price_analysis import create_analyzer
    analyzer = create_analyzer(supabase_url, supabase_key)
    
    trends = analyzer.get_price_trends(days=7)
    
    # Custom rule: Alert if >10 products have >50% price increase
    high_increases = [t for t in trends if t.price_change_percentage > 50]
    
    if len(high_increases) > 10:
        monitor._create_alert(
            alert_type="business_rule",
            severity="high",
            title="Unusual Market Activity",
            description=f"{len(high_increases)} products with >50% price increases",
            metric_value=len(high_increases),
            threshold_value=10,
            recommended_action="Investigate market conditions and data sources"
        )

# Run custom checks
check_custom_business_rules(monitor)
```

### Batch Monitoring

```python
# Monitor multiple aspects in sequence
def comprehensive_monitoring_cycle():
    monitor = create_monitor(supabase_url, supabase_key)
    
    results = {}
    
    # Data freshness
    results['freshness'] = monitor.check_data_freshness()
    
    # Price anomalies
    results['anomalies'] = monitor.detect_price_anomalies()
    
    # Data quality
    results['quality'] = monitor.run_data_quality_checks()
    
    # Performance
    results['performance'] = monitor.monitor_performance()
    
    # Maintenance (weekly)
    if datetime.now().weekday() == 0:  # Monday
        results['maintenance'] = monitor.run_data_maintenance()
    
    return results

# Run comprehensive monitoring
monitoring_results = comprehensive_monitoring_cycle()
```

### Integration with External Systems

```python
# Integrate with Slack
import requests

def send_slack_alert(alert, webhook_url):
    payload = {
        "text": f"🚨 {alert.title}",
        "attachments": [
            {
                "color": "danger" if alert.severity == "critical" else "warning",
                "fields": [
                    {"title": "Description", "value": alert.description},
                    {"title": "Severity", "value": alert.severity.upper()},
                    {"title": "Recommended Action", "value": alert.recommended_action}
                ]
            }
        ]
    }
    
    requests.post(webhook_url, json=payload)

# Send critical alerts to Slack
monitor = create_monitor(supabase_url, supabase_key)
result = monitor.run_full_monitoring()

for alert_data in result.get('alerts', []):
    if alert_data['severity'] == 'critical':
        send_slack_alert(alert_data, "https://hooks.slack.com/your-webhook")
```

### Scheduled Monitoring

```python
# Schedule monitoring with cron-like syntax
import schedule
import time

def daily_monitoring():
    monitor = create_monitor(supabase_url, supabase_key)
    result = monitor.run_full_monitoring()
    
    # Generate and send daily report
    daily_report = monitor.generate_daily_report()
    monitor.send_report_notification(daily_report)
    
    print(f"Daily monitoring completed. Health: {result['overall_health_percentage']:.1f}%")

def weekly_maintenance():
    monitor = create_monitor(supabase_url, supabase_key)
    monitor.run_data_maintenance()
    print("Weekly maintenance completed")

# Schedule tasks
schedule.every().day.at("06:00").do(daily_monitoring)
schedule.every().monday.at("02:00").do(weekly_maintenance)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```python
   # Test connectivity
   try:
       monitor = create_monitor(supabase_url, supabase_key)
       result = monitor.check_data_freshness()
       print("✓ Database connection OK")
   except Exception as e:
       print(f"✗ Database connection failed: {e}")
   ```

2. **Email Notifications Not Working**
   ```python
   # Test email configuration
   config = MonitoringConfig(
       email_from="test@yourcompany.com",
       email_password="your-app-password"
   )
   
   monitor = create_monitor(supabase_url, supabase_key, config)
   success = monitor.send_email_notification(
       subject="Test Alert",
       body="This is a test email",
       recipients=["admin@yourcompany.com"]
   )
   
   print(f"Email test: {'✓ Success' if success else '✗ Failed'}")
   ```

3. **High Memory Usage**
   ```python
   # Use smaller batch sizes for large datasets
   config = MonitoringConfig(
       max_results=500,  # Limit result sets
       cache_ttl=600     # Reduce cache retention
   )
   ```

4. **Slow Performance**
   ```python
   # Check query performance
   performance_result = monitor.monitor_performance()
   query_metrics = performance_result['metrics']['query_performance']
   
   if query_metrics['max_query_time'] > 30:
       print("⚠ Slow queries detected - consider database optimization")
   ```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# All monitoring operations will be logged
monitor = create_monitor(supabase_url, supabase_key)
result = monitor.run_full_monitoring()
```

### Health Check Script

```python
#!/usr/bin/env python3
def health_check():
    """Quick health check script"""
    monitor = create_monitor(supabase_url, supabase_key)
    
    # Test database
    try:
        freshness = monitor.check_data_freshness()
        print("✓ Database accessible")
    except:
        print("✗ Database connection failed")
        return False
    
    # Check data freshness
    hours_old = freshness['hours_since_import']
    if hours_old < 25:
        print("✓ Data is fresh")
    else:
        print(f"⚠ Data is {hours_old:.1f} hours old")
    
    # Quick quality check
    quality = monitor.run_data_quality_checks()
    score = quality['overall_quality_score']
    if score > 90:
        print("✓ Data quality excellent")
    else:
        print(f"⚠ Data quality score: {score:.1f}%")
    
    return True

if __name__ == "__main__":
    health_check()
```

## 📝 Examples

Run the examples to see all features in action:

```bash
python monitoring_examples.py
```

**Example Categories**:
- Basic monitoring setup
- Custom configuration
- Data freshness monitoring
- Price anomaly detection
- Data quality checks
- Performance monitoring
- Automated reporting
- Data maintenance
- Dashboard metrics
- Export formats
- Email notifications
- Real-time monitoring
- Troubleshooting

## 🔄 Production Deployment

### Environment Setup

```bash
# Production environment variables
export SUPABASE_URL="https://your-prod-project.supabase.co"
export SUPABASE_KEY="your-production-service-key"
export SMTP_PASSWORD="your-production-email-password"
export ALERT_RECIPIENTS="admin@yourcompany.com,ops@yourcompany.com"
```

### Systemd Service

Create a systemd service for continuous monitoring:

```ini
[Unit]
Description=Price History Monitoring Service
After=network.target

[Service]
Type=simple
User=monitoring
WorkingDirectory=/opt/boodschappen_app
Environment=SUPABASE_URL=https://your-project.supabase.co
Environment=SUPABASE_KEY=your-key
ExecStart=/usr/bin/python3 -m monitoring_system
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY monitoring_system.py .
COPY monitoring_dashboard.py .

CMD ["python", "monitoring_system.py"]
```

### Monitoring Schedule

```bash
# Add to crontab for scheduled monitoring
0 6 * * * /opt/boodschappen_app/run_daily_monitoring.sh
0 2 * * 1 /opt/boodschappen_app/run_weekly_maintenance.sh
0 1 1 * * /opt/boodschappen_app/run_monthly_report.sh
```

This comprehensive monitoring system provides complete visibility into your price history import process with automated alerts, detailed reporting, and proactive maintenance capabilities.