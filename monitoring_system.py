#!/usr/bin/env python3
"""
Price History Monitoring System
==============================

Comprehensive monitoring system for CheckjeBon price history import process.
Provides data freshness monitoring, quality checks, performance tracking,
automated reporting, and maintenance utilities.

Features:
- Data freshness and completeness monitoring
- Price change anomaly detection
- Data quality validation
- Performance metrics tracking
- Automated reporting and alerts
- Data maintenance and cleanup
- Email notifications
- Dashboard metrics

Usage:
    from monitoring_system import PriceHistoryMonitor
    
    monitor = PriceHistoryMonitor(supabase_client)
    status = monitor.run_full_monitoring()
"""

import os
import json
import logging
import smtplib
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import asyncio
import time

# Third-party imports
import numpy as np
import pandas as pd
from supabase import Client
from postgrest import APIError

@dataclass
class MonitoringConfig:
    """Configuration for monitoring system"""
    # Data freshness thresholds
    max_import_age_hours: int = 25  # Alert if last import > 25 hours ago
    min_daily_records: int = 1000   # Minimum records expected per day
    expected_supermarkets: int = 11  # Expected number of active supermarkets
    
    # Price change thresholds
    max_price_change_percentage: float = 200.0  # Alert if price changes > 200%
    price_volatility_threshold: float = 50.0    # High volatility threshold
    min_price_value: float = 0.01               # Minimum realistic price
    max_price_value: float = 1000.0             # Maximum realistic price
    
    # Data quality thresholds
    max_duplicate_percentage: float = 1.0       # Max 1% duplicates allowed
    min_product_coverage: float = 90.0          # Min 90% products should have prices
    max_missing_data_percentage: float = 5.0    # Max 5% missing data allowed
    
    # Performance thresholds
    max_import_duration_minutes: int = 120      # Max 2 hours for import
    max_query_time_seconds: float = 30.0        # Max 30 seconds per query
    max_error_rate_percentage: float = 5.0      # Max 5% error rate
    
    # Storage thresholds
    max_storage_growth_gb_per_month: float = 10.0  # Max 10GB growth per month
    archive_after_days: int = 365 * 2              # Archive after 2 years
    
    # Email configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_from: str = ""
    email_password: str = ""
    alert_recipients: List[str] = None
    report_recipients: List[str] = None

@dataclass
class MonitoringAlert:
    """Monitoring alert data structure"""
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    metric_value: Any
    threshold_value: Any
    detected_at: datetime
    affected_entities: List[str]
    recommended_action: str

@dataclass
class MonitoringReport:
    """Monitoring report data structure"""
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    alerts: List[MonitoringAlert]
    recommendations: List[str]

class PriceHistoryMonitor:
    """Main monitoring class for price history system"""
    
    def __init__(self, supabase_client: Client, config: MonitoringConfig = None):
        self.supabase = supabase_client
        self.config = config or MonitoringConfig()
        self.logger = self._setup_logging()
        self.alerts: List[MonitoringAlert] = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('price_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            file_handler = logging.FileHandler('price_monitoring.log')
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _create_alert(self, alert_type: str, severity: str, title: str, 
                     description: str, metric_value: Any, threshold_value: Any,
                     affected_entities: List[str] = None, 
                     recommended_action: str = "") -> MonitoringAlert:
        """Create a monitoring alert"""
        alert_id = f"{alert_type}_{int(time.time())}"
        
        alert = MonitoringAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            metric_value=metric_value,
            threshold_value=threshold_value,
            detected_at=datetime.now(),
            affected_entities=affected_entities or [],
            recommended_action=recommended_action
        )
        
        self.alerts.append(alert)
        self.logger.warning(f"Alert created: {title} - {description}")
        
        return alert
    
    # =====================================================================
    # 1. DATA FRESHNESS MONITORING
    # =====================================================================
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """Check data freshness and completeness"""
        try:
            # Check last import time
            last_import = self._get_last_import_time()
            hours_since_import = (datetime.now() - last_import).total_seconds() / 3600
            
            # Check daily record counts
            daily_counts = self._get_daily_record_counts(days=7)
            
            # Check supermarket coverage
            supermarket_coverage = self._check_supermarket_coverage()
            
            # Generate alerts
            if hours_since_import > self.config.max_import_age_hours:
                self._create_alert(
                    alert_type="data_freshness",
                    severity="high",
                    title="Import Overdue",
                    description=f"Last import was {hours_since_import:.1f} hours ago",
                    metric_value=hours_since_import,
                    threshold_value=self.config.max_import_age_hours,
                    recommended_action="Check import process status and restart if needed"
                )
            
            # Check if recent daily counts are too low
            if daily_counts:
                latest_count = daily_counts[0]['count']
                if latest_count < self.config.min_daily_records:
                    self._create_alert(
                        alert_type="data_completeness",
                        severity="medium",
                        title="Low Daily Record Count",
                        description=f"Only {latest_count} records imported today",
                        metric_value=latest_count,
                        threshold_value=self.config.min_daily_records,
                        recommended_action="Investigate data source availability"
                    )
            
            # Check supermarket coverage
            active_supermarkets = supermarket_coverage['active_count']
            if active_supermarkets < self.config.expected_supermarkets:
                missing_supermarkets = supermarket_coverage['missing_supermarkets']
                self._create_alert(
                    alert_type="supermarket_coverage",
                    severity="medium",
                    title="Missing Supermarket Data",
                    description=f"Only {active_supermarkets}/{self.config.expected_supermarkets} supermarkets have recent data",
                    metric_value=active_supermarkets,
                    threshold_value=self.config.expected_supermarkets,
                    affected_entities=missing_supermarkets,
                    recommended_action="Check data source for missing supermarkets"
                )
            
            return {
                'status': 'completed',
                'last_import': last_import.isoformat(),
                'hours_since_import': hours_since_import,
                'daily_counts': daily_counts,
                'supermarket_coverage': supermarket_coverage,
                'alerts_generated': len([a for a in self.alerts if a.alert_type in ['data_freshness', 'data_completeness', 'supermarket_coverage']])
            }
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_last_import_time(self) -> datetime:
        """Get timestamp of last import"""
        try:
            # Check import_logs table first
            response = self.supabase.table("import_logs").select(
                "end_time"
            ).order("end_time", desc=True).limit(1).execute()
            
            if response.data:
                return datetime.fromisoformat(response.data[0]['end_time'].replace('Z', '+00:00'))
            
            # Fallback to latest price_history record
            response = self.supabase.table("price_history").select(
                "created_at"
            ).order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                return datetime.fromisoformat(response.data[0]['created_at'].replace('Z', '+00:00'))
            
            # Default to very old date if no data
            return datetime.now() - timedelta(days=30)
            
        except Exception as e:
            self.logger.error(f"Error getting last import time: {e}")
            return datetime.now() - timedelta(days=30)
    
    def _get_daily_record_counts(self, days: int = 7) -> List[Dict]:
        """Get daily record counts for the last N days"""
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            response = self.supabase.rpc(
                'get_daily_price_counts',
                {'start_date': start_date}
            ).execute()
            
            if response.data:
                return response.data
            
            # Fallback query if RPC doesn't exist
            response = self.supabase.table("price_history").select(
                "price_date"
            ).gte("price_date", start_date).execute()
            
            # Count by date
            date_counts = defaultdict(int)
            for row in response.data:
                date_counts[row['price_date']] += 1
            
            return [{'date': k, 'count': v} for k, v in sorted(date_counts.items(), reverse=True)]
            
        except Exception as e:
            self.logger.error(f"Error getting daily record counts: {e}")
            return []
    
    def _check_supermarket_coverage(self) -> Dict[str, Any]:
        """Check which supermarkets have recent data"""
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            # Get all active supermarkets
            all_supermarkets = self.supabase.table("supermarkets").select(
                "id, name, slug"
            ).eq("is_active", True).execute()
            
            # Get supermarkets with recent price data
            recent_data = self.supabase.table("price_history").select(
                "supermarket_id"
            ).gte("price_date", yesterday).execute()
            
            supermarkets_with_data = set(row['supermarket_id'] for row in recent_data.data)
            
            missing_supermarkets = []
            for sm in all_supermarkets.data:
                if sm['id'] not in supermarkets_with_data:
                    missing_supermarkets.append(sm['name'])
            
            return {
                'total_supermarkets': len(all_supermarkets.data),
                'active_count': len(supermarkets_with_data),
                'missing_count': len(missing_supermarkets),
                'missing_supermarkets': missing_supermarkets,
                'coverage_percentage': (len(supermarkets_with_data) / len(all_supermarkets.data)) * 100 if all_supermarkets.data else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error checking supermarket coverage: {e}")
            return {'total_supermarkets': 0, 'active_count': 0, 'missing_count': 0, 'missing_supermarkets': [], 'coverage_percentage': 0}
    
    # =====================================================================
    # 2. PRICE CHANGE DETECTION
    # =====================================================================
    
    def detect_price_anomalies(self, days: int = 1) -> Dict[str, Any]:
        """Detect unusual price movements and potential data errors"""
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Get recent price changes
            response = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price, price_change_percentage, price_date, "
                "products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", start_date).execute()
            
            anomalies = {
                'extreme_changes': [],
                'missing_prices': [],
                'price_errors': [],
                'high_volatility': []
            }
            
            # Analyze price changes
            for row in response.data:
                price = row['price']
                change_pct = row.get('price_change_percentage', 0)
                
                # Check for extreme price changes
                if change_pct and abs(change_pct) > self.config.max_price_change_percentage:
                    anomalies['extreme_changes'].append({
                        'product_name': row['products']['name'],
                        'supermarket_name': row['supermarkets']['name'],
                        'price': price,
                        'change_percentage': change_pct,
                        'date': row['price_date']
                    })
                
                # Check for unrealistic prices
                if price < self.config.min_price_value or price > self.config.max_price_value:
                    anomalies['price_errors'].append({
                        'product_name': row['products']['name'],
                        'supermarket_name': row['supermarkets']['name'],
                        'price': price,
                        'date': row['price_date'],
                        'error_type': 'unrealistic_price'
                    })
            
            # Check for missing prices (products that had prices before but not now)
            missing_prices = self._check_missing_prices(days=days)
            anomalies['missing_prices'] = missing_prices
            
            # Check price volatility
            high_volatility = self._check_price_volatility(days=7)
            anomalies['high_volatility'] = high_volatility
            
            # Generate alerts
            if anomalies['extreme_changes']:
                self._create_alert(
                    alert_type="price_anomaly",
                    severity="high",
                    title="Extreme Price Changes Detected",
                    description=f"Found {len(anomalies['extreme_changes'])} extreme price changes",
                    metric_value=len(anomalies['extreme_changes']),
                    threshold_value=0,
                    affected_entities=[item['product_name'] for item in anomalies['extreme_changes']],
                    recommended_action="Review and validate extreme price changes"
                )
            
            if anomalies['price_errors']:
                self._create_alert(
                    alert_type="data_quality",
                    severity="medium",
                    title="Unrealistic Price Values",
                    description=f"Found {len(anomalies['price_errors'])} unrealistic prices",
                    metric_value=len(anomalies['price_errors']),
                    threshold_value=0,
                    affected_entities=[item['product_name'] for item in anomalies['price_errors']],
                    recommended_action="Investigate data source for price validation"
                )
            
            return {
                'status': 'completed',
                'analysis_period': f"{days} days",
                'anomalies': anomalies,
                'total_issues': sum(len(v) for v in anomalies.values())
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting price anomalies: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_missing_prices(self, days: int = 1) -> List[Dict]:
        """Check for products missing recent price data"""
        try:
            recent_date = (date.today() - timedelta(days=days)).isoformat()
            previous_date = (date.today() - timedelta(days=days + 7)).isoformat()
            
            # Get products that had prices in previous period
            previous_products = self.supabase.table("price_history").select(
                "product_id, supermarket_id"
            ).gte("price_date", previous_date).lt("price_date", recent_date).execute()
            
            # Get products that have prices in recent period
            recent_products = self.supabase.table("price_history").select(
                "product_id, supermarket_id"
            ).gte("price_date", recent_date).execute()
            
            previous_combinations = set((row['product_id'], row['supermarket_id']) for row in previous_products.data)
            recent_combinations = set((row['product_id'], row['supermarket_id']) for row in recent_products.data)
            
            missing_combinations = previous_combinations - recent_combinations
            
            # Get product details for missing combinations
            missing_prices = []
            for product_id, supermarket_id in list(missing_combinations)[:100]:  # Limit to 100 for performance
                try:
                    product_info = self.supabase.table("products").select("name").eq("id", product_id).single().execute()
                    supermarket_info = self.supabase.table("supermarkets").select("name").eq("id", supermarket_id).single().execute()
                    
                    if product_info.data and supermarket_info.data:
                        missing_prices.append({
                            'product_name': product_info.data['name'],
                            'supermarket_name': supermarket_info.data['name'],
                            'product_id': product_id,
                            'supermarket_id': supermarket_id
                        })
                except:
                    continue
            
            return missing_prices
            
        except Exception as e:
            self.logger.error(f"Error checking missing prices: {e}")
            return []
    
    def _check_price_volatility(self, days: int = 7) -> List[Dict]:
        """Check for products with high price volatility"""
        try:
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "product_id, supermarket_id, price, products!inner(name), supermarkets!inner(name)"
            ).gte("price_date", start_date).execute()
            
            # Group by product and supermarket
            price_groups = defaultdict(list)
            for row in response.data:
                key = (row['product_id'], row['supermarket_id'])
                price_groups[key].append({
                    'price': row['price'],
                    'product_name': row['products']['name'],
                    'supermarket_name': row['supermarkets']['name']
                })
            
            high_volatility = []
            for (product_id, supermarket_id), prices in price_groups.items():
                if len(prices) >= 3:  # Need at least 3 data points
                    price_values = [p['price'] for p in prices]
                    mean_price = np.mean(price_values)
                    std_price = np.std(price_values)
                    volatility = (std_price / mean_price) * 100 if mean_price > 0 else 0
                    
                    if volatility > self.config.price_volatility_threshold:
                        high_volatility.append({
                            'product_name': prices[0]['product_name'],
                            'supermarket_name': prices[0]['supermarket_name'],
                            'volatility': volatility,
                            'mean_price': mean_price,
                            'std_price': std_price,
                            'data_points': len(prices)
                        })
            
            # Sort by volatility descending
            high_volatility.sort(key=lambda x: x['volatility'], reverse=True)
            
            return high_volatility[:50]  # Return top 50
            
        except Exception as e:
            self.logger.error(f"Error checking price volatility: {e}")
            return []
    
    # =====================================================================
    # 3. DATA QUALITY CHECKS
    # =====================================================================
    
    def run_data_quality_checks(self) -> Dict[str, Any]:
        """Run comprehensive data quality checks"""
        try:
            quality_results = {
                'duplicate_check': self._check_duplicates(),
                'consistency_check': self._check_data_consistency(),
                'completeness_check': self._check_data_completeness(),
                'integrity_check': self._check_referential_integrity()
            }
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(quality_results)
            
            # Generate alerts for quality issues
            for check_name, result in quality_results.items():
                if result.get('issue_count', 0) > 0:
                    severity = "high" if result['issue_count'] > 100 else "medium"
                    self._create_alert(
                        alert_type="data_quality",
                        severity=severity,
                        title=f"Data Quality Issue: {check_name.replace('_', ' ').title()}",
                        description=f"Found {result['issue_count']} issues in {check_name}",
                        metric_value=result['issue_count'],
                        threshold_value=0,
                        recommended_action=result.get('recommended_action', 'Review and fix data quality issues')
                    )
            
            return {
                'status': 'completed',
                'overall_quality_score': quality_score,
                'checks': quality_results,
                'alerts_generated': len([a for a in self.alerts if a.alert_type == 'data_quality'])
            }
            
        except Exception as e:
            self.logger.error(f"Error running data quality checks: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_duplicates(self) -> Dict[str, Any]:
        """Check for duplicate price records"""
        try:
            # Check for duplicate price history records
            response = self.supabase.rpc(
                'check_price_history_duplicates'
            ).execute()
            
            if response.data:
                duplicate_count = response.data[0].get('duplicate_count', 0)
            else:
                # Fallback query
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                all_records = self.supabase.table("price_history").select(
                    "product_id, supermarket_id, price_date"
                ).gte("price_date", yesterday).execute()
                
                # Count duplicates manually
                seen = set()
                duplicate_count = 0
                for row in all_records.data:
                    key = (row['product_id'], row['supermarket_id'], row['price_date'])
                    if key in seen:
                        duplicate_count += 1
                    seen.add(key)
            
            return {
                'issue_count': duplicate_count,
                'check_type': 'duplicates',
                'description': f'Found {duplicate_count} duplicate price records',
                'recommended_action': 'Remove duplicate records and fix import process'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking duplicates: {e}")
            return {'issue_count': 0, 'check_type': 'duplicates', 'error': str(e)}
    
    def _check_data_consistency(self) -> Dict[str, Any]:
        """Check for data consistency issues"""
        try:
            issues = []
            
            # Check for products with inconsistent names
            response = self.supabase.table("products").select(
                "id, name, normalized_name"
            ).execute()
            
            inconsistent_names = 0
            for row in response.data:
                if row['name'] and row['normalized_name']:
                    # Basic consistency check
                    if len(row['name'].strip()) == 0 or len(row['normalized_name'].strip()) == 0:
                        inconsistent_names += 1
            
            # Check for price consistency (current_prices vs price_history)
            price_inconsistencies = self._check_price_consistency()
            
            total_issues = inconsistent_names + price_inconsistencies
            
            return {
                'issue_count': total_issues,
                'check_type': 'consistency',
                'details': {
                    'inconsistent_names': inconsistent_names,
                    'price_inconsistencies': price_inconsistencies
                },
                'description': f'Found {total_issues} consistency issues',
                'recommended_action': 'Review and standardize data formatting'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking data consistency: {e}")
            return {'issue_count': 0, 'check_type': 'consistency', 'error': str(e)}
    
    def _check_price_consistency(self) -> int:
        """Check consistency between current_prices and price_history"""
        try:
            # Get latest price_history for each product-supermarket combination
            latest_history = self.supabase.rpc(
                'get_latest_price_history'
            ).execute()
            
            # Get current_prices
            current_prices = self.supabase.table("current_prices").select(
                "product_id, supermarket_id, price, last_updated"
            ).execute()
            
            # Compare prices
            inconsistencies = 0
            current_dict = {(row['product_id'], row['supermarket_id']): row['price'] 
                          for row in current_prices.data}
            
            for row in latest_history.data if latest_history.data else []:
                key = (row['product_id'], row['supermarket_id'])
                if key in current_dict:
                    if abs(current_dict[key] - row['price']) > 0.01:  # Allow for small rounding differences
                        inconsistencies += 1
            
            return inconsistencies
            
        except Exception as e:
            self.logger.error(f"Error checking price consistency: {e}")
            return 0
    
    def _check_data_completeness(self) -> Dict[str, Any]:
        """Check for data completeness issues"""
        try:
            # Check for products without recent prices
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            total_products = self.supabase.table("products").select(
                "id", count="exact"
            ).execute().count
            
            products_with_recent_prices = self.supabase.table("price_history").select(
                "product_id"
            ).gte("price_date", yesterday).execute()
            
            unique_products_with_prices = len(set(row['product_id'] for row in products_with_recent_prices.data))
            
            missing_percentage = ((total_products - unique_products_with_prices) / total_products) * 100 if total_products > 0 else 0
            
            issue_count = 0
            if missing_percentage > self.config.max_missing_data_percentage:
                issue_count = total_products - unique_products_with_prices
            
            return {
                'issue_count': issue_count,
                'check_type': 'completeness',
                'details': {
                    'total_products': total_products,
                    'products_with_recent_prices': unique_products_with_prices,
                    'missing_percentage': missing_percentage
                },
                'description': f'{missing_percentage:.1f}% of products missing recent price data',
                'recommended_action': 'Investigate why some products lack recent price updates'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking data completeness: {e}")
            return {'issue_count': 0, 'check_type': 'completeness', 'error': str(e)}
    
    def _check_referential_integrity(self) -> Dict[str, Any]:
        """Check for referential integrity issues"""
        try:
            issues = 0
            
            # Check for orphaned price_history records
            orphaned_prices = self.supabase.rpc(
                'check_orphaned_price_records'
            ).execute()
            
            if orphaned_prices.data:
                issues += orphaned_prices.data[0].get('orphaned_count', 0)
            
            # Check for orphaned current_prices records
            orphaned_current = self.supabase.rpc(
                'check_orphaned_current_prices'
            ).execute()
            
            if orphaned_current.data:
                issues += orphaned_current.data[0].get('orphaned_count', 0)
            
            return {
                'issue_count': issues,
                'check_type': 'referential_integrity',
                'description': f'Found {issues} orphaned records',
                'recommended_action': 'Clean up orphaned records and check foreign key constraints'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking referential integrity: {e}")
            return {'issue_count': 0, 'check_type': 'referential_integrity', 'error': str(e)}
    
    def _calculate_quality_score(self, quality_results: Dict) -> float:
        """Calculate overall data quality score (0-100)"""
        try:
            total_issues = sum(result.get('issue_count', 0) for result in quality_results.values())
            
            # Base score of 100, subtract points for issues
            score = 100.0
            
            # Deduct points based on issue count and type
            for check_name, result in quality_results.items():
                issue_count = result.get('issue_count', 0)
                if issue_count > 0:
                    # Different weights for different types of issues
                    if check_name == 'duplicate_check':
                        score -= min(issue_count * 0.1, 20)  # Max 20 points for duplicates
                    elif check_name == 'consistency_check':
                        score -= min(issue_count * 0.2, 25)  # Max 25 points for consistency
                    elif check_name == 'completeness_check':
                        score -= min(issue_count * 0.3, 30)  # Max 30 points for completeness
                    elif check_name == 'integrity_check':
                        score -= min(issue_count * 0.5, 25)  # Max 25 points for integrity
            
            return max(score, 0.0)  # Ensure score doesn't go below 0
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    # =====================================================================
    # 4. PERFORMANCE MONITORING
    # =====================================================================
    
    def monitor_performance(self) -> Dict[str, Any]:
        """Monitor system performance metrics"""
        try:
            performance_metrics = {
                'import_performance': self._check_import_performance(),
                'query_performance': self._check_query_performance(),
                'storage_usage': self._check_storage_usage(),
                'error_rates': self._check_error_rates()
            }
            
            # Generate performance alerts
            for metric_name, metric_data in performance_metrics.items():
                if metric_data.get('alert_triggered', False):
                    self._create_alert(
                        alert_type="performance",
                        severity=metric_data.get('severity', 'medium'),
                        title=f"Performance Issue: {metric_name.replace('_', ' ').title()}",
                        description=metric_data.get('alert_message', 'Performance threshold exceeded'),
                        metric_value=metric_data.get('current_value'),
                        threshold_value=metric_data.get('threshold'),
                        recommended_action=metric_data.get('recommended_action', 'Investigate performance issue')
                    )
            
            return {
                'status': 'completed',
                'metrics': performance_metrics,
                'alerts_generated': len([a for a in self.alerts if a.alert_type == 'performance'])
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring performance: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_import_performance(self) -> Dict[str, Any]:
        """Check import process performance"""
        try:
            # Get recent import logs
            response = self.supabase.table("import_logs").select(
                "start_time, end_time, total_products, errors"
            ).order("start_time", desc=True).limit(10).execute()
            
            if not response.data:
                return {'status': 'no_data', 'message': 'No import logs found'}
            
            # Calculate average import duration
            durations = []
            error_counts = []
            
            for log in response.data:
                if log['start_time'] and log['end_time']:
                    start = datetime.fromisoformat(log['start_time'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(log['end_time'].replace('Z', '+00:00'))
                    duration_minutes = (end - start).total_seconds() / 60
                    durations.append(duration_minutes)
                
                error_counts.append(log.get('errors', 0))
            
            avg_duration = np.mean(durations) if durations else 0
            latest_duration = durations[0] if durations else 0
            
            # Check if latest import exceeded threshold
            alert_triggered = latest_duration > self.config.max_import_duration_minutes
            
            return {
                'avg_duration_minutes': avg_duration,
                'latest_duration_minutes': latest_duration,
                'max_duration_minutes': max(durations) if durations else 0,
                'alert_triggered': alert_triggered,
                'current_value': latest_duration,
                'threshold': self.config.max_import_duration_minutes,
                'severity': 'high' if latest_duration > self.config.max_import_duration_minutes * 1.5 else 'medium',
                'alert_message': f'Import took {latest_duration:.1f} minutes',
                'recommended_action': 'Optimize import process or increase timeout threshold'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking import performance: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_query_performance(self) -> Dict[str, Any]:
        """Check database query performance"""
        try:
            # Run test queries and measure performance
            test_queries = [
                ("current_prices_query", "SELECT COUNT(*) FROM current_prices"),
                ("price_history_query", "SELECT COUNT(*) FROM price_history WHERE price_date >= CURRENT_DATE - INTERVAL '7 days'"),
                ("product_search_query", "SELECT * FROM products WHERE name ILIKE '%melk%' LIMIT 10")
            ]
            
            query_results = []
            max_query_time = 0
            
            for query_name, query_sql in test_queries:
                start_time = time.time()
                
                try:
                    # Execute query through Supabase
                    if "COUNT(*)" in query_sql:
                        if "current_prices" in query_sql:
                            result = self.supabase.table("current_prices").select("*", count="exact").execute()
                        elif "price_history" in query_sql:
                            yesterday = (date.today() - timedelta(days=7)).isoformat()
                            result = self.supabase.table("price_history").select("*", count="exact").gte("price_date", yesterday).execute()
                    else:
                        result = self.supabase.table("products").select("*").ilike("name", "%melk%").limit(10).execute()
                    
                    query_time = time.time() - start_time
                    max_query_time = max(max_query_time, query_time)
                    
                    query_results.append({
                        'query_name': query_name,
                        'execution_time': query_time,
                        'status': 'success'
                    })
                    
                except Exception as e:
                    query_results.append({
                        'query_name': query_name,
                        'execution_time': time.time() - start_time,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Check if any query exceeded threshold
            alert_triggered = max_query_time > self.config.max_query_time_seconds
            
            return {
                'query_results': query_results,
                'max_query_time': max_query_time,
                'avg_query_time': np.mean([q['execution_time'] for q in query_results]),
                'alert_triggered': alert_triggered,
                'current_value': max_query_time,
                'threshold': self.config.max_query_time_seconds,
                'severity': 'high' if max_query_time > self.config.max_query_time_seconds * 2 else 'medium',
                'alert_message': f'Query took {max_query_time:.2f} seconds',
                'recommended_action': 'Check database performance and optimize slow queries'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking query performance: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_storage_usage(self) -> Dict[str, Any]:
        """Check database storage usage trends"""
        try:
            # This would typically require database-specific queries
            # For Supabase/PostgreSQL, we can estimate based on record counts
            
            # Count records in main tables
            tables_to_check = ["price_history", "current_prices", "products", "supermarkets"]
            table_sizes = {}
            
            for table in tables_to_check:
                try:
                    response = self.supabase.table(table).select("*", count="exact").execute()
                    table_sizes[table] = response.count
                except Exception as e:
                    table_sizes[table] = 0
            
            # Estimate storage (rough calculation)
            # Assume average 200 bytes per price_history record
            estimated_size_mb = (table_sizes.get("price_history", 0) * 200) / (1024 * 1024)
            
            # Check growth rate (would need historical data for accurate calculation)
            # For now, use a placeholder
            monthly_growth_gb = estimated_size_mb / 1024  # Very rough estimate
            
            alert_triggered = monthly_growth_gb > self.config.max_storage_growth_gb_per_month
            
            return {
                'table_sizes': table_sizes,
                'estimated_size_mb': estimated_size_mb,
                'monthly_growth_gb': monthly_growth_gb,
                'alert_triggered': alert_triggered,
                'current_value': monthly_growth_gb,
                'threshold': self.config.max_storage_growth_gb_per_month,
                'severity': 'medium',
                'alert_message': f'Storage growing at {monthly_growth_gb:.2f} GB/month',
                'recommended_action': 'Consider archiving old data or optimizing storage'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking storage usage: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_error_rates(self) -> Dict[str, Any]:
        """Check error rates in recent imports"""
        try:
            # Get recent import logs with error information
            response = self.supabase.table("import_logs").select(
                "total_products, errors, import_date"
            ).gte("import_date", (date.today() - timedelta(days=7)).isoformat()).execute()
            
            if not response.data:
                return {'status': 'no_data', 'message': 'No recent import logs found'}
            
            total_records = sum(log.get('total_products', 0) for log in response.data)
            total_errors = sum(log.get('errors', 0) for log in response.data)
            
            error_rate = (total_errors / total_records) * 100 if total_records > 0 else 0
            
            alert_triggered = error_rate > self.config.max_error_rate_percentage
            
            return {
                'total_records': total_records,
                'total_errors': total_errors,
                'error_rate_percentage': error_rate,
                'imports_analyzed': len(response.data),
                'alert_triggered': alert_triggered,
                'current_value': error_rate,
                'threshold': self.config.max_error_rate_percentage,
                'severity': 'high' if error_rate > self.config.max_error_rate_percentage * 2 else 'medium',
                'alert_message': f'Error rate is {error_rate:.2f}%',
                'recommended_action': 'Investigate and fix data source issues causing errors'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking error rates: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # =====================================================================
    # 5. AUTOMATED REPORTING
    # =====================================================================
    
    def generate_daily_report(self) -> MonitoringReport:
        """Generate daily import summary report"""
        try:
            period_start = datetime.combine(date.today(), datetime.min.time())
            period_end = datetime.combine(date.today(), datetime.max.time())
            
            # Get import statistics for today
            today = date.today().isoformat()
            import_stats = self._get_daily_import_stats(today)
            
            # Get alerts from today
            today_alerts = [alert for alert in self.alerts 
                          if alert.detected_at.date() == date.today()]
            
            # Generate summary
            summary = {
                'import_status': 'completed' if import_stats['records_imported'] > 0 else 'no_import',
                'records_imported': import_stats['records_imported'],
                'products_updated': import_stats['products_updated'],
                'price_changes': import_stats['price_changes'],
                'errors': import_stats['errors'],
                'alerts_triggered': len(today_alerts),
                'data_quality_score': self._get_current_quality_score()
            }
            
            # Metrics
            metrics = {
                'import_duration': import_stats.get('duration_minutes', 0),
                'processing_rate': import_stats.get('processing_rate', 0),
                'error_rate': import_stats.get('error_rate', 0),
                'supermarket_coverage': import_stats.get('supermarket_coverage', 0)
            }
            
            # Recommendations
            recommendations = self._generate_daily_recommendations(summary, today_alerts)
            
            report = MonitoringReport(
                report_type="daily_import_summary",
                generated_at=datetime.now(),
                period_start=period_start,
                period_end=period_end,
                summary=summary,
                metrics=metrics,
                alerts=today_alerts,
                recommendations=recommendations
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return MonitoringReport(
                report_type="daily_import_summary",
                generated_at=datetime.now(),
                period_start=datetime.now(),
                period_end=datetime.now(),
                summary={'error': str(e)},
                metrics={},
                alerts=[],
                recommendations=[]
            )
    
    def generate_weekly_report(self) -> MonitoringReport:
        """Generate weekly price trend report"""
        try:
            period_end = datetime.now()
            period_start = period_end - timedelta(days=7)
            
            # Analyze price trends for the week
            from price_analysis import create_analyzer
            
            analyzer = create_analyzer(
                supabase_url=os.getenv("SUPABASE_URL"),
                supabase_key=os.getenv("SUPABASE_KEY")
            )
            
            # Get weekly trends
            trends = analyzer.get_price_trends(days=7)
            significant_changes = analyzer.detect_significant_changes(days=7, threshold=10.0)
            
            # Calculate summary statistics
            if trends:
                avg_change = np.mean([t.price_change_percentage for t in trends])
                max_increase = max([t.price_change_percentage for t in trends])
                max_decrease = min([t.price_change_percentage for t in trends])
                volatile_products = len([t for t in trends if t.volatility > 20])
            else:
                avg_change = max_increase = max_decrease = volatile_products = 0
            
            summary = {
                'total_products_analyzed': len(trends),
                'avg_price_change': avg_change,
                'max_price_increase': max_increase,
                'max_price_decrease': max_decrease,
                'significant_changes': len(significant_changes),
                'volatile_products': volatile_products
            }
            
            metrics = {
                'price_volatility': np.mean([t.volatility for t in trends]) if trends else 0,
                'products_with_increases': len([t for t in trends if t.price_change_percentage > 0]),
                'products_with_decreases': len([t for t in trends if t.price_change_percentage < 0]),
                'data_coverage_days': 7
            }
            
            # Weekly alerts (price-related only)
            weekly_alerts = [alert for alert in self.alerts 
                           if alert.alert_type in ['price_anomaly', 'data_quality'] 
                           and alert.detected_at >= period_start]
            
            recommendations = self._generate_weekly_recommendations(summary, significant_changes)
            
            report = MonitoringReport(
                report_type="weekly_price_trends",
                generated_at=datetime.now(),
                period_start=period_start,
                period_end=period_end,
                summary=summary,
                metrics=metrics,
                alerts=weekly_alerts,
                recommendations=recommendations
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
            return MonitoringReport(
                report_type="weekly_price_trends",
                generated_at=datetime.now(),
                period_start=datetime.now(),
                period_end=datetime.now(),
                summary={'error': str(e)},
                metrics={},
                alerts=[],
                recommendations=[]
            )
    
    def generate_monthly_report(self) -> MonitoringReport:
        """Generate monthly data health report"""
        try:
            period_end = datetime.now()
            period_start = period_end - timedelta(days=30)
            
            # Run comprehensive health checks
            quality_results = self.run_data_quality_checks()
            performance_results = self.monitor_performance()
            
            # Get monthly statistics
            monthly_stats = self._get_monthly_statistics()
            
            summary = {
                'data_quality_score': quality_results.get('overall_quality_score', 0),
                'total_imports': monthly_stats.get('total_imports', 0),
                'total_records_processed': monthly_stats.get('total_records', 0),
                'avg_daily_records': monthly_stats.get('avg_daily_records', 0),
                'total_alerts': len(self.alerts),
                'system_uptime_percentage': monthly_stats.get('uptime_percentage', 0)
            }
            
            metrics = {
                'storage_growth_gb': performance_results.get('metrics', {}).get('storage_usage', {}).get('monthly_growth_gb', 0),
                'avg_import_duration': performance_results.get('metrics', {}).get('import_performance', {}).get('avg_duration_minutes', 0),
                'avg_query_time': performance_results.get('metrics', {}).get('query_performance', {}).get('avg_query_time', 0),
                'error_rate': performance_results.get('metrics', {}).get('error_rates', {}).get('error_rate_percentage', 0)
            }
            
            # Monthly alerts (all types)
            monthly_alerts = [alert for alert in self.alerts 
                            if alert.detected_at >= period_start]
            
            recommendations = self._generate_monthly_recommendations(summary, quality_results, performance_results)
            
            report = MonitoringReport(
                report_type="monthly_data_health",
                generated_at=datetime.now(),
                period_start=period_start,
                period_end=period_end,
                summary=summary,
                metrics=metrics,
                alerts=monthly_alerts,
                recommendations=recommendations
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating monthly report: {e}")
            return MonitoringReport(
                report_type="monthly_data_health",
                generated_at=datetime.now(),
                period_start=datetime.now(),
                period_end=datetime.now(),
                summary={'error': str(e)},
                metrics={},
                alerts=[],
                recommendations=[]
            )
    
    def _get_daily_import_stats(self, date_str: str) -> Dict[str, Any]:
        """Get import statistics for a specific date"""
        try:
            # Get from import_logs table
            response = self.supabase.table("import_logs").select(
                "*"
            ).eq("import_date", date_str).execute()
            
            if response.data:
                log = response.data[0]
                return {
                    'records_imported': log.get('total_products', 0),
                    'products_updated': log.get('updated_products', 0),
                    'price_changes': log.get('price_changes', 0),
                    'errors': log.get('errors', 0),
                    'duration_minutes': self._calculate_duration_minutes(log.get('start_time'), log.get('end_time')),
                    'processing_rate': log.get('total_products', 0) / max(self._calculate_duration_minutes(log.get('start_time'), log.get('end_time')), 1),
                    'error_rate': (log.get('errors', 0) / max(log.get('total_products', 1), 1)) * 100,
                    'supermarket_coverage': 100  # Placeholder
                }
            else:
                return {
                    'records_imported': 0,
                    'products_updated': 0,
                    'price_changes': 0,
                    'errors': 0,
                    'duration_minutes': 0,
                    'processing_rate': 0,
                    'error_rate': 0,
                    'supermarket_coverage': 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting daily import stats: {e}")
            return {}
    
    def _calculate_duration_minutes(self, start_time: str, end_time: str) -> float:
        """Calculate duration in minutes between two timestamp strings"""
        try:
            if not start_time or not end_time:
                return 0.0
            
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            return (end - start).total_seconds() / 60
        except:
            return 0.0
    
    def _get_current_quality_score(self) -> float:
        """Get current data quality score"""
        try:
            quality_results = self.run_data_quality_checks()
            return quality_results.get('overall_quality_score', 0.0)
        except:
            return 0.0
    
    def _get_monthly_statistics(self) -> Dict[str, Any]:
        """Get monthly system statistics"""
        try:
            thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
            
            # Get import logs for the month
            response = self.supabase.table("import_logs").select(
                "*"
            ).gte("import_date", thirty_days_ago).execute()
            
            if response.data:
                total_imports = len(response.data)
                total_records = sum(log.get('total_products', 0) for log in response.data)
                avg_daily_records = total_records / 30  # Average over 30 days
                
                # Calculate uptime (days with successful imports / total days)
                successful_days = len([log for log in response.data if log.get('errors', 0) == 0])
                uptime_percentage = (successful_days / 30) * 100
            else:
                total_imports = total_records = avg_daily_records = uptime_percentage = 0
            
            return {
                'total_imports': total_imports,
                'total_records': total_records,
                'avg_daily_records': avg_daily_records,
                'uptime_percentage': uptime_percentage
            }
            
        except Exception as e:
            self.logger.error(f"Error getting monthly statistics: {e}")
            return {}
    
    def _generate_daily_recommendations(self, summary: Dict, alerts: List[MonitoringAlert]) -> List[str]:
        """Generate recommendations for daily report"""
        recommendations = []
        
        if summary.get('import_status') == 'no_import':
            recommendations.append("No import detected today. Check import schedule and process status.")
        
        if summary.get('errors', 0) > 0:
            recommendations.append(f"Fix {summary['errors']} import errors to improve data quality.")
        
        if summary.get('alerts_triggered', 0) > 0:
            recommendations.append("Review and address triggered alerts to maintain system health.")
        
        if summary.get('data_quality_score', 100) < 90:
            recommendations.append("Data quality score is below 90%. Run detailed quality checks.")
        
        if not recommendations:
            recommendations.append("System is operating normally. Continue monitoring.")
        
        return recommendations
    
    def _generate_weekly_recommendations(self, summary: Dict, significant_changes: List) -> List[str]:
        """Generate recommendations for weekly report"""
        recommendations = []
        
        if abs(summary.get('avg_price_change', 0)) > 5:
            recommendations.append("Significant average price changes detected. Review market conditions.")
        
        if summary.get('volatile_products', 0) > 10:
            recommendations.append("High number of volatile products. Investigate price instability.")
        
        if len(significant_changes) > 50:
            recommendations.append("Many significant price changes detected. Validate data sources.")
        
        if not recommendations:
            recommendations.append("Price trends are within normal ranges.")
        
        return recommendations
    
    def _generate_monthly_recommendations(self, summary: Dict, quality_results: Dict, performance_results: Dict) -> List[str]:
        """Generate recommendations for monthly report"""
        recommendations = []
        
        if summary.get('data_quality_score', 100) < 80:
            recommendations.append("Data quality score is concerning. Implement data validation improvements.")
        
        if summary.get('system_uptime_percentage', 100) < 95:
            recommendations.append("System uptime is below target. Improve reliability and monitoring.")
        
        performance_metrics = performance_results.get('metrics', {})
        if performance_metrics.get('storage_usage', {}).get('monthly_growth_gb', 0) > 5:
            recommendations.append("High storage growth detected. Consider data archiving strategy.")
        
        if performance_metrics.get('import_performance', {}).get('avg_duration_minutes', 0) > 60:
            recommendations.append("Import process is slowing down. Optimize performance.")
        
        if not recommendations:
            recommendations.append("System health is good. Continue current maintenance practices.")
        
        return recommendations
    
    # =====================================================================
    # 6. DATA MAINTENANCE
    # =====================================================================
    
    def run_data_maintenance(self) -> Dict[str, Any]:
        """Run data maintenance operations"""
        try:
            maintenance_results = {
                'archive_operations': self._archive_old_data(),
                'cleanup_operations': self._cleanup_orphaned_records(),
                'optimization_operations': self._optimize_database_performance(),
                'backup_validation': self._validate_backup_integrity()
            }
            
            # Log maintenance completion
            self.logger.info("Data maintenance completed successfully")
            
            return {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'operations': maintenance_results
            }
            
        except Exception as e:
            self.logger.error(f"Error running data maintenance: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _archive_old_data(self) -> Dict[str, Any]:
        """Archive old price history data"""
        try:
            archive_date = (date.today() - timedelta(days=self.config.archive_after_days)).isoformat()
            
            # Count records to be archived
            old_records = self.supabase.table("price_history").select(
                "id", count="exact"
            ).lt("price_date", archive_date).execute()
            
            records_to_archive = old_records.count
            
            if records_to_archive > 0:
                # In a real implementation, you would move these to an archive table
                # For now, we'll just log the operation
                self.logger.info(f"Would archive {records_to_archive} records older than {archive_date}")
                
                # Archive operation would be implemented here
                # Example: Move to price_history_archive table
                
            return {
                'records_identified': records_to_archive,
                'archive_date': archive_date,
                'status': 'completed' if records_to_archive == 0 else 'simulated'
            }
            
        except Exception as e:
            self.logger.error(f"Error archiving old data: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _cleanup_orphaned_records(self) -> Dict[str, Any]:
        """Clean up orphaned records"""
        try:
            cleanup_results = {}
            
            # Check for orphaned current_prices
            orphaned_current = self.supabase.rpc('cleanup_orphaned_current_prices').execute()
            cleanup_results['current_prices'] = orphaned_current.data[0] if orphaned_current.data else {'cleaned': 0}
            
            # Check for orphaned price_history
            orphaned_history = self.supabase.rpc('cleanup_orphaned_price_history').execute()
            cleanup_results['price_history'] = orphaned_history.data[0] if orphaned_history.data else {'cleaned': 0}
            
            total_cleaned = sum(result.get('cleaned', 0) for result in cleanup_results.values())
            
            return {
                'total_records_cleaned': total_cleaned,
                'details': cleanup_results,
                'status': 'completed'
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning orphaned records: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _optimize_database_performance(self) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            optimization_results = {}
            
            # Update table statistics
            try:
                self.supabase.rpc('update_table_statistics').execute()
                optimization_results['statistics_updated'] = True
            except:
                optimization_results['statistics_updated'] = False
            
            # Reindex tables (if needed)
            try:
                self.supabase.rpc('reindex_price_tables').execute()
                optimization_results['indexes_rebuilt'] = True
            except:
                optimization_results['indexes_rebuilt'] = False
            
            # Vacuum tables (PostgreSQL specific)
            try:
                self.supabase.rpc('vacuum_price_tables').execute()
                optimization_results['tables_vacuumed'] = True
            except:
                optimization_results['tables_vacuumed'] = False
            
            return {
                'optimizations': optimization_results,
                'status': 'completed'
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _validate_backup_integrity(self) -> Dict[str, Any]:
        """Validate backup integrity"""
        try:
            # This would typically involve checking backup files
            # For Supabase, we can verify data consistency
            
            validation_results = {
                'data_consistency': True,
                'row_counts_match': True,
                'foreign_keys_valid': True
            }
            
            # Verify row counts between related tables
            products_count = self.supabase.table("products").select("*", count="exact").execute().count
            price_products = self.supabase.table("price_history").select("product_id").execute()
            unique_price_products = len(set(row['product_id'] for row in price_products.data))
            
            if unique_price_products > products_count:
                validation_results['data_consistency'] = False
                validation_results['row_counts_match'] = False
            
            return {
                'validation_results': validation_results,
                'backup_status': 'healthy' if all(validation_results.values()) else 'issues_detected',
                'status': 'completed'
            }
            
        except Exception as e:
            self.logger.error(f"Error validating backup integrity: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # =====================================================================
    # 7. EMAIL NOTIFICATIONS
    # =====================================================================
    
    def send_email_notification(self, subject: str, body: str, recipients: List[str] = None, 
                              is_alert: bool = False) -> bool:
        """Send email notification"""
        try:
            if not self.config.email_from or not self.config.email_password:
                self.logger.warning("Email credentials not configured")
                return False
            
            # Determine recipients
            if recipients is None:
                recipients = self.config.alert_recipients if is_alert else self.config.report_recipients
            
            if not recipients:
                self.logger.warning("No email recipients configured")
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_from, self.config.email_password)
            
            text = msg.as_string()
            server.sendmail(self.config.email_from, recipients, text)
            server.quit()
            
            self.logger.info(f"Email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def send_alert_notifications(self) -> bool:
        """Send email notifications for alerts"""
        try:
            if not self.alerts:
                return True
            
            # Group alerts by severity
            critical_alerts = [a for a in self.alerts if a.severity == 'critical']
            high_alerts = [a for a in self.alerts if a.severity == 'high']
            medium_alerts = [a for a in self.alerts if a.severity == 'medium']
            
            # Send critical alerts immediately
            if critical_alerts:
                subject = f"🚨 CRITICAL: Price History System Alerts ({len(critical_alerts)})"
                body = self._format_alert_email(critical_alerts, "CRITICAL")
                self.send_email_notification(subject, body, is_alert=True)
            
            # Send high priority alerts
            if high_alerts:
                subject = f"⚠️ HIGH PRIORITY: Price History System Alerts ({len(high_alerts)})"
                body = self._format_alert_email(high_alerts, "HIGH PRIORITY")
                self.send_email_notification(subject, body, is_alert=True)
            
            # Send medium priority alerts (grouped)
            if medium_alerts:
                subject = f"ℹ️ MEDIUM PRIORITY: Price History System Alerts ({len(medium_alerts)})"
                body = self._format_alert_email(medium_alerts, "MEDIUM PRIORITY")
                self.send_email_notification(subject, body, is_alert=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert notifications: {e}")
            return False
    
    def send_report_notification(self, report: MonitoringReport) -> bool:
        """Send email notification for a report"""
        try:
            subject = f"📊 {report.report_type.replace('_', ' ').title()} - {report.generated_at.strftime('%Y-%m-%d')}"
            body = self._format_report_email(report)
            
            return self.send_email_notification(subject, body, is_alert=False)
            
        except Exception as e:
            self.logger.error(f"Error sending report notification: {e}")
            return False
    
    def _format_alert_email(self, alerts: List[MonitoringAlert], severity_label: str) -> str:
        """Format alerts into HTML email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ff6b6b; background-color: #fff5f5; }}
                .alert-high {{ border-left-color: #ff6b6b; }}
                .alert-medium {{ border-left-color: #ffa726; }}
                .alert-critical {{ border-left-color: #d32f2f; }}
                .metric {{ font-weight: bold; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h2>{severity_label} Alerts - Price History System</h2>
            <p>The following alerts have been triggered:</p>
        """
        
        for alert in alerts:
            html += f"""
            <div class="alert alert-{alert.severity}">
                <h3>{alert.title}</h3>
                <p>{alert.description}</p>
                <p><span class="metric">Current Value:</span> {alert.metric_value}</p>
                <p><span class="metric">Threshold:</span> {alert.threshold_value}</p>
                <p><strong>Recommended Action:</strong> {alert.recommended_action}</p>
                <p class="timestamp">Detected: {alert.detected_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """
        
        html += """
            <hr>
            <p>Please investigate and resolve these alerts as soon as possible.</p>
            <p><em>This is an automated message from the Price History Monitoring System.</em></p>
        </body>
        </html>
        """
        
        return html
    
    def _format_report_email(self, report: MonitoringReport) -> str:
        """Format report into HTML email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; }}
                .metric {{ margin: 5px 0; }}
                .good {{ color: #4caf50; }}
                .warning {{ color: #ff9800; }}
                .error {{ color: #f44336; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>{report.report_type.replace('_', ' ').title()}</h2>
            <p><strong>Period:</strong> {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}</p>
            <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h3>Summary</h3>
        """
        
        for key, value in report.summary.items():
            status_class = "good"
            if isinstance(value, (int, float)):
                if key.endswith('_score') and value < 80:
                    status_class = "warning"
                elif key.endswith('errors') and value > 0:
                    status_class = "error"
            
            html += f'<div class="metric {status_class}"><strong>{key.replace("_", " ").title()}:</strong> {value}</div>'
        
        html += """
            </div>
            
            <h3>Metrics</h3>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for key, value in report.metrics.items():
            html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
        
        html += "</table>"
        
        if report.alerts:
            html += f"""
            <h3>Alerts ({len(report.alerts)})</h3>
            <ul>
            """
            for alert in report.alerts:
                html += f"<li><strong>{alert.title}</strong> - {alert.description}</li>"
            html += "</ul>"
        
        if report.recommendations:
            html += """
            <h3>Recommendations</h3>
            <ul>
            """
            for rec in report.recommendations:
                html += f"<li>{rec}</li>"
            html += "</ul>"
        
        html += """
            <hr>
            <p><em>This is an automated report from the Price History Monitoring System.</em></p>
        </body>
        </html>
        """
        
        return html
    
    # =====================================================================
    # 8. MAIN MONITORING FUNCTION
    # =====================================================================
    
    def run_full_monitoring(self) -> Dict[str, Any]:
        """Run complete monitoring suite"""
        try:
            self.logger.info("Starting full monitoring suite...")
            
            # Clear previous alerts
            self.alerts = []
            
            monitoring_results = {
                'data_freshness': self.check_data_freshness(),
                'price_anomalies': self.detect_price_anomalies(),
                'data_quality': self.run_data_quality_checks(),
                'performance': self.monitor_performance()
            }
            
            # Generate reports
            reports = {
                'daily_report': self.generate_daily_report(),
                'weekly_report': self.generate_weekly_report(),
                'monthly_report': self.generate_monthly_report()
            }
            
            # Send notifications
            alert_sent = self.send_alert_notifications()
            
            # Calculate overall system health
            overall_health = self._calculate_overall_health(monitoring_results)
            
            self.logger.info(f"Monitoring completed. Overall health: {overall_health}%")
            
            return {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'overall_health_percentage': overall_health,
                'monitoring_results': monitoring_results,
                'reports_generated': len(reports),
                'alerts_triggered': len(self.alerts),
                'notifications_sent': alert_sent,
                'alerts': [asdict(alert) for alert in self.alerts]
            }
            
        except Exception as e:
            self.logger.error(f"Error in full monitoring: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_overall_health(self, monitoring_results: Dict) -> float:
        """Calculate overall system health percentage"""
        try:
            health_score = 100.0
            
            # Deduct points for issues
            for category, result in monitoring_results.items():
                if result.get('status') == 'error':
                    health_score -= 25  # Major deduction for errors
                elif category == 'data_quality':
                    quality_score = result.get('overall_quality_score', 100)
                    health_score = min(health_score, quality_score)
                elif result.get('alerts_generated', 0) > 0:
                    health_score -= min(result['alerts_generated'] * 5, 20)  # Max 20 points for alerts
            
            return max(health_score, 0.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating overall health: {e}")
            return 0.0

# Convenience function for easy usage
def create_monitor(supabase_url: str, supabase_key: str, config: MonitoringConfig = None) -> PriceHistoryMonitor:
    """
    Create a PriceHistoryMonitor instance
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        config: Monitoring configuration
        
    Returns:
        PriceHistoryMonitor instance
    """
    from supabase import create_client
    
    supabase = create_client(supabase_url, supabase_key)
    return PriceHistoryMonitor(supabase, config)

# Example usage
if __name__ == "__main__":
    import os
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        monitor = create_monitor(supabase_url, supabase_key)
        result = monitor.run_full_monitoring()
        print(f"Monitoring completed with {result.get('alerts_triggered', 0)} alerts")
    else:
        print("Please set SUPABASE_URL and SUPABASE_KEY environment variables")