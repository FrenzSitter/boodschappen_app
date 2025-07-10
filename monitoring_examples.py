#!/usr/bin/env python3
"""
Monitoring System Examples
==========================

Comprehensive examples demonstrating how to use the price history
monitoring system for various scenarios and use cases.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from monitoring_system import PriceHistoryMonitor, MonitoringConfig, create_monitor
from monitoring_dashboard import DashboardMetrics, create_dashboard_metrics

def example_basic_monitoring():
    """Basic monitoring example"""
    print("=== Basic Monitoring Example ===")
    
    # Create monitor with default configuration
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Run full monitoring suite
    result = monitor.run_full_monitoring()
    
    print(f"Monitoring Status: {result['status']}")
    print(f"Overall Health: {result.get('overall_health_percentage', 0):.1f}%")
    print(f"Alerts Triggered: {result.get('alerts_triggered', 0)}")
    print(f"Notifications Sent: {result.get('notifications_sent', False)}")
    
    # Show any alerts
    if result.get('alerts'):
        print("\nAlerts:")
        for alert in result['alerts'][:3]:  # Show first 3 alerts
            print(f"- {alert['title']}: {alert['description']}")

def example_custom_configuration():
    """Custom configuration example"""
    print("=== Custom Configuration Example ===")
    
    # Create custom configuration
    custom_config = MonitoringConfig(
        max_import_age_hours=12,  # More strict freshness requirement
        min_daily_records=5000,   # Higher minimum records
        max_price_change_percentage=100.0,  # Lower change threshold
        price_volatility_threshold=25.0,    # Lower volatility threshold
        max_duplicate_percentage=0.5,       # Stricter duplicate tolerance
        smtp_server="smtp.gmail.com",
        email_from="alerts@yourcompany.com",
        alert_recipients=["admin@yourcompany.com", "ops@yourcompany.com"],
        report_recipients=["management@yourcompany.com"]
    )
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        config=custom_config
    )
    
    print(f"Custom config - Max import age: {custom_config.max_import_age_hours} hours")
    print(f"Custom config - Min daily records: {custom_config.min_daily_records}")
    print(f"Custom config - Price change threshold: {custom_config.max_price_change_percentage}%")
    
    # Run specific checks with custom configuration
    freshness_result = monitor.check_data_freshness()
    print(f"Data freshness check: {freshness_result['status']}")

def example_data_freshness_monitoring():
    """Data freshness monitoring example"""
    print("=== Data Freshness Monitoring Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Check data freshness
    freshness_result = monitor.check_data_freshness()
    
    if freshness_result['status'] == 'completed':
        print(f"Last import: {freshness_result['last_import']}")
        print(f"Hours since import: {freshness_result['hours_since_import']:.1f}")
        
        # Show daily counts
        daily_counts = freshness_result['daily_counts']
        if daily_counts:
            print("\nDaily record counts:")
            for day_data in daily_counts[:5]:  # Show last 5 days
                print(f"  {day_data['date']}: {day_data['count']} records")
        
        # Show supermarket coverage
        coverage = freshness_result['supermarket_coverage']
        print(f"\nSupermarket coverage: {coverage['active_count']}/{coverage['total_supermarkets']}")
        if coverage['missing_supermarkets']:
            print(f"Missing supermarkets: {', '.join(coverage['missing_supermarkets'])}")
    else:
        print(f"Error: {freshness_result.get('error', 'Unknown error')}")

def example_price_anomaly_detection():
    """Price anomaly detection example"""
    print("=== Price Anomaly Detection Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Detect price anomalies
    anomaly_result = monitor.detect_price_anomalies(days=1)
    
    if anomaly_result['status'] == 'completed':
        anomalies = anomaly_result['anomalies']
        
        print(f"Total issues found: {anomaly_result['total_issues']}")
        
        # Show extreme price changes
        if anomalies['extreme_changes']:
            print(f"\nExtreme price changes ({len(anomalies['extreme_changes'])}):")
            for change in anomalies['extreme_changes'][:3]:
                print(f"- {change['product_name']} at {change['supermarket_name']}")
                print(f"  Price: €{change['price']:.2f} ({change['change_percentage']:+.1f}%)")
        
        # Show price errors
        if anomalies['price_errors']:
            print(f"\nPrice errors ({len(anomalies['price_errors'])}):")
            for error in anomalies['price_errors'][:3]:
                print(f"- {error['product_name']}: €{error['price']:.2f} ({error['error_type']})")
        
        # Show high volatility products
        if anomalies['high_volatility']:
            print(f"\nHigh volatility products ({len(anomalies['high_volatility'])}):")
            for vol in anomalies['high_volatility'][:3]:
                print(f"- {vol['product_name']}: {vol['volatility']:.1f}% volatility")
    else:
        print(f"Error: {anomaly_result.get('error', 'Unknown error')}")

def example_data_quality_checks():
    """Data quality checks example"""
    print("=== Data Quality Checks Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Run data quality checks
    quality_result = monitor.run_data_quality_checks()
    
    if quality_result['status'] == 'completed':
        print(f"Overall quality score: {quality_result['overall_quality_score']:.1f}%")
        
        # Show individual check results
        checks = quality_result['checks']
        for check_name, check_result in checks.items():
            issue_count = check_result.get('issue_count', 0)
            status = "✓" if issue_count == 0 else "⚠"
            print(f"{status} {check_name.replace('_', ' ').title()}: {issue_count} issues")
            
            if issue_count > 0:
                print(f"   {check_result.get('description', 'No description')}")
        
        print(f"\nAlerts generated: {quality_result['alerts_generated']}")
    else:
        print(f"Error: {quality_result.get('error', 'Unknown error')}")

def example_performance_monitoring():
    """Performance monitoring example"""
    print("=== Performance Monitoring Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Monitor performance
    performance_result = monitor.monitor_performance()
    
    if performance_result['status'] == 'completed':
        metrics = performance_result['metrics']
        
        # Show import performance
        import_perf = metrics.get('import_performance', {})
        if import_perf.get('status') != 'error':
            print(f"Import Performance:")
            print(f"  Latest duration: {import_perf.get('latest_duration_minutes', 0):.1f} minutes")
            print(f"  Average duration: {import_perf.get('avg_duration_minutes', 0):.1f} minutes")
            print(f"  Max duration: {import_perf.get('max_duration_minutes', 0):.1f} minutes")
        
        # Show query performance
        query_perf = metrics.get('query_performance', {})
        if query_perf.get('status') != 'error':
            print(f"\nQuery Performance:")
            print(f"  Max query time: {query_perf.get('max_query_time', 0):.3f} seconds")
            print(f"  Average query time: {query_perf.get('avg_query_time', 0):.3f} seconds")
        
        # Show storage usage
        storage = metrics.get('storage_usage', {})
        if storage.get('status') != 'error':
            print(f"\nStorage Usage:")
            print(f"  Estimated size: {storage.get('estimated_size_mb', 0):.1f} MB")
            print(f"  Monthly growth: {storage.get('monthly_growth_gb', 0):.2f} GB")
        
        # Show error rates
        error_rates = metrics.get('error_rates', {})
        if error_rates.get('status') != 'error':
            print(f"\nError Rates:")
            print(f"  Total records: {error_rates.get('total_records', 0)}")
            print(f"  Total errors: {error_rates.get('total_errors', 0)}")
            print(f"  Error rate: {error_rates.get('error_rate_percentage', 0):.2f}%")
        
        print(f"\nPerformance alerts: {performance_result['alerts_generated']}")
    else:
        print(f"Error: {performance_result.get('error', 'Unknown error')}")

def example_automated_reporting():
    """Automated reporting example"""
    print("=== Automated Reporting Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Generate different types of reports
    print("Generating reports...")
    
    # Daily report
    daily_report = monitor.generate_daily_report()
    print(f"\nDaily Report ({daily_report.generated_at.strftime('%Y-%m-%d')}):")
    print(f"  Import status: {daily_report.summary.get('import_status', 'unknown')}")
    print(f"  Records imported: {daily_report.summary.get('records_imported', 0)}")
    print(f"  Price changes: {daily_report.summary.get('price_changes', 0)}")
    print(f"  Alerts triggered: {daily_report.summary.get('alerts_triggered', 0)}")
    print(f"  Data quality score: {daily_report.summary.get('data_quality_score', 0):.1f}%")
    
    if daily_report.recommendations:
        print("  Recommendations:")
        for rec in daily_report.recommendations:
            print(f"    - {rec}")
    
    # Weekly report
    weekly_report = monitor.generate_weekly_report()
    print(f"\nWeekly Report:")
    print(f"  Products analyzed: {weekly_report.summary.get('total_products_analyzed', 0)}")
    print(f"  Avg price change: {weekly_report.summary.get('avg_price_change', 0):.2f}%")
    print(f"  Significant changes: {weekly_report.summary.get('significant_changes', 0)}")
    print(f"  Volatile products: {weekly_report.summary.get('volatile_products', 0)}")
    
    # Monthly report
    monthly_report = monitor.generate_monthly_report()
    print(f"\nMonthly Report:")
    print(f"  Data quality score: {monthly_report.summary.get('data_quality_score', 0):.1f}%")
    print(f"  Total imports: {monthly_report.summary.get('total_imports', 0)}")
    print(f"  Uptime percentage: {monthly_report.summary.get('system_uptime_percentage', 0):.1f}%")

def example_data_maintenance():
    """Data maintenance example"""
    print("=== Data Maintenance Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Run data maintenance
    maintenance_result = monitor.run_data_maintenance()
    
    if maintenance_result['status'] == 'completed':
        operations = maintenance_result['operations']
        
        print(f"Maintenance completed at: {maintenance_result['timestamp']}")
        
        # Show archive operations
        archive_ops = operations.get('archive_operations', {})
        if archive_ops.get('status') == 'completed':
            print(f"Archive: {archive_ops.get('records_identified', 0)} records identified for archiving")
        
        # Show cleanup operations
        cleanup_ops = operations.get('cleanup_operations', {})
        if cleanup_ops.get('status') == 'completed':
            print(f"Cleanup: {cleanup_ops.get('total_records_cleaned', 0)} orphaned records cleaned")
        
        # Show optimization operations
        optimization_ops = operations.get('optimization_operations', {})
        if optimization_ops.get('status') == 'completed':
            optimizations = optimization_ops.get('optimizations', {})
            print(f"Optimization:")
            print(f"  Statistics updated: {optimizations.get('statistics_updated', False)}")
            print(f"  Indexes rebuilt: {optimizations.get('indexes_rebuilt', False)}")
            print(f"  Tables vacuumed: {optimizations.get('tables_vacuumed', False)}")
        
        # Show backup validation
        backup_ops = operations.get('backup_validation', {})
        if backup_ops.get('status') == 'completed':
            validation = backup_ops.get('validation_results', {})
            print(f"Backup validation:")
            print(f"  Data consistency: {validation.get('data_consistency', False)}")
            print(f"  Row counts match: {validation.get('row_counts_match', False)}")
            print(f"  Foreign keys valid: {validation.get('foreign_keys_valid', False)}")
    else:
        print(f"Error: {maintenance_result.get('error', 'Unknown error')}")

def example_dashboard_metrics():
    """Dashboard metrics example"""
    print("=== Dashboard Metrics Example ===")
    
    dashboard = create_dashboard_metrics(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    # Get dashboard metrics
    metrics = dashboard.get_dashboard_metrics()
    
    if 'error' not in metrics:
        print("Dashboard metrics generated successfully")
        
        # Show system health metrics
        system_health = metrics.get('system_health', [])
        if system_health:
            print("\nSystem Health Metrics:")
            for metric in system_health:
                status_icon = "✓" if metric.status == "healthy" else "⚠" if metric.status == "warning" else "✗"
                print(f"  {status_icon} {metric.name}: {metric.value} {metric.unit} ({metric.status})")
        
        # Show alert summary
        alerts = metrics.get('alerts')
        if alerts:
            print(f"\nAlert Summary:")
            print(f"  Total alerts: {alerts.total_alerts}")
            print(f"  Critical: {alerts.critical_alerts}")
            print(f"  High: {alerts.high_alerts}")
            print(f"  Medium: {alerts.medium_alerts}")
            print(f"  Low: {alerts.low_alerts}")
            print(f"  Trend: {alerts.trend_24h}")
        
        # Show trends
        trends = metrics.get('trends', {})
        if trends:
            print(f"\nTrend Data Available:")
            for trend_name, trend_data in trends.items():
                if isinstance(trend_data, list):
                    print(f"  {trend_name}: {len(trend_data)} data points")
    else:
        print(f"Error: {metrics['error']}")

def example_export_formats():
    """Export formats example"""
    print("=== Export Formats Example ===")
    
    dashboard = create_dashboard_metrics(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    print("Generating exports...")
    
    # Prometheus format
    prometheus_metrics = dashboard.export_prometheus_metrics()
    print(f"\nPrometheus format:")
    print(f"  Lines: {len(prometheus_metrics.split('\\n'))}")
    print("  Sample metrics:")
    for line in prometheus_metrics.split('\\n')[:5]:
        if line and not line.startswith('#'):
            print(f"    {line}")
    
    # Grafana dashboard
    grafana_dashboard = dashboard.export_grafana_dashboard()
    if 'error' not in grafana_dashboard:
        panels = grafana_dashboard.get('dashboard', {}).get('panels', [])
        print(f"\nGrafana dashboard:")
        print(f"  Panels: {len(panels)}")
        for panel in panels:
            print(f"    - {panel['title']} ({panel['type']})")
    
    # JSON export
    json_metrics = dashboard.export_json_metrics()
    json_data = json.loads(json_metrics)
    if 'error' not in json_data:
        print(f"\nJSON export:")
        print(f"  Categories: {len(json_data.keys())}")
        for category in json_data.keys():
            if category != 'metadata':
                print(f"    - {category}")

def example_email_notifications():
    """Email notifications example (simulated)"""
    print("=== Email Notifications Example ===")
    
    # Create configuration with email settings
    config = MonitoringConfig(
        email_from="monitoring@yourcompany.com",
        email_password="your-app-password",  # Use app-specific password
        alert_recipients=["admin@yourcompany.com", "ops@yourcompany.com"],
        report_recipients=["management@yourcompany.com"]
    )
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        config=config
    )
    
    print("Email configuration:")
    print(f"  SMTP server: {config.smtp_server}:{config.smtp_port}")
    print(f"  From address: {config.email_from}")
    print(f"  Alert recipients: {len(config.alert_recipients or [])} addresses")
    print(f"  Report recipients: {len(config.report_recipients or [])} addresses")
    
    # Run monitoring to generate alerts
    result = monitor.run_full_monitoring()
    
    if result.get('alerts_triggered', 0) > 0:
        print(f"\nAlerts generated: {result['alerts_triggered']}")
        print("Email notifications would be sent for:")
        
        for alert in result.get('alerts', [])[:3]:
            print(f"  - {alert['severity'].upper()}: {alert['title']}")
    else:
        print("\nNo alerts generated - no email notifications needed")

def example_real_time_monitoring():
    """Real-time monitoring example"""
    print("=== Real-time Monitoring Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    dashboard = create_dashboard_metrics(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    print("Starting real-time monitoring (press Ctrl+C to stop)...")
    
    try:
        iteration = 0
        while iteration < 3:  # Run for 3 iterations for demo
            iteration += 1
            print(f"\n--- Monitoring Cycle {iteration} ---")
            
            # Get quick health metrics
            metrics = dashboard.get_dashboard_metrics()
            
            if 'error' not in metrics:
                # Show key metrics
                system_health = metrics.get('system_health', [])
                health_score = next((m.value for m in system_health if m.name == 'system_health_score'), 0)
                
                data_freshness = next((m.value for m in system_health if m.name == 'data_freshness'), 999)
                
                import_metrics = metrics.get('import_status', [])
                todays_imports = next((m.value for m in import_metrics if m.name == 'todays_imports'), 0)
                
                print(f"Health Score: {health_score:.1f}%")
                print(f"Data Freshness: {data_freshness:.1f} hours ago")
                print(f"Today's Imports: {todays_imports} records")
                
                # Check for alerts
                alerts = metrics.get('alerts')
                if alerts and alerts.total_alerts > 0:
                    print(f"⚠ Active Alerts: {alerts.total_alerts}")
                else:
                    print("✓ No active alerts")
            
            # Wait before next cycle
            if iteration < 3:
                print("Waiting 30 seconds for next cycle...")
                time.sleep(30)
    
    except KeyboardInterrupt:
        print("\nReal-time monitoring stopped")

def example_troubleshooting():
    """Troubleshooting example"""
    print("=== Troubleshooting Example ===")
    
    monitor = create_monitor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )
    
    print("Running comprehensive system diagnostics...")
    
    # Test database connectivity
    try:
        result = monitor.run_full_monitoring()
        print("✓ Database connectivity: OK")
    except Exception as e:
        print(f"✗ Database connectivity: FAILED ({e})")
        return
    
    # Check data freshness
    freshness = monitor.check_data_freshness()
    if freshness['status'] == 'completed':
        hours_old = freshness['hours_since_import']
        if hours_old < 25:
            print("✓ Data freshness: OK")
        else:
            print(f"⚠ Data freshness: WARNING (data is {hours_old:.1f} hours old)")
    else:
        print(f"✗ Data freshness: ERROR ({freshness.get('error', 'Unknown')})")
    
    # Check data quality
    quality = monitor.run_data_quality_checks()
    if quality['status'] == 'completed':
        score = quality['overall_quality_score']
        if score >= 90:
            print("✓ Data quality: EXCELLENT")
        elif score >= 70:
            print(f"⚠ Data quality: WARNING (score: {score:.1f}%)")
        else:
            print(f"✗ Data quality: POOR (score: {score:.1f}%)")
    else:
        print(f"✗ Data quality: ERROR ({quality.get('error', 'Unknown')})")
    
    # Check performance
    performance = monitor.monitor_performance()
    if performance['status'] == 'completed':
        print("✓ Performance monitoring: OK")
        
        # Show any performance issues
        metrics = performance.get('metrics', {})
        for metric_name, metric_data in metrics.items():
            if metric_data.get('alert_triggered', False):
                print(f"⚠ Performance issue: {metric_name}")
    else:
        print(f"✗ Performance monitoring: ERROR ({performance.get('error', 'Unknown')})")
    
    print("\nDiagnostics completed")

def main():
    """Run all examples"""
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("Error: Please set SUPABASE_URL and SUPABASE_KEY environment variables")
        sys.exit(1)
    
    examples = [
        example_basic_monitoring,
        example_custom_configuration,
        example_data_freshness_monitoring,
        example_price_anomaly_detection,
        example_data_quality_checks,
        example_performance_monitoring,
        example_automated_reporting,
        example_data_maintenance,
        example_dashboard_metrics,
        example_export_formats,
        example_email_notifications,
        example_troubleshooting
    ]
    
    print("Price History Monitoring System Examples")
    print("=" * 50)
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n{i}. Running {example.__name__}...")
            example()
            print("-" * 50)
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            print("-" * 50)
    
    print("\nAll examples completed!")

if __name__ == "__main__":
    main()