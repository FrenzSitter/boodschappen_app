#!/usr/bin/env python3
"""
Data Validation and Monitoring Script
=====================================

This script validates data integrity, monitors freshness, and generates
health reports for the CheckjeBon import system.

Features:
- Data freshness validation
- Integrity checks (missing prices, invalid formats)
- Record count comparison
- Daily health reports
- Price change detection
- Automated alerting

Author: Generated for boodschappen_app
Date: 2025-01-09
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import argparse
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
    import requests
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Run: pip install supabase requests")
    sys.exit(1)

# Configuration
VALIDATION_LOG_FILE = "logs/data_validation.log"
HEALTH_REPORT_DIR = "logs/health_reports"
VALIDATION_CONFIG_FILE = "automation/validation_config.json"
PRICE_CHANGE_THRESHOLD = 0.20  # 20% price change threshold
FRESHNESS_THRESHOLD_HOURS = 48  # Data older than 48 hours is stale

@dataclass
class ValidationResult:
    """Results of data validation"""
    check_name: str
    status: str  # PASS, WARN, FAIL
    message: str
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

@dataclass
class HealthReport:
    """Daily health report structure"""
    date: str
    total_checks: int
    passed_checks: int
    warning_checks: int
    failed_checks: int
    data_freshness: Dict[str, Any]
    integrity_checks: Dict[str, Any]
    record_counts: Dict[str, Any]
    price_changes: Dict[str, Any]
    alerts: List[str]
    recommendations: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

class DataValidator:
    """Main data validation and monitoring class"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.logger = self._setup_logging()
        self.validation_results = []
        self.alerts = []
        self.recommendations = []
        
        # Initialize Supabase client
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.logger.info("✅ Connected to Supabase")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise
        
        # Load validation configuration
        self.config = self._load_validation_config()
        
        # Create necessary directories
        os.makedirs(HEALTH_REPORT_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(VALIDATION_LOG_FILE), exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('data_validator')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(VALIDATION_LOG_FILE)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers if not already added
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _load_validation_config(self) -> Dict:
        """Load validation configuration"""
        default_config = {
            "freshness_threshold_hours": FRESHNESS_THRESHOLD_HOURS,
            "price_change_threshold": PRICE_CHANGE_THRESHOLD,
            "min_record_count": 100,
            "max_record_count": 1000000,
            "required_fields": ["name", "price", "supermarket_id"],
            "price_range": {"min": 0.01, "max": 1000.00},
            "alert_thresholds": {
                "missing_prices_pct": 5.0,
                "invalid_formats_pct": 2.0,
                "record_count_change_pct": 20.0,
                "stale_data_pct": 10.0
            }
        }
        
        if os.path.exists(VALIDATION_CONFIG_FILE):
            try:
                with open(VALIDATION_CONFIG_FILE, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    self.logger.info(f"Loaded validation config from {VALIDATION_CONFIG_FILE}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}, using defaults")
        
        return default_config
    
    def _add_result(self, check_name: str, status: str, message: str, details: Dict = None):
        """Add validation result"""
        result = ValidationResult(
            check_name=check_name,
            status=status,
            message=message,
            details=details or {}
        )
        self.validation_results.append(result)
        
        # Log the result
        if status == "PASS":
            self.logger.info(f"✅ {check_name}: {message}")
        elif status == "WARN":
            self.logger.warning(f"⚠️  {check_name}: {message}")
        elif status == "FAIL":
            self.logger.error(f"❌ {check_name}: {message}")
            self.alerts.append(f"{check_name}: {message}")
    
    def check_data_freshness(self) -> None:
        """Check data freshness across different tables"""
        self.logger.info("🔍 Checking data freshness...")
        
        tables_to_check = [
            ("products", "updated_at"),
            ("product_prices", "last_updated"),
            ("supermarkets", "last_data_update")
        ]
        
        freshness_results = {}
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=self.config["freshness_threshold_hours"])
        
        for table_name, timestamp_field in tables_to_check:
            try:
                # Get latest timestamp
                response = self.supabase.table(table_name).select(timestamp_field).order(timestamp_field, desc=True).limit(1).execute()
                
                if response.data:
                    latest_update = response.data[0][timestamp_field]
                    latest_datetime = datetime.fromisoformat(latest_update.replace('Z', '+00:00'))
                    
                    # Check if data is fresh
                    is_fresh = latest_datetime > threshold_time
                    hours_old = (datetime.now(timezone.utc) - latest_datetime).total_seconds() / 3600
                    
                    freshness_results[table_name] = {
                        "latest_update": latest_update,
                        "hours_old": round(hours_old, 2),
                        "is_fresh": is_fresh
                    }
                    
                    if is_fresh:
                        self._add_result(
                            f"Data Freshness - {table_name}",
                            "PASS",
                            f"Data is fresh ({hours_old:.1f} hours old)",
                            freshness_results[table_name]
                        )
                    else:
                        self._add_result(
                            f"Data Freshness - {table_name}",
                            "WARN",
                            f"Data is stale ({hours_old:.1f} hours old)",
                            freshness_results[table_name]
                        )
                        self.recommendations.append(f"Consider investigating why {table_name} data is {hours_old:.1f} hours old")
                else:
                    self._add_result(
                        f"Data Freshness - {table_name}",
                        "FAIL",
                        f"No data found in {table_name} table",
                        {"table": table_name}
                    )
                    
            except Exception as e:
                self._add_result(
                    f"Data Freshness - {table_name}",
                    "FAIL",
                    f"Error checking freshness: {str(e)}",
                    {"table": table_name, "error": str(e)}
                )
        
        return freshness_results
    
    def check_data_integrity(self) -> Dict:
        """Check data integrity - missing prices, invalid formats, etc."""
        self.logger.info("🔍 Checking data integrity...")
        
        integrity_results = {}
        
        # Check products table
        try:
            # Get total product count
            total_products = self.supabase.table("products").select("id", count="exact").execute()
            total_count = total_products.count
            
            # Check for missing names
            missing_names = self.supabase.table("products").select("id", count="exact").is_("name", "null").execute()
            missing_names_count = missing_names.count
            
            # Check for missing or invalid prices
            missing_prices = self.supabase.table("product_prices").select("id", count="exact").is_("price", "null").execute()
            missing_prices_count = missing_prices.count
            
            # Check for invalid price ranges
            invalid_prices = self.supabase.table("product_prices").select("id", count="exact").or_(
                f"price.lt.{self.config['price_range']['min']},price.gt.{self.config['price_range']['max']}"
            ).execute()
            invalid_prices_count = invalid_prices.count
            
            # Check for products without prices
            products_without_prices = self.supabase.table("products").select("id", count="exact").not_.in_(
                "id", 
                self.supabase.table("product_prices").select("product_id").execute().data
            ).execute()
            products_without_prices_count = products_without_prices.count if products_without_prices.data else 0
            
            integrity_results = {
                "total_products": total_count,
                "missing_names": missing_names_count,
                "missing_prices": missing_prices_count,
                "invalid_prices": invalid_prices_count,
                "products_without_prices": products_without_prices_count,
                "missing_names_pct": (missing_names_count / total_count * 100) if total_count > 0 else 0,
                "missing_prices_pct": (missing_prices_count / total_count * 100) if total_count > 0 else 0,
                "invalid_prices_pct": (invalid_prices_count / total_count * 100) if total_count > 0 else 0,
                "products_without_prices_pct": (products_without_prices_count / total_count * 100) if total_count > 0 else 0
            }
            
            # Validate against thresholds
            alerts = self.config["alert_thresholds"]
            
            # Check missing names
            if integrity_results["missing_names_pct"] > alerts["invalid_formats_pct"]:
                self._add_result(
                    "Data Integrity - Missing Names",
                    "FAIL",
                    f"High percentage of missing names: {integrity_results['missing_names_pct']:.1f}%",
                    {"missing_names": missing_names_count, "percentage": integrity_results["missing_names_pct"]}
                )
            else:
                self._add_result(
                    "Data Integrity - Missing Names",
                    "PASS",
                    f"Missing names within acceptable range: {integrity_results['missing_names_pct']:.1f}%",
                    {"missing_names": missing_names_count, "percentage": integrity_results["missing_names_pct"]}
                )
            
            # Check missing prices
            if integrity_results["missing_prices_pct"] > alerts["missing_prices_pct"]:
                self._add_result(
                    "Data Integrity - Missing Prices",
                    "FAIL",
                    f"High percentage of missing prices: {integrity_results['missing_prices_pct']:.1f}%",
                    {"missing_prices": missing_prices_count, "percentage": integrity_results["missing_prices_pct"]}
                )
            else:
                self._add_result(
                    "Data Integrity - Missing Prices",
                    "PASS",
                    f"Missing prices within acceptable range: {integrity_results['missing_prices_pct']:.1f}%",
                    {"missing_prices": missing_prices_count, "percentage": integrity_results["missing_prices_pct"]}
                )
            
            # Check invalid prices
            if integrity_results["invalid_prices_pct"] > alerts["invalid_formats_pct"]:
                self._add_result(
                    "Data Integrity - Invalid Prices",
                    "FAIL",
                    f"High percentage of invalid prices: {integrity_results['invalid_prices_pct']:.1f}%",
                    {"invalid_prices": invalid_prices_count, "percentage": integrity_results["invalid_prices_pct"]}
                )
            else:
                self._add_result(
                    "Data Integrity - Invalid Prices",
                    "PASS",
                    f"Invalid prices within acceptable range: {integrity_results['invalid_prices_pct']:.1f}%",
                    {"invalid_prices": invalid_prices_count, "percentage": integrity_results["invalid_prices_pct"]}
                )
            
            # Check products without prices
            if integrity_results["products_without_prices_pct"] > alerts["missing_prices_pct"]:
                self._add_result(
                    "Data Integrity - Products Without Prices",
                    "WARN",
                    f"Products without prices: {integrity_results['products_without_prices_pct']:.1f}%",
                    {"products_without_prices": products_without_prices_count, "percentage": integrity_results["products_without_prices_pct"]}
                )
                self.recommendations.append("Consider investigating why some products don't have prices")
            else:
                self._add_result(
                    "Data Integrity - Products Without Prices",
                    "PASS",
                    f"Products without prices within acceptable range: {integrity_results['products_without_prices_pct']:.1f}%",
                    {"products_without_prices": products_without_prices_count, "percentage": integrity_results["products_without_prices_pct"]}
                )
            
        except Exception as e:
            self._add_result(
                "Data Integrity Check",
                "FAIL",
                f"Error during integrity check: {str(e)}",
                {"error": str(e)}
            )
            integrity_results = {"error": str(e)}
        
        return integrity_results
    
    def compare_record_counts(self) -> Dict:
        """Compare record counts between current and previous runs"""
        self.logger.info("🔍 Comparing record counts...")
        
        record_counts = {}
        
        try:
            # Get current counts
            current_counts = {}
            tables = ["products", "product_prices", "supermarkets", "categories"]
            
            for table in tables:
                response = self.supabase.table(table).select("id", count="exact").execute()
                current_counts[table] = response.count
            
            # Load previous counts (if exists)
            counts_file = f"{HEALTH_REPORT_DIR}/record_counts.json"
            previous_counts = {}
            
            if os.path.exists(counts_file):
                try:
                    with open(counts_file, 'r') as f:
                        previous_counts = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Failed to load previous counts: {e}")
            
            # Compare counts
            for table in tables:
                current = current_counts.get(table, 0)
                previous = previous_counts.get(table, 0)
                
                if previous > 0:
                    change = current - previous
                    change_pct = (change / previous) * 100
                    
                    record_counts[table] = {
                        "current": current,
                        "previous": previous,
                        "change": change,
                        "change_pct": change_pct
                    }
                    
                    # Check for significant changes
                    if abs(change_pct) > self.config["alert_thresholds"]["record_count_change_pct"]:
                        self._add_result(
                            f"Record Count - {table}",
                            "WARN",
                            f"Significant change in {table}: {change:+d} records ({change_pct:+.1f}%)",
                            record_counts[table]
                        )
                        self.recommendations.append(f"Investigate {change_pct:+.1f}% change in {table} record count")
                    else:
                        self._add_result(
                            f"Record Count - {table}",
                            "PASS",
                            f"{table} count change within normal range: {change:+d} records ({change_pct:+.1f}%)",
                            record_counts[table]
                        )
                else:
                    record_counts[table] = {
                        "current": current,
                        "previous": 0,
                        "change": current,
                        "change_pct": 0
                    }
                    
                    self._add_result(
                        f"Record Count - {table}",
                        "PASS",
                        f"{table} baseline established: {current} records",
                        record_counts[table]
                    )
            
            # Save current counts for next run
            with open(counts_file, 'w') as f:
                json.dump(current_counts, f, indent=2)
            
            # Check minimum record count thresholds
            min_count = self.config["min_record_count"]
            if current_counts.get("products", 0) < min_count:
                self._add_result(
                    "Record Count - Minimum Threshold",
                    "FAIL",
                    f"Product count below minimum threshold: {current_counts['products']} < {min_count}",
                    {"current": current_counts["products"], "minimum": min_count}
                )
            
        except Exception as e:
            self._add_result(
                "Record Count Comparison",
                "FAIL",
                f"Error comparing record counts: {str(e)}",
                {"error": str(e)}
            )
            record_counts = {"error": str(e)}
        
        return record_counts
    
    def detect_price_changes(self) -> Dict:
        """Detect significant price changes"""
        self.logger.info("🔍 Detecting significant price changes...")
        
        price_changes = {}
        
        try:
            # Get recent price changes from price_history table
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            response = self.supabase.table("price_history").select(
                "product_id, price, price_change, price_change_percentage, recorded_at"
            ).gte("recorded_at", yesterday.isoformat()).order("recorded_at", desc=True).execute()
            
            recent_changes = response.data
            
            if recent_changes:
                # Analyze price changes
                significant_changes = []
                threshold = self.config["price_change_threshold"] * 100  # Convert to percentage
                
                for change in recent_changes:
                    if change["price_change_percentage"] and abs(change["price_change_percentage"]) > threshold:
                        significant_changes.append(change)
                
                price_changes = {
                    "total_changes": len(recent_changes),
                    "significant_changes": len(significant_changes),
                    "significant_changes_pct": (len(significant_changes) / len(recent_changes) * 100) if recent_changes else 0,
                    "largest_increases": sorted(
                        [c for c in significant_changes if c["price_change_percentage"] > 0],
                        key=lambda x: x["price_change_percentage"],
                        reverse=True
                    )[:5],
                    "largest_decreases": sorted(
                        [c for c in significant_changes if c["price_change_percentage"] < 0],
                        key=lambda x: x["price_change_percentage"]
                    )[:5]
                }
                
                # Create validation results
                if len(significant_changes) > 0:
                    self._add_result(
                        "Price Changes",
                        "WARN",
                        f"Detected {len(significant_changes)} significant price changes (>{threshold}%)",
                        price_changes
                    )
                    
                    if len(significant_changes) > len(recent_changes) * 0.1:  # More than 10% of changes are significant
                        self.recommendations.append("High number of significant price changes detected - investigate data source")
                else:
                    self._add_result(
                        "Price Changes",
                        "PASS",
                        f"No significant price changes detected in {len(recent_changes)} price updates",
                        price_changes
                    )
            else:
                self._add_result(
                    "Price Changes",
                    "PASS",
                    "No recent price changes found",
                    {"total_changes": 0}
                )
                price_changes = {"total_changes": 0}
            
        except Exception as e:
            self._add_result(
                "Price Change Detection",
                "FAIL",
                f"Error detecting price changes: {str(e)}",
                {"error": str(e)}
            )
            price_changes = {"error": str(e)}
        
        return price_changes
    
    def generate_health_report(self) -> HealthReport:
        """Generate comprehensive health report"""
        self.logger.info("📊 Generating health report...")
        
        # Count results by status
        passed = len([r for r in self.validation_results if r.status == "PASS"])
        warnings = len([r for r in self.validation_results if r.status == "WARN"])
        failed = len([r for r in self.validation_results if r.status == "FAIL"])
        
        # Get individual check results
        freshness_results = self.check_data_freshness()
        integrity_results = self.check_data_integrity()
        record_count_results = self.compare_record_counts()
        price_change_results = self.detect_price_changes()
        
        # Create health report
        report = HealthReport(
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            total_checks=len(self.validation_results),
            passed_checks=passed,
            warning_checks=warnings,
            failed_checks=failed,
            data_freshness=freshness_results,
            integrity_checks=integrity_results,
            record_counts=record_count_results,
            price_changes=price_change_results,
            alerts=self.alerts,
            recommendations=self.recommendations
        )
        
        return report
    
    def save_health_report(self, report: HealthReport) -> str:
        """Save health report to file"""
        report_file = f"{HEALTH_REPORT_DIR}/health_report_{report.date}.json"
        
        # Convert to dict for JSON serialization
        report_dict = asdict(report)
        report_dict["timestamp"] = report.timestamp.isoformat()
        
        # Save detailed results
        report_dict["validation_results"] = [
            {
                "check_name": r.check_name,
                "status": r.status,
                "message": r.message,
                "details": r.details,
                "timestamp": r.timestamp.isoformat()
            }
            for r in self.validation_results
        ]
        
        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        self.logger.info(f"Health report saved to: {report_file}")
        return report_file
    
    def generate_html_report(self, report: HealthReport) -> str:
        """Generate HTML version of health report"""
        html_file = f"{HEALTH_REPORT_DIR}/health_report_{report.date}.html"
        
        # Status colors
        status_colors = {
            "PASS": "#28a745",
            "WARN": "#ffc107",
            "FAIL": "#dc3545"
        }
        
        # Generate HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CheckjeBon Health Report - {report.date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 15px; background-color: #e9ecef; border-radius: 5px; }}
        .metric h3 {{ margin: 0; color: #495057; }}
        .metric .value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .section {{ margin: 20px 0; }}
        .section h2 {{ color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }}
        .check-result {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
        .check-result.PASS {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
        .check-result.WARN {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
        .check-result.FAIL {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
        .alert {{ background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        .recommendation {{ background-color: #d1ecf1; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        .table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .table th, .table td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; }}
        .table th {{ background-color: #e9ecef; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CheckjeBon Health Report</h1>
        <p><strong>Date:</strong> {report.date}</p>
        <p><strong>Generated:</strong> {report.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Checks</h3>
            <div class="value">{report.total_checks}</div>
        </div>
        <div class="metric">
            <h3>Passed</h3>
            <div class="value" style="color: #28a745;">{report.passed_checks}</div>
        </div>
        <div class="metric">
            <h3>Warnings</h3>
            <div class="value" style="color: #ffc107;">{report.warning_checks}</div>
        </div>
        <div class="metric">
            <h3>Failed</h3>
            <div class="value" style="color: #dc3545;">{report.failed_checks}</div>
        </div>
    </div>

    <div class="section">
        <h2>Validation Results</h2>
        """
        
        for result in self.validation_results:
            html_content += f"""
        <div class="check-result {result.status}">
            <strong>{result.check_name}:</strong> {result.message}
            <small style="float: right;">{result.timestamp.strftime("%H:%M:%S")}</small>
        </div>
            """
        
        html_content += """
    </div>
        """
        
        # Add alerts section
        if report.alerts:
            html_content += """
    <div class="section">
        <h2>Alerts</h2>
            """
            for alert in report.alerts:
                html_content += f'<div class="alert">{alert}</div>'
            html_content += """
    </div>
            """
        
        # Add recommendations section
        if report.recommendations:
            html_content += """
    <div class="section">
        <h2>Recommendations</h2>
            """
            for rec in report.recommendations:
                html_content += f'<div class="recommendation">{rec}</div>'
            html_content += """
    </div>
            """
        
        # Add data summary tables
        html_content += f"""
    <div class="section">
        <h2>Data Summary</h2>
        
        <h3>Record Counts</h3>
        <table class="table">
            <thead>
                <tr>
                    <th>Table</th>
                    <th>Current Count</th>
                    <th>Previous Count</th>
                    <th>Change</th>
                    <th>Change %</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for table, data in report.record_counts.items():
            if isinstance(data, dict) and "current" in data:
                html_content += f"""
                <tr>
                    <td>{table}</td>
                    <td>{data['current']:,}</td>
                    <td>{data['previous']:,}</td>
                    <td>{data['change']:+,}</td>
                    <td>{data['change_pct']:+.1f}%</td>
                </tr>
                """
        
        html_content += """
            </tbody>
        </table>
    </div>

</body>
</html>
        """
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report saved to: {html_file}")
        return html_file
    
    def send_alert_email(self, report: HealthReport) -> bool:
        """Send alert email if there are failures or critical issues"""
        if not report.alerts and report.failed_checks == 0:
            return True  # No alerts to send
        
        # Check if email is configured
        if not os.getenv('EMAIL_ENABLED', 'false').lower() == 'true':
            self.logger.info("Email alerts disabled")
            return True
        
        try:
            # Import email notification module
            from email_notifications import EmailNotifier
            
            notifier = EmailNotifier()
            
            # Prepare email content
            subject = f"CheckjeBon Data Validation Alert - {report.date}"
            
            body = f"""
Data Validation Alert Report
===========================

Date: {report.date}
Time: {report.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

Summary:
- Total Checks: {report.total_checks}
- Passed: {report.passed_checks}
- Warnings: {report.warning_checks}
- Failed: {report.failed_checks}

Alerts:
"""
            
            for alert in report.alerts:
                body += f"- {alert}\n"
            
            body += "\nRecommendations:\n"
            for rec in report.recommendations:
                body += f"- {rec}\n"
            
            body += f"\nFull report available in: {HEALTH_REPORT_DIR}/health_report_{report.date}.html"
            
            # Send email
            email_to = os.getenv('EMAIL_TO', '').split(',')
            return notifier.send_email(
                to_emails=email_to,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send alert email: {e}")
            return False
    
    def run_validation(self) -> HealthReport:
        """Run complete validation process"""
        self.logger.info("🚀 Starting data validation...")
        
        # Clear previous results
        self.validation_results = []
        self.alerts = []
        self.recommendations = []
        
        # Run all validation checks
        try:
            self.check_data_freshness()
            self.check_data_integrity()
            self.compare_record_counts()
            self.detect_price_changes()
            
            # Generate health report
            report = self.generate_health_report()
            
            # Save reports
            json_file = self.save_health_report(report)
            html_file = self.generate_html_report(report)
            
            # Send alerts if needed
            if report.alerts or report.failed_checks > 0:
                self.send_alert_email(report)
            
            self.logger.info(f"✅ Data validation completed. Reports saved to {json_file} and {html_file}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Data validation failed: {e}")
            raise

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='CheckjeBon Data Validation and Monitoring')
    parser.add_argument('--freshness', action='store_true', help='Check data freshness only')
    parser.add_argument('--integrity', action='store_true', help='Check data integrity only')
    parser.add_argument('--counts', action='store_true', help='Compare record counts only')
    parser.add_argument('--prices', action='store_true', help='Detect price changes only')
    parser.add_argument('--report', action='store_true', help='Generate health report only')
    parser.add_argument('--config', help='Custom config file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        sys.exit(1)
    
    try:
        # Initialize validator
        validator = DataValidator(supabase_url, supabase_key)
        
        # Run specific checks or full validation
        if args.freshness:
            validator.check_data_freshness()
        elif args.integrity:
            validator.check_data_integrity()
        elif args.counts:
            validator.compare_record_counts()
        elif args.prices:
            validator.detect_price_changes()
        elif args.report:
            report = validator.generate_health_report()
            validator.save_health_report(report)
            validator.generate_html_report(report)
        else:
            # Run full validation
            report = validator.run_validation()
            
            # Exit with appropriate code
            if report.failed_checks > 0:
                print(f"❌ Validation failed with {report.failed_checks} failures")
                sys.exit(1)
            elif report.warning_checks > 0:
                print(f"⚠️  Validation completed with {report.warning_checks} warnings")
                sys.exit(0)
            else:
                print("✅ All validations passed")
                sys.exit(0)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()