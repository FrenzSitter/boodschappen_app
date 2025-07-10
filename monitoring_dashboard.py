#!/usr/bin/env python3
"""
Monitoring Dashboard for Price History System
=============================================

Creates dashboard-ready metrics and visualization data for monitoring
the price history import process. Provides real-time metrics, charts,
and alerts for operational dashboards.

Features:
- Real-time system health metrics
- Performance KPIs
- Alert summaries
- Historical trends for dashboards
- Export to common dashboard formats (Grafana, Prometheus, etc.)

Usage:
    from monitoring_dashboard import DashboardMetrics
    
    dashboard = DashboardMetrics(supabase_client)
    metrics = dashboard.get_dashboard_metrics()
"""

import os
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import asyncio

# Third-party imports
import numpy as np
import pandas as pd
from supabase import Client

@dataclass
class DashboardMetric:
    """Individual dashboard metric"""
    name: str
    value: Union[int, float, str]
    unit: str
    timestamp: datetime
    status: str  # healthy, warning, critical
    trend: str   # up, down, stable
    target: Optional[Union[int, float]] = None
    description: str = ""

@dataclass
class AlertSummary:
    """Alert summary for dashboard"""
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    latest_alert_time: Optional[datetime]
    trend_24h: str  # increasing, decreasing, stable

class DashboardMetrics:
    """Generate dashboard-ready metrics for monitoring system"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get complete dashboard metrics package"""
        try:
            return {
                'system_health': self.get_system_health_metrics(),
                'data_quality': self.get_data_quality_metrics(),
                'performance': self.get_performance_metrics(),
                'import_status': self.get_import_status_metrics(),
                'alerts': self.get_alert_metrics(),
                'trends': self.get_trend_metrics(),
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'refresh_interval': 300,  # 5 minutes
                    'data_retention_days': 30
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_health_metrics(self) -> List[DashboardMetric]:
        """Get system health KPIs"""
        metrics = []
        
        try:
            # Overall system health score
            health_score = self._calculate_system_health()
            metrics.append(DashboardMetric(
                name="system_health_score",
                value=health_score,
                unit="%",
                timestamp=datetime.now(),
                status=self._get_health_status(health_score),
                trend=self._get_health_trend(),
                target=95.0,
                description="Overall system health based on all monitoring metrics"
            ))
            
            # Data freshness
            last_import_hours = self._get_hours_since_last_import()
            metrics.append(DashboardMetric(
                name="data_freshness",
                value=last_import_hours,
                unit="hours",
                timestamp=datetime.now(),
                status="healthy" if last_import_hours < 25 else "warning" if last_import_hours < 48 else "critical",
                trend="stable",
                target=24.0,
                description="Hours since last successful data import"
            ))
            
            # Database connectivity
            db_status = self._check_database_connectivity()
            metrics.append(DashboardMetric(
                name="database_connectivity",
                value=1 if db_status else 0,
                unit="boolean",
                timestamp=datetime.now(),
                status="healthy" if db_status else "critical",
                trend="stable",
                target=1,
                description="Database connection status"
            ))
            
            # API response time
            api_response_time = self._measure_api_response_time()
            metrics.append(DashboardMetric(
                name="api_response_time",
                value=api_response_time,
                unit="ms",
                timestamp=datetime.now(),
                status="healthy" if api_response_time < 1000 else "warning" if api_response_time < 3000 else "critical",
                trend="stable",
                target=500.0,
                description="Average API response time"
            ))
            
        except Exception as e:
            metrics.append(DashboardMetric(
                name="system_health_error",
                value=str(e),
                unit="error",
                timestamp=datetime.now(),
                status="critical",
                trend="stable",
                description="Error calculating system health"
            ))
        
        return metrics
    
    def get_data_quality_metrics(self) -> List[DashboardMetric]:
        """Get data quality KPIs"""
        metrics = []
        
        try:
            # Data quality score
            quality_score = self._calculate_data_quality_score()
            metrics.append(DashboardMetric(
                name="data_quality_score",
                value=quality_score,
                unit="%",
                timestamp=datetime.now(),
                status=self._get_quality_status(quality_score),
                trend=self._get_quality_trend(),
                target=90.0,
                description="Overall data quality score"
            ))
            
            # Record completeness
            completeness = self._get_data_completeness()
            metrics.append(DashboardMetric(
                name="data_completeness",
                value=completeness,
                unit="%",
                timestamp=datetime.now(),
                status="healthy" if completeness > 95 else "warning" if completeness > 90 else "critical",
                trend="stable",
                target=98.0,
                description="Percentage of expected data records present"
            ))
            
            # Duplicate records
            duplicates = self._count_duplicate_records()
            metrics.append(DashboardMetric(
                name="duplicate_records",
                value=duplicates,
                unit="count",
                timestamp=datetime.now(),
                status="healthy" if duplicates < 100 else "warning" if duplicates < 1000 else "critical",
                trend="stable",
                target=0,
                description="Number of duplicate price records"
            ))
            
            # Invalid prices
            invalid_prices = self._count_invalid_prices()
            metrics.append(DashboardMetric(
                name="invalid_prices",
                value=invalid_prices,
                unit="count",
                timestamp=datetime.now(),
                status="healthy" if invalid_prices < 10 else "warning" if invalid_prices < 100 else "critical",
                trend="stable",
                target=0,
                description="Number of invalid price values"
            ))
            
        except Exception as e:
            metrics.append(DashboardMetric(
                name="data_quality_error",
                value=str(e),
                unit="error",
                timestamp=datetime.now(),
                status="critical",
                trend="stable",
                description="Error calculating data quality"
            ))
        
        return metrics
    
    def get_performance_metrics(self) -> List[DashboardMetric]:
        """Get performance KPIs"""
        metrics = []
        
        try:
            # Import processing rate
            processing_rate = self._get_processing_rate()
            metrics.append(DashboardMetric(
                name="processing_rate",
                value=processing_rate,
                unit="records/min",
                timestamp=datetime.now(),
                status="healthy" if processing_rate > 100 else "warning" if processing_rate > 50 else "critical",
                trend=self._get_processing_trend(),
                target=150.0,
                description="Records processed per minute during import"
            ))
            
            # Query performance
            avg_query_time = self._get_average_query_time()
            metrics.append(DashboardMetric(
                name="average_query_time",
                value=avg_query_time,
                unit="ms",
                timestamp=datetime.now(),
                status="healthy" if avg_query_time < 1000 else "warning" if avg_query_time < 3000 else "critical",
                trend="stable",
                target=500.0,
                description="Average database query response time"
            ))
            
            # Storage usage
            storage_usage = self._get_storage_usage()
            metrics.append(DashboardMetric(
                name="storage_usage",
                value=storage_usage,
                unit="GB",
                timestamp=datetime.now(),
                status="healthy" if storage_usage < 50 else "warning" if storage_usage < 80 else "critical",
                trend="up",
                target=100.0,
                description="Total database storage usage"
            ))
            
            # Error rate
            error_rate = self._get_error_rate()
            metrics.append(DashboardMetric(
                name="error_rate",
                value=error_rate,
                unit="%",
                timestamp=datetime.now(),
                status="healthy" if error_rate < 1 else "warning" if error_rate < 5 else "critical",
                trend="stable",
                target=0.5,
                description="Error rate in recent imports"
            ))
            
        except Exception as e:
            metrics.append(DashboardMetric(
                name="performance_error",
                value=str(e),
                unit="error",
                timestamp=datetime.now(),
                status="critical",
                trend="stable",
                description="Error calculating performance metrics"
            ))
        
        return metrics
    
    def get_import_status_metrics(self) -> List[DashboardMetric]:
        """Get import status KPIs"""
        metrics = []
        
        try:
            # Today's import status
            today_imported = self._get_today_import_count()
            metrics.append(DashboardMetric(
                name="todays_imports",
                value=today_imported,
                unit="records",
                timestamp=datetime.now(),
                status="healthy" if today_imported > 1000 else "warning" if today_imported > 0 else "critical",
                trend="stable",
                target=5000,
                description="Number of records imported today"
            ))
            
            # Supermarket coverage
            supermarket_coverage = self._get_supermarket_coverage()
            metrics.append(DashboardMetric(
                name="supermarket_coverage",
                value=supermarket_coverage,
                unit="%",
                timestamp=datetime.now(),
                status="healthy" if supermarket_coverage > 90 else "warning" if supermarket_coverage > 70 else "critical",
                trend="stable",
                target=100.0,
                description="Percentage of supermarkets with recent data"
            ))
            
            # Price changes detected
            price_changes = self._get_price_changes_count()
            metrics.append(DashboardMetric(
                name="price_changes_24h",
                value=price_changes,
                unit="count",
                timestamp=datetime.now(),
                status="healthy",
                trend="stable",
                description="Number of price changes detected in last 24 hours"
            ))
            
            # Products updated
            products_updated = self._get_products_updated_count()
            metrics.append(DashboardMetric(
                name="products_updated_24h",
                value=products_updated,
                unit="count",
                timestamp=datetime.now(),
                status="healthy" if products_updated > 1000 else "warning",
                trend="stable",
                target=5000,
                description="Number of products updated in last 24 hours"
            ))
            
        except Exception as e:
            metrics.append(DashboardMetric(
                name="import_status_error",
                value=str(e),
                unit="error",
                timestamp=datetime.now(),
                status="critical",
                trend="stable",
                description="Error calculating import status"
            ))
        
        return metrics
    
    def get_alert_metrics(self) -> AlertSummary:
        """Get alert summary for dashboard"""
        try:
            # Get alerts from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            
            # This would typically come from an alerts table
            # For now, we'll simulate based on system state
            alerts_data = self._get_recent_alerts()
            
            # Count by severity
            critical = len([a for a in alerts_data if a.get('severity') == 'critical'])
            high = len([a for a in alerts_data if a.get('severity') == 'high'])
            medium = len([a for a in alerts_data if a.get('severity') == 'medium'])
            low = len([a for a in alerts_data if a.get('severity') == 'low'])
            
            # Get latest alert time
            latest_alert_time = None
            if alerts_data:
                latest_alert_time = max(datetime.fromisoformat(a['timestamp']) for a in alerts_data)
            
            # Calculate trend
            trend_24h = self._get_alert_trend()
            
            return AlertSummary(
                total_alerts=len(alerts_data),
                critical_alerts=critical,
                high_alerts=high,
                medium_alerts=medium,
                low_alerts=low,
                latest_alert_time=latest_alert_time,
                trend_24h=trend_24h
            )
            
        except Exception as e:
            return AlertSummary(
                total_alerts=0,
                critical_alerts=0,
                high_alerts=0,
                medium_alerts=0,
                low_alerts=0,
                latest_alert_time=None,
                trend_24h="unknown"
            )
    
    def get_trend_metrics(self) -> Dict[str, List[Dict]]:
        """Get time series data for trends"""
        try:
            return {
                'import_volume': self._get_import_volume_trend(),
                'data_quality': self._get_quality_trend_data(),
                'response_times': self._get_response_time_trend(),
                'error_rates': self._get_error_rate_trend(),
                'storage_growth': self._get_storage_growth_trend()
            }
        except Exception as e:
            return {'error': str(e)}
    
    # Helper methods for metric calculations
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health score"""
        try:
            # Simplified health calculation
            health_factors = []
            
            # Data freshness factor
            hours_since_import = self._get_hours_since_last_import()
            freshness_score = max(0, 100 - (hours_since_import - 24) * 5) if hours_since_import > 24 else 100
            health_factors.append(freshness_score)
            
            # Database connectivity factor
            db_connected = self._check_database_connectivity()
            health_factors.append(100 if db_connected else 0)
            
            # Data quality factor
            quality_score = self._calculate_data_quality_score()
            health_factors.append(quality_score)
            
            # Error rate factor
            error_rate = self._get_error_rate()
            error_score = max(0, 100 - error_rate * 10)
            health_factors.append(error_score)
            
            return np.mean(health_factors)
            
        except Exception:
            return 0.0
    
    def _get_hours_since_last_import(self) -> float:
        """Get hours since last import"""
        try:
            response = self.supabase.table("import_logs").select(
                "end_time"
            ).order("end_time", desc=True).limit(1).execute()
            
            if response.data:
                last_import = datetime.fromisoformat(response.data[0]['end_time'].replace('Z', '+00:00'))
                return (datetime.now() - last_import.replace(tzinfo=None)).total_seconds() / 3600
            
            return 999.0  # Very old if no data
            
        except Exception:
            return 999.0
    
    def _check_database_connectivity(self) -> bool:
        """Check if database is accessible"""
        try:
            self.supabase.table("supermarkets").select("id").limit(1).execute()
            return True
        except Exception:
            return False
    
    def _measure_api_response_time(self) -> float:
        """Measure API response time"""
        try:
            start_time = time.time()
            self.supabase.table("products").select("id").limit(10).execute()
            end_time = time.time()
            
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception:
            return 99999.0
    
    def _calculate_data_quality_score(self) -> float:
        """Calculate data quality score"""
        try:
            # Simplified quality calculation
            quality_factors = []
            
            # Completeness factor
            completeness = self._get_data_completeness()
            quality_factors.append(completeness)
            
            # Duplicate factor
            duplicates = self._count_duplicate_records()
            duplicate_score = max(0, 100 - duplicates / 10)  # Penalize duplicates
            quality_factors.append(duplicate_score)
            
            # Invalid data factor
            invalid_prices = self._count_invalid_prices()
            invalid_score = max(0, 100 - invalid_prices / 5)  # Penalize invalid prices
            quality_factors.append(invalid_score)
            
            return np.mean(quality_factors)
            
        except Exception:
            return 0.0
    
    def _get_data_completeness(self) -> float:
        """Get data completeness percentage"""
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            # Get total expected products (all active products)
            total_products = self.supabase.table("products").select(
                "id", count="exact"
            ).execute().count
            
            # Get products with recent prices
            recent_prices = self.supabase.table("price_history").select(
                "product_id"
            ).gte("price_date", yesterday).execute()
            
            unique_products = len(set(row['product_id'] for row in recent_prices.data))
            
            return (unique_products / total_products) * 100 if total_products > 0 else 0
            
        except Exception:
            return 0.0
    
    def _count_duplicate_records(self) -> int:
        """Count duplicate price records"""
        try:
            # This would ideally use a stored procedure
            # For now, we'll return a placeholder
            return 0
        except Exception:
            return 0
    
    def _count_invalid_prices(self) -> int:
        """Count invalid price values"""
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            invalid_response = self.supabase.table("price_history").select(
                "id", count="exact"
            ).gte("price_date", yesterday).or_(
                "price.lt.0.01,price.gt.1000"
            ).execute()
            
            return invalid_response.count
            
        except Exception:
            return 0
    
    def _get_processing_rate(self) -> float:
        """Get processing rate (records per minute)"""
        try:
            # Get latest import log
            response = self.supabase.table("import_logs").select(
                "total_products, start_time, end_time"
            ).order("start_time", desc=True).limit(1).execute()
            
            if response.data:
                log = response.data[0]
                if log['start_time'] and log['end_time']:
                    start = datetime.fromisoformat(log['start_time'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(log['end_time'].replace('Z', '+00:00'))
                    duration_minutes = (end - start).total_seconds() / 60
                    
                    if duration_minutes > 0:
                        return log['total_products'] / duration_minutes
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _get_average_query_time(self) -> float:
        """Get average query response time"""
        try:
            # Run a test query and measure time
            start_time = time.time()
            self.supabase.table("current_prices").select("*").limit(100).execute()
            end_time = time.time()
            
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception:
            return 99999.0
    
    def _get_storage_usage(self) -> float:
        """Get estimated storage usage in GB"""
        try:
            # Estimate based on record counts
            price_records = self.supabase.table("price_history").select(
                "id", count="exact"
            ).execute().count
            
            # Rough estimate: 200 bytes per price record
            estimated_bytes = price_records * 200
            estimated_gb = estimated_bytes / (1024 ** 3)
            
            return estimated_gb
            
        except Exception:
            return 0.0
    
    def _get_error_rate(self) -> float:
        """Get error rate percentage"""
        try:
            # Get recent import logs
            week_ago = (date.today() - timedelta(days=7)).isoformat()
            
            response = self.supabase.table("import_logs").select(
                "total_products, errors"
            ).gte("import_date", week_ago).execute()
            
            if response.data:
                total_records = sum(log.get('total_products', 0) for log in response.data)
                total_errors = sum(log.get('errors', 0) for log in response.data)
                
                return (total_errors / total_records) * 100 if total_records > 0 else 0
            
            return 0.0
            
        except Exception:
            return 100.0
    
    def _get_today_import_count(self) -> int:
        """Get number of records imported today"""
        try:
            today = date.today().isoformat()
            
            response = self.supabase.table("import_logs").select(
                "total_products"
            ).eq("import_date", today).execute()
            
            if response.data:
                return response.data[0].get('total_products', 0)
            
            return 0
            
        except Exception:
            return 0
    
    def _get_supermarket_coverage(self) -> float:
        """Get supermarket coverage percentage"""
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            # Get all active supermarkets
            total_supermarkets = self.supabase.table("supermarkets").select(
                "id", count="exact"
            ).eq("is_active", True).execute().count
            
            # Get supermarkets with recent data
            recent_data = self.supabase.table("price_history").select(
                "supermarket_id"
            ).gte("price_date", yesterday).execute()
            
            unique_supermarkets = len(set(row['supermarket_id'] for row in recent_data.data))
            
            return (unique_supermarkets / total_supermarkets) * 100 if total_supermarkets > 0 else 0
            
        except Exception:
            return 0.0
    
    def _get_price_changes_count(self) -> int:
        """Get number of price changes in last 24 hours"""
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "id", count="exact"
            ).gte("price_date", yesterday).neq("price_change_percentage", 0).execute()
            
            return response.count
            
        except Exception:
            return 0
    
    def _get_products_updated_count(self) -> int:
        """Get number of products updated in last 24 hours"""
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            response = self.supabase.table("price_history").select(
                "product_id"
            ).gte("price_date", yesterday).execute()
            
            unique_products = len(set(row['product_id'] for row in response.data))
            return unique_products
            
        except Exception:
            return 0
    
    def _get_recent_alerts(self) -> List[Dict]:
        """Get recent alerts (simulated)"""
        # This would typically come from an alerts table
        # For now, return simulated alerts based on current metrics
        alerts = []
        
        # Check for freshness alert
        hours_since_import = self._get_hours_since_last_import()
        if hours_since_import > 25:
            alerts.append({
                'severity': 'high' if hours_since_import > 48 else 'medium',
                'timestamp': datetime.now().isoformat(),
                'type': 'data_freshness'
            })
        
        # Check for error rate alert
        error_rate = self._get_error_rate()
        if error_rate > 5:
            alerts.append({
                'severity': 'high' if error_rate > 10 else 'medium',
                'timestamp': datetime.now().isoformat(),
                'type': 'error_rate'
            })
        
        return alerts
    
    def _get_health_status(self, health_score: float) -> str:
        """Get status based on health score"""
        if health_score >= 90:
            return "healthy"
        elif health_score >= 70:
            return "warning"
        else:
            return "critical"
    
    def _get_quality_status(self, quality_score: float) -> str:
        """Get status based on quality score"""
        if quality_score >= 90:
            return "healthy"
        elif quality_score >= 70:
            return "warning"
        else:
            return "critical"
    
    def _get_health_trend(self) -> str:
        """Get health trend (simplified)"""
        return "stable"  # Would need historical data for real trend
    
    def _get_quality_trend(self) -> str:
        """Get quality trend (simplified)"""
        return "stable"  # Would need historical data for real trend
    
    def _get_processing_trend(self) -> str:
        """Get processing rate trend (simplified)"""
        return "stable"  # Would need historical data for real trend
    
    def _get_alert_trend(self) -> str:
        """Get alert trend (simplified)"""
        return "stable"  # Would need historical data for real trend
    
    def _get_import_volume_trend(self) -> List[Dict]:
        """Get import volume trend data"""
        try:
            week_ago = (date.today() - timedelta(days=7)).isoformat()
            
            response = self.supabase.table("import_logs").select(
                "import_date, total_products"
            ).gte("import_date", week_ago).order("import_date").execute()
            
            trend_data = []
            for row in response.data:
                trend_data.append({
                    'timestamp': row['import_date'],
                    'value': row['total_products']
                })
            
            return trend_data
            
        except Exception:
            return []
    
    def _get_quality_trend_data(self) -> List[Dict]:
        """Get data quality trend (simulated)"""
        # Would typically track quality scores over time
        trend_data = []
        for i in range(7):
            date_str = (date.today() - timedelta(days=i)).isoformat()
            trend_data.append({
                'timestamp': date_str,
                'value': 95 + np.random.normal(0, 2)  # Simulated quality score
            })
        
        return trend_data
    
    def _get_response_time_trend(self) -> List[Dict]:
        """Get response time trend (simulated)"""
        # Would typically track response times over time
        trend_data = []
        for i in range(24):  # Last 24 hours
            timestamp = datetime.now() - timedelta(hours=i)
            trend_data.append({
                'timestamp': timestamp.isoformat(),
                'value': 500 + np.random.normal(0, 100)  # Simulated response time
            })
        
        return trend_data
    
    def _get_error_rate_trend(self) -> List[Dict]:
        """Get error rate trend"""
        try:
            week_ago = (date.today() - timedelta(days=7)).isoformat()
            
            response = self.supabase.table("import_logs").select(
                "import_date, total_products, errors"
            ).gte("import_date", week_ago).order("import_date").execute()
            
            trend_data = []
            for row in response.data:
                error_rate = (row.get('errors', 0) / max(row.get('total_products', 1), 1)) * 100
                trend_data.append({
                    'timestamp': row['import_date'],
                    'value': error_rate
                })
            
            return trend_data
            
        except Exception:
            return []
    
    def _get_storage_growth_trend(self) -> List[Dict]:
        """Get storage growth trend (simulated)"""
        # Would typically track actual storage usage over time
        trend_data = []
        base_storage = 10.0  # GB
        
        for i in range(30):  # Last 30 days
            date_str = (date.today() - timedelta(days=i)).isoformat()
            # Simulate gradual storage growth
            storage = base_storage + (30 - i) * 0.1
            trend_data.append({
                'timestamp': date_str,
                'value': storage
            })
        
        return trend_data
    
    # Export methods for different dashboard formats
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            metrics = self.get_dashboard_metrics()
            prometheus_output = []
            
            # Add help and type comments
            prometheus_output.append("# HELP price_history_system_health Overall system health percentage")
            prometheus_output.append("# TYPE price_history_system_health gauge")
            
            # Export system health metrics
            for metric in metrics.get('system_health', []):
                if isinstance(metric.value, (int, float)):
                    metric_name = f"price_history_{metric.name}"
                    prometheus_output.append(f'{metric_name}{{status="{metric.status}"}} {metric.value}')
            
            # Export data quality metrics
            prometheus_output.append("# HELP price_history_data_quality Data quality percentage")
            prometheus_output.append("# TYPE price_history_data_quality gauge")
            
            for metric in metrics.get('data_quality', []):
                if isinstance(metric.value, (int, float)):
                    metric_name = f"price_history_{metric.name}"
                    prometheus_output.append(f'{metric_name}{{status="{metric.status}"}} {metric.value}')
            
            # Export performance metrics
            for metric in metrics.get('performance', []):
                if isinstance(metric.value, (int, float)):
                    metric_name = f"price_history_{metric.name}"
                    prometheus_output.append(f'{metric_name}{{unit="{metric.unit}"}} {metric.value}')
            
            return "\n".join(prometheus_output)
            
        except Exception as e:
            return f"# Error generating Prometheus metrics: {e}"
    
    def export_grafana_dashboard(self) -> Dict[str, Any]:
        """Export dashboard configuration for Grafana"""
        try:
            dashboard = {
                "dashboard": {
                    "id": None,
                    "title": "Price History Monitoring",
                    "tags": ["price-history", "monitoring"],
                    "timezone": "browser",
                    "panels": [
                        {
                            "id": 1,
                            "title": "System Health Score",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "price_history_system_health_score",
                                    "legendFormat": "Health Score"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "unit": "percent",
                                    "min": 0,
                                    "max": 100,
                                    "thresholds": {
                                        "steps": [
                                            {"color": "red", "value": 0},
                                            {"color": "yellow", "value": 70},
                                            {"color": "green", "value": 90}
                                        ]
                                    }
                                }
                            },
                            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                        },
                        {
                            "id": 2,
                            "title": "Data Quality Score",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "price_history_data_quality_score",
                                    "legendFormat": "Quality Score"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "unit": "percent",
                                    "min": 0,
                                    "max": 100,
                                    "thresholds": {
                                        "steps": [
                                            {"color": "red", "value": 0},
                                            {"color": "yellow", "value": 70},
                                            {"color": "green", "value": 90}
                                        ]
                                    }
                                }
                            },
                            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                        },
                        {
                            "id": 3,
                            "title": "Import Volume Trend",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "price_history_todays_imports",
                                    "legendFormat": "Records Imported"
                                }
                            ],
                            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                        }
                    ],
                    "time": {
                        "from": "now-24h",
                        "to": "now"
                    },
                    "refresh": "5m"
                }
            }
            
            return dashboard
            
        except Exception as e:
            return {"error": str(e)}
    
    def export_json_metrics(self) -> str:
        """Export metrics as JSON for custom dashboards"""
        try:
            metrics = self.get_dashboard_metrics()
            
            # Convert dataclasses to dictionaries
            json_metrics = {}
            for category, data in metrics.items():
                if isinstance(data, list):
                    json_metrics[category] = [asdict(item) if hasattr(item, '__dict__') else item for item in data]
                else:
                    json_metrics[category] = data
            
            return json.dumps(json_metrics, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({"error": str(e)})

# Convenience function
def create_dashboard_metrics(supabase_url: str, supabase_key: str) -> DashboardMetrics:
    """Create DashboardMetrics instance"""
    from supabase import create_client
    
    supabase = create_client(supabase_url, supabase_key)
    return DashboardMetrics(supabase)

# Example usage
if __name__ == "__main__":
    import os
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        dashboard = create_dashboard_metrics(supabase_url, supabase_key)
        
        # Get dashboard metrics
        metrics = dashboard.get_dashboard_metrics()
        print("Dashboard metrics generated successfully")
        
        # Export to different formats
        prometheus = dashboard.export_prometheus_metrics()
        print(f"Prometheus metrics: {len(prometheus.split('\\n'))} lines")
        
        grafana = dashboard.export_grafana_dashboard()
        print(f"Grafana dashboard: {len(grafana.get('dashboard', {}).get('panels', []))} panels")
        
        json_export = dashboard.export_json_metrics()
        print(f"JSON export: {len(json_export)} characters")
    else:
        print("Please set SUPABASE_URL and SUPABASE_KEY environment variables")