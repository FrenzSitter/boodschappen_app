# CheckjeBon Data Validation System

Comprehensive data validation and monitoring system that ensures data quality and system health after each import.

## 🎯 Overview

The data validation system provides:
- **Data Freshness Monitoring** - Tracks when data was last updated
- **Data Integrity Checks** - Validates data format, completeness, and accuracy
- **Record Count Comparison** - Monitors changes in data volume between runs
- **Health Report Generation** - Creates detailed daily health reports
- **Price Change Detection** - Identifies significant price fluctuations
- **Automated Alerting** - Sends notifications for data issues

## 📁 Components

### 1. Data Validation Script (`data_validation.py`)
Main validation engine that performs comprehensive data quality checks.

### 2. Configuration File (`validation_config.json`)
Configurable thresholds and validation rules.

### 3. Dashboard (`validation_dashboard.py`)
Interactive web dashboard for monitoring validation results.

### 4. Integration
Seamlessly integrated with the daily import script for automatic validation.

## 🚀 Quick Start

### Basic Usage

```bash
# Run full validation
python automation/data_validation.py

# Run specific checks
python automation/data_validation.py --freshness
python automation/data_validation.py --integrity
python automation/data_validation.py --counts
python automation/data_validation.py --prices

# Generate health report
python automation/data_validation.py --report
```

### Dashboard

```bash
# Start validation dashboard
python automation/validation_dashboard.py

# Custom host/port
python automation/validation_dashboard.py --host 0.0.0.0 --port 8080

# Access dashboard
open http://localhost:5000
```

## 📊 Validation Checks

### 1. Data Freshness
**Purpose**: Ensures data is current and up-to-date

**Checks**:
- Products table last update time
- Price data last update time
- Supermarket data freshness
- Configurable staleness threshold (default: 48 hours)

**Alerts**:
- Data older than threshold triggers warning
- Missing data triggers failure

### 2. Data Integrity
**Purpose**: Validates data completeness and format

**Checks**:
- Missing product names
- Missing or invalid prices
- Products without prices
- Price range validation
- Required field validation

**Thresholds**:
- Missing prices: <5% (configurable)
- Invalid formats: <2% (configurable)
- Products without prices: <5% (configurable)

### 3. Record Count Comparison
**Purpose**: Monitors data volume changes

**Checks**:
- Product count changes
- Price record changes
- Supermarket data changes
- Category distribution changes

**Alerts**:
- Changes >20% trigger warnings (configurable)
- Significant drops trigger failures

### 4. Price Change Detection
**Purpose**: Identifies unusual price fluctuations

**Checks**:
- Price changes >20% (configurable)
- Sudden price spikes or drops
- Price trend analysis
- Price consistency checks

**Reports**:
- Top 5 price increases
- Top 5 price decreases
- Price volatility metrics

## 🔧 Configuration

### Validation Config (`validation_config.json`)

```json
{
  "freshness_threshold_hours": 48,
  "price_change_threshold": 0.20,
  "min_record_count": 100,
  "max_record_count": 1000000,
  "alert_thresholds": {
    "missing_prices_pct": 5.0,
    "invalid_formats_pct": 2.0,
    "record_count_change_pct": 20.0,
    "stale_data_pct": 10.0
  }
}
```

### Environment Variables

```bash
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Optional - Email Notifications
EMAIL_ENABLED=true
EMAIL_TO=admin@example.com
EMAIL_FROM=noreply@checkjebon.local
```

## 📈 Health Reports

### Daily Health Report Structure

```json
{
  "date": "2025-01-09",
  "total_checks": 12,
  "passed_checks": 10,
  "warning_checks": 2,
  "failed_checks": 0,
  "data_freshness": {
    "products": {
      "latest_update": "2025-01-09T03:15:00Z",
      "hours_old": 2.5,
      "is_fresh": true
    }
  },
  "integrity_checks": {
    "total_products": 5678,
    "missing_prices": 12,
    "invalid_prices": 3,
    "missing_prices_pct": 0.2
  },
  "record_counts": {
    "products": {
      "current": 5678,
      "previous": 5650,
      "change": 28,
      "change_pct": 0.5
    }
  },
  "price_changes": {
    "total_changes": 234,
    "significant_changes": 12,
    "largest_increases": [...],
    "largest_decreases": [...]
  },
  "alerts": [
    "High percentage of missing prices: 5.2%"
  ],
  "recommendations": [
    "Investigate why some products don't have prices"
  ]
}
```

### Report Formats

- **JSON**: Machine-readable format for automation
- **HTML**: Human-readable format with styling
- **Email**: Formatted for email notifications

## 🚨 Alerting System

### Alert Types

1. **Data Freshness Alerts**
   - Stale data warnings
   - Missing data failures

2. **Data Integrity Alerts**
   - High missing price percentages
   - Invalid data format issues
   - Required field violations

3. **Volume Change Alerts**
   - Significant record count changes
   - Unexpected data volume spikes/drops

4. **Price Change Alerts**
   - Unusual price fluctuations
   - Price volatility warnings

### Notification Channels

- **Email**: Detailed failure reports
- **Dashboard**: Real-time status
- **Log Files**: Structured logging
- **Future**: Slack, Teams, Discord webhooks

## 📱 Dashboard Features

### Real-time Metrics
- Total validation runs
- Success rate percentage
- Average validation duration
- Recent status indicator
- Active alerts count

### Trend Analysis
- 7-day validation trends
- Pass/warning/failure rates
- Historical performance

### Interactive Features
- Auto-refresh every 30 seconds
- Manual refresh button
- Responsive design
- Chart visualizations

### Access Dashboard
```bash
# Start dashboard
python automation/validation_dashboard.py

# Access in browser
http://localhost:5000
```

## 🔗 Integration

### Automatic Integration
The validation system automatically runs after each successful import:

```bash
# In daily_import.sh
if run_import; then
    log_success "Daily import completed successfully"
    
    # Run data validation after successful import
    if run_data_validation; then
        log_success "Data validation passed"
    else
        log_error "Data validation failed"
    fi
fi
```

### Manual Integration
Run validation independently:

```bash
# After manual import
python supabase_import.py
python automation/data_validation.py
```

## 📊 Monitoring

### Log Files
- `logs/data_validation.log` - Detailed validation logs
- `logs/health_reports/` - Daily health reports
- `logs/daily_import.log` - Integration logs

### Metrics Tracking
- Validation execution time
- Check success rates
- Alert frequency
- Data quality trends

### Performance Monitoring
- Database query performance
- Validation script execution time
- Memory usage during validation
- Storage usage for reports

## 🛠️ Maintenance

### Regular Tasks

1. **Log Rotation**
   - Health reports: 30-day retention
   - Validation logs: Auto-rotation
   - Report cleanup: Monthly

2. **Configuration Updates**
   - Threshold adjustments
   - Alert rule modifications
   - New validation rules

3. **System Health**
   - Database performance
   - Validation script updates
   - Dashboard maintenance

### Troubleshooting

```bash
# Check validation logs
tail -f logs/data_validation.log

# Test specific validation
python automation/data_validation.py --integrity --verbose

# Verify configuration
python automation/data_validation.py --config

# Check dashboard status
curl http://localhost:5000/api/summary
```

## 📋 Validation Checklist

Before going live:
- [ ] Configure validation thresholds
- [ ] Set up email notifications
- [ ] Test all validation checks
- [ ] Verify dashboard access
- [ ] Configure alert rules
- [ ] Test integration with import
- [ ] Set up log rotation
- [ ] Configure monitoring
- [ ] Train team on dashboard
- [ ] Document procedures

## 🚀 Usage Examples

### Example 1: Daily Health Check
```bash
# Run full validation after import
python automation/data_validation.py

# Check results
ls -la logs/health_reports/health_report_$(date +%Y-%m-%d).*
```

### Example 2: Price Monitoring
```bash
# Monitor price changes only
python automation/data_validation.py --prices

# Check for alerts
grep "price change" logs/data_validation.log
```

### Example 3: Data Quality Dashboard
```bash
# Start dashboard
python automation/validation_dashboard.py --host 0.0.0.0

# Access from any device
http://your-server:5000
```

## 🔮 Future Enhancements

Planned improvements:
- **Machine Learning**: Anomaly detection
- **Webhooks**: Slack/Teams integration
- **Real-time**: Live data validation
- **Advanced Analytics**: Predictive monitoring
- **API**: REST API for external integrations
- **Mobile**: Mobile-friendly dashboard
- **Backup**: Validation result backup

## 📞 Support

For validation issues:
1. Check validation logs: `logs/data_validation.log`
2. Review health reports: `logs/health_reports/`
3. Use dashboard: `http://localhost:5000`
4. Run specific checks: `--freshness`, `--integrity`, etc.
5. Verify configuration: `validation_config.json`

## 🎯 Success Metrics

Target KPIs:
- **Data Freshness**: <6 hours average
- **Data Integrity**: >95% quality score
- **Validation Success**: >98% pass rate
- **Alert Response**: <2 hour resolution
- **System Uptime**: >99.9%

This comprehensive validation system ensures high data quality and provides early warning for potential issues in the CheckjeBon import system.