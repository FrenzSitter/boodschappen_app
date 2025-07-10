#!/usr/bin/env python3
"""
Metrics Exporter for Price History System
=========================================

Exports custom metrics for Prometheus monitoring including
business metrics, data quality, and system health indicators.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Thread
import asyncio

from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
from supabase import create_client, Client

from monitoring_system import create_monitor
from backup.backup_manager import create_backup_manager


# Prometheus metrics
SYSTEM_HEALTH_SCORE = Gauge('price_history_system_health_score', 'Overall system health score (0-100)')
DATA_FRESHNESS_HOURS = Gauge('price_history_data_freshness_hours', 'Hours since last data import')
DATA_QUALITY_SCORE = Gauge('price_history_data_quality_score', 'Data quality score (0-100)')

IMPORT_SUCCESS = Gauge('price_history_import_success', 'Import success status (1=success, 0=failed)')
IMPORT_RECORDS_PROCESSED = Gauge('price_history_import_records_processed', 'Records processed in last import')
IMPORT_DURATION_SECONDS = Gauge('price_history_import_duration_seconds', 'Import duration in seconds')
IMPORT_PRICE_CHANGES = Gauge('price_history_import_price_changes', 'Price changes detected in last import')

BACKUP_SUCCESS = Gauge('price_history_backup_success', 'Backup success status (1=success, 0=failed)')
BACKUP_HOURS_SINCE_LAST = Gauge('price_history_backup_hours_since_last', 'Hours since last backup')
BACKUP_SIZE_MB = Gauge('price_history_backup_size_mb', 'Size of last backup in MB')

ANOMALY_COUNT = Gauge('price_history_anomaly_count', 'Number of price anomalies detected')
SUPERMARKET_COVERAGE = Gauge('price_history_supermarket_coverage', 'Percentage of supermarkets with data')
VOLATILITY_PRODUCTS = Gauge('price_history_volatility_products', 'Number of products with high volatility')

API_REQUEST_DURATION = Histogram('price_history_api_request_duration_seconds', 'API request duration')
API_REQUESTS_TOTAL = Counter('price_history_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])

DATABASE_CONNECTIONS = Gauge('price_history_database_connections', 'Number of database connections')
CACHE_HIT_RATE = Gauge('price_history_cache_hit_rate', 'Cache hit rate percentage')
CACHE_MEMORY_USAGE = Gauge('price_history_cache_memory_usage_bytes', 'Cache memory usage in bytes')

SYSTEM_INFO = Info('price_history_system_info', 'System information')


class MetricsExporter:
    """Main metrics exporter class"""
    
    def __init__(self, supabase_url: str, supabase_key: str, port: int = 8001):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.port = port
        self.logger = self._setup_logging()
        
        # Initialize clients
        self.supabase = create_client(supabase_url, supabase_key)
        self.monitor = create_monitor(supabase_url, supabase_key)
        self.backup_manager = create_backup_manager(supabase_url, supabase_key)
        
        # Metrics collection interval
        self.collection_interval = 30  # seconds
        self.running = False
        
        # Set system info
        SYSTEM_INFO.info({
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'deployment': 'docker'
        })
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('metrics_exporter')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('/app/logs/metrics.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start(self):
        """Start the metrics exporter"""
        self.logger.info(f"Starting metrics exporter on port {self.port}")
        
        # Start Prometheus HTTP server
        start_http_server(self.port)
        
        # Start metrics collection
        self.running = True
        collection_thread = Thread(target=self._collect_metrics_loop, daemon=True)
        collection_thread.start()
        
        self.logger.info("Metrics exporter started successfully")
    
    def stop(self):
        """Stop the metrics exporter"""
        self.running = False
        self.logger.info("Metrics exporter stopped")
    
    def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                self._collect_all_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                time.sleep(5)  # Wait before retry
    
    def _collect_all_metrics(self):
        """Collect all metrics"""
        try:
            # System health metrics
            self._collect_system_health_metrics()
            
            # Data metrics
            self._collect_data_metrics()
            
            # Import metrics
            self._collect_import_metrics()
            
            # Backup metrics
            self._collect_backup_metrics()
            
            # Business metrics
            self._collect_business_metrics()
            
            # Infrastructure metrics
            self._collect_infrastructure_metrics()
            
        except Exception as e:
            self.logger.error(f"Error in metrics collection: {e}")
    
    def _collect_system_health_metrics(self):
        """Collect system health metrics"""
        try:
            # Run monitoring check
            monitoring_result = self.monitor.run_full_monitoring()
            
            health_score = monitoring_result.get('overall_health_percentage', 0)
            SYSTEM_HEALTH_SCORE.set(health_score)
            
            self.logger.debug(f"System health score: {health_score}")
            
        except Exception as e:
            self.logger.error(f"Error collecting system health metrics: {e}")
            SYSTEM_HEALTH_SCORE.set(0)
    
    def _collect_data_metrics(self):
        """Collect data-related metrics"""
        try:
            # Data freshness
            freshness_result = self.monitor.check_data_freshness()
            
            if freshness_result['status'] == 'completed':
                hours_since_import = freshness_result['hours_since_import']
                DATA_FRESHNESS_HOURS.set(hours_since_import)
                
                # Supermarket coverage
                coverage = freshness_result['supermarket_coverage']
                coverage_percentage = coverage['coverage_percentage']
                SUPERMARKET_COVERAGE.set(coverage_percentage / 100)
                
                self.logger.debug(f"Data freshness: {hours_since_import} hours")
                self.logger.debug(f"Supermarket coverage: {coverage_percentage}%")
            
            # Data quality
            quality_result = self.monitor.run_data_quality_checks()
            
            if quality_result['status'] == 'completed':
                quality_score = quality_result['overall_quality_score']
                DATA_QUALITY_SCORE.set(quality_score)
                
                self.logger.debug(f"Data quality score: {quality_score}")
            
        except Exception as e:
            self.logger.error(f"Error collecting data metrics: {e}")
    
    def _collect_import_metrics(self):
        """Collect import-related metrics"""
        try:
            # Get latest import log
            import_logs = self.supabase.table('import_logs').select('*').order('created_at', desc=True).limit(1).execute()
            
            if import_logs.data:
                latest_import = import_logs.data[0]
                
                # Import success status
                success = 1 if latest_import.get('status') == 'completed' else 0
                IMPORT_SUCCESS.set(success)
                
                # Records processed
                records_processed = latest_import.get('products_processed', 0)
                IMPORT_RECORDS_PROCESSED.set(records_processed)
                
                # Import duration
                duration_minutes = latest_import.get('duration_minutes', 0)
                IMPORT_DURATION_SECONDS.set(duration_minutes * 60)
                
                # Price changes
                price_changes = latest_import.get('price_changes', 0)
                IMPORT_PRICE_CHANGES.set(price_changes)
                
                self.logger.debug(f"Import success: {success}, Records: {records_processed}")
            
        except Exception as e:
            self.logger.error(f"Error collecting import metrics: {e}")
    
    def _collect_backup_metrics(self):
        """Collect backup-related metrics"""
        try:
            # Backup status
            backup_status = self.backup_manager.get_backup_status()
            
            if backup_status['status'] != 'error':
                # Success status
                success = 1 if backup_status['status'] == 'healthy' else 0
                BACKUP_SUCCESS.set(success)
                
                # Hours since last backup
                hours_since_last = backup_status.get('hours_since_last', 999)
                BACKUP_HOURS_SINCE_LAST.set(hours_since_last)
                
                # Backup size
                if backup_status.get('last_backup'):
                    size_bytes = backup_status['last_backup'].get('size_bytes', 0)
                    size_mb = size_bytes / (1024 * 1024)
                    BACKUP_SIZE_MB.set(size_mb)
                
                self.logger.debug(f"Backup status: {backup_status['status']}, Hours: {hours_since_last}")
            
        except Exception as e:
            self.logger.error(f"Error collecting backup metrics: {e}")
    
    def _collect_business_metrics(self):
        """Collect business-related metrics"""
        try:
            # Price anomalies
            anomaly_result = self.monitor.detect_price_anomalies(days=1)
            
            if anomaly_result['status'] == 'completed':
                total_anomalies = anomaly_result['total_issues']
                ANOMALY_COUNT.set(total_anomalies)
                
                self.logger.debug(f"Price anomalies: {total_anomalies}")
            
            # Volatility products
            try:
                # Get products with high volatility
                volatility_query = """
                    SELECT COUNT(*) as volatile_count
                    FROM products p
                    WHERE EXISTS (
                        SELECT 1 FROM price_history ph
                        WHERE ph.product_id = p.id
                        AND ph.price_date >= NOW() - INTERVAL '7 days'
                        GROUP BY ph.product_id
                        HAVING STDDEV(ph.price) / AVG(ph.price) > 0.2
                    )
                """
                
                # This would require a direct SQL query - simplified for demo
                VOLATILITY_PRODUCTS.set(0)  # Placeholder
                
            except Exception as e:
                self.logger.debug(f"Error collecting volatility metrics: {e}")
                VOLATILITY_PRODUCTS.set(0)
            
        except Exception as e:
            self.logger.error(f"Error collecting business metrics: {e}")
    
    def _collect_infrastructure_metrics(self):
        """Collect infrastructure metrics"""
        try:
            # Database connections (simplified)
            DATABASE_CONNECTIONS.set(1)  # Placeholder
            
            # Cache metrics (if Redis is available)
            try:
                import redis
                redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
                
                info = redis_client.info()
                
                # Cache hit rate
                hit_rate = info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
                CACHE_HIT_RATE.set(hit_rate * 100)
                
                # Memory usage
                memory_used = info.get('used_memory', 0)
                CACHE_MEMORY_USAGE.set(memory_used)
                
                self.logger.debug(f"Cache hit rate: {hit_rate:.2%}, Memory: {memory_used} bytes")
                
            except Exception as e:
                self.logger.debug(f"Error collecting cache metrics: {e}")
                CACHE_HIT_RATE.set(0)
                CACHE_MEMORY_USAGE.set(0)
            
        except Exception as e:
            self.logger.error(f"Error collecting infrastructure metrics: {e}")
    
    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record API request metrics"""
        try:
            # Record request
            API_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            
            # Record duration
            API_REQUEST_DURATION.observe(duration)
            
        except Exception as e:
            self.logger.error(f"Error recording API request: {e}")


def main():
    """Main entry point for standalone metrics exporter"""
    import signal
    import sys
    
    def signal_handler(signum, frame):
        print("Shutting down metrics exporter...")
        if 'exporter' in globals():
            exporter.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get configuration
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    port = int(os.getenv('METRICS_PORT', '8001'))
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables required")
        sys.exit(1)
    
    # Create and start exporter
    exporter = MetricsExporter(supabase_url, supabase_key, port)
    exporter.start()
    
    print(f"Metrics exporter running on port {port}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        exporter.stop()


if __name__ == "__main__":
    main()