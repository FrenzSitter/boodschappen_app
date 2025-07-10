#!/usr/bin/env python3
"""
Data Validation Dashboard
========================

Interactive dashboard for monitoring data validation results,
health reports, and system status.

Features:
- Interactive web dashboard
- Real-time validation status
- Historical trend analysis
- Alert management
- Health report viewer

Author: Generated for boodschappen_app
Date: 2025-01-09
"""

import os
import sys
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from flask import Flask, render_template_string, jsonify, request
    import sqlite3
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Run: pip install flask")
    sys.exit(1)

# Configuration
HEALTH_REPORT_DIR = "logs/health_reports"
VALIDATION_LOG_FILE = "logs/data_validation.log"
DASHBOARD_DB = "logs/validation_dashboard.db"

class ValidationDashboard:
    """Dashboard for validation monitoring"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_database()
        self.setup_routes()
    
    def setup_database(self):
        """Setup SQLite database for dashboard data"""
        os.makedirs(os.path.dirname(DASHBOARD_DB), exist_ok=True)
        
        conn = sqlite3.connect(DASHBOARD_DB)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                total_checks INTEGER,
                passed_checks INTEGER,
                warning_checks INTEGER,
                failed_checks INTEGER,
                duration_seconds INTEGER,
                status TEXT,
                alerts TEXT,
                recommendations TEXT,
                report_file TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                check_name TEXT,
                status TEXT,
                message TEXT,
                details TEXT,
                timestamp TEXT,
                FOREIGN KEY (run_id) REFERENCES validation_runs (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                metric_name TEXT,
                metric_value REAL,
                metric_unit TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_health_reports(self) -> List[Dict]:
        """Load health reports from files"""
        reports = []
        
        try:
            report_files = glob.glob(f"{HEALTH_REPORT_DIR}/health_report_*.json")
            report_files.sort(reverse=True)  # Latest first
            
            for report_file in report_files[:30]:  # Last 30 reports
                try:
                    with open(report_file, 'r') as f:
                        report = json.load(f)
                        reports.append(report)
                except Exception as e:
                    print(f"Error loading report {report_file}: {e}")
        
        except Exception as e:
            print(f"Error loading health reports: {e}")
        
        return reports
    
    def get_validation_summary(self) -> Dict:
        """Get validation summary statistics"""
        reports = self.load_health_reports()
        
        if not reports:
            return {
                "total_runs": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "recent_status": "No Data",
                "alerts_count": 0
            }
        
        total_runs = len(reports)
        successful_runs = len([r for r in reports if r.get("failed_checks", 0) == 0])
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        # Calculate average duration (if available)
        durations = []
        for report in reports:
            if "validation_results" in report:
                # Estimate duration from timestamp differences
                results = report["validation_results"]
                if len(results) > 1:
                    first_time = datetime.fromisoformat(results[0]["timestamp"].replace('Z', '+00:00'))
                    last_time = datetime.fromisoformat(results[-1]["timestamp"].replace('Z', '+00:00'))
                    duration = (last_time - first_time).total_seconds()
                    durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        recent_report = reports[0] if reports else {}
        recent_status = "PASS" if recent_report.get("failed_checks", 0) == 0 else "FAIL"
        alerts_count = len(recent_report.get("alerts", []))
        
        return {
            "total_runs": total_runs,
            "success_rate": round(success_rate, 1),
            "avg_duration": round(avg_duration, 1),
            "recent_status": recent_status,
            "alerts_count": alerts_count,
            "recent_report": recent_report
        }
    
    def get_trend_data(self, days: int = 7) -> Dict:
        """Get trend data for the last N days"""
        reports = self.load_health_reports()
        
        # Group by date
        date_data = {}
        for report in reports:
            report_date = report.get("date", "unknown")
            if report_date not in date_data:
                date_data[report_date] = {
                    "date": report_date,
                    "runs": 0,
                    "passed": 0,
                    "warnings": 0,
                    "failures": 0,
                    "alerts": 0
                }
            
            date_data[report_date]["runs"] += 1
            date_data[report_date]["passed"] += report.get("passed_checks", 0)
            date_data[report_date]["warnings"] += report.get("warning_checks", 0)
            date_data[report_date]["failures"] += report.get("failed_checks", 0)
            date_data[report_date]["alerts"] += len(report.get("alerts", []))
        
        # Sort by date and limit to last N days
        sorted_data = sorted(date_data.values(), key=lambda x: x["date"], reverse=True)[:days]
        
        return {
            "dates": [d["date"] for d in reversed(sorted_data)],
            "runs": [d["runs"] for d in reversed(sorted_data)],
            "passed": [d["passed"] for d in reversed(sorted_data)],
            "warnings": [d["warnings"] for d in reversed(sorted_data)],
            "failures": [d["failures"] for d in reversed(sorted_data)],
            "alerts": [d["alerts"] for d in reversed(sorted_data)]
        }
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/summary')
        def api_summary():
            """API endpoint for validation summary"""
            return jsonify(self.get_validation_summary())
        
        @self.app.route('/api/trends')
        def api_trends():
            """API endpoint for trend data"""
            days = request.args.get('days', 7, type=int)
            return jsonify(self.get_trend_data(days))
        
        @self.app.route('/api/reports')
        def api_reports():
            """API endpoint for health reports"""
            reports = self.load_health_reports()
            return jsonify(reports[:10])  # Last 10 reports
        
        @self.app.route('/api/report/<date>')
        def api_report(date):
            """API endpoint for specific report"""
            report_file = f"{HEALTH_REPORT_DIR}/health_report_{date}.json"
            
            if os.path.exists(report_file):
                with open(report_file, 'r') as f:
                    report = json.load(f)
                return jsonify(report)
            else:
                return jsonify({"error": "Report not found"}), 404
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the dashboard"""
        print(f"🚀 Starting Validation Dashboard on http://{host}:{port}")
        print("📊 Dashboard features:")
        print("  • Real-time validation status")
        print("  • Historical trend analysis")
        print("  • Health report viewer")
        print("  • Alert management")
        print("\nPress Ctrl+C to stop")
        
        self.app.run(host=host, port=port, debug=debug)

# HTML template for dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>CheckjeBon Data Validation Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-value.success { color: #28a745; }
        .metric-value.warning { color: #ffc107; }
        .metric-value.danger { color: #dc3545; }
        .metric-value.info { color: #17a2b8; }
        .metric-label {
            color: #6c757d;
            font-size: 0.9em;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .chart-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #495057;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-pass { background-color: #28a745; }
        .status-warn { background-color: #ffc107; }
        .status-fail { background-color: #dc3545; }
        .alert-list {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .alert-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #dc3545;
            background-color: #f8d7da;
            border-radius: 5px;
        }
        .recommendation-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #17a2b8;
            background-color: #d1ecf1;
            border-radius: 5px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        .refresh-button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
        }
        .refresh-button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 CheckjeBon Data Validation Dashboard</h1>
            <p>Real-time monitoring of data quality and system health</p>
        </div>

        <button class="refresh-button" onclick="refreshData()">🔄 Refresh Data</button>

        <div class="metrics-grid" id="metricsGrid">
            <div class="loading">Loading metrics...</div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📈 Validation Trends (Last 7 Days)</div>
            <canvas id="trendsChart" width="400" height="200"></canvas>
        </div>

        <div class="alert-list" id="alertsList">
            <div class="loading">Loading alerts...</div>
        </div>
    </div>

    <script>
        let trendsChart;

        async function fetchData(endpoint) {
            try {
                const response = await fetch(`/api/${endpoint}`);
                return await response.json();
            } catch (error) {
                console.error(`Error fetching ${endpoint}:`, error);
                return null;
            }
        }

        function createMetricCard(title, value, status, unit = '') {
            const statusClass = status === 'PASS' ? 'success' : 
                               status === 'WARN' ? 'warning' : 
                               status === 'FAIL' ? 'danger' : 'info';
            
            return `
                <div class="metric-card">
                    <div class="metric-label">${title}</div>
                    <div class="metric-value ${statusClass}">${value}${unit}</div>
                </div>
            `;
        }

        function updateMetrics(summary) {
            const metricsGrid = document.getElementById('metricsGrid');
            
            metricsGrid.innerHTML = [
                createMetricCard('Total Runs', summary.total_runs, 'info'),
                createMetricCard('Success Rate', summary.success_rate, 
                    summary.success_rate > 95 ? 'PASS' : 
                    summary.success_rate > 80 ? 'WARN' : 'FAIL', '%'),
                createMetricCard('Avg Duration', summary.avg_duration, 'info', 's'),
                createMetricCard('Recent Status', 
                    summary.recent_status === 'PASS' ? '✅ PASS' : '❌ FAIL', 
                    summary.recent_status),
                createMetricCard('Active Alerts', summary.alerts_count, 
                    summary.alerts_count === 0 ? 'PASS' : 'FAIL')
            ].join('');
        }

        function updateTrendsChart(trends) {
            const ctx = document.getElementById('trendsChart').getContext('2d');
            
            if (trendsChart) {
                trendsChart.destroy();
            }

            trendsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trends.dates,
                    datasets: [
                        {
                            label: 'Passed Checks',
                            data: trends.passed,
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Warning Checks',
                            data: trends.warnings,
                            borderColor: '#ffc107',
                            backgroundColor: 'rgba(255, 193, 7, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Failed Checks',
                            data: trends.failures,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        }

        function updateAlerts(summary) {
            const alertsList = document.getElementById('alertsList');
            const recentReport = summary.recent_report || {};
            const alerts = recentReport.alerts || [];
            const recommendations = recentReport.recommendations || [];

            let html = '<div class="chart-title">🚨 Recent Alerts & Recommendations</div>';

            if (alerts.length === 0 && recommendations.length === 0) {
                html += '<p style="color: #28a745; text-align: center; padding: 20px;">✅ No alerts or recommendations</p>';
            } else {
                if (alerts.length > 0) {
                    html += '<h3>Alerts</h3>';
                    alerts.forEach(alert => {
                        html += `<div class="alert-item">⚠️ ${alert}</div>`;
                    });
                }

                if (recommendations.length > 0) {
                    html += '<h3>Recommendations</h3>';
                    recommendations.forEach(rec => {
                        html += `<div class="recommendation-item">💡 ${rec}</div>`;
                    });
                }
            }

            alertsList.innerHTML = html;
        }

        async function refreshData() {
            console.log('Refreshing dashboard data...');
            
            const [summary, trends] = await Promise.all([
                fetchData('summary'),
                fetchData('trends')
            ]);

            if (summary) {
                updateMetrics(summary);
                updateAlerts(summary);
            }

            if (trends) {
                updateTrendsChart(trends);
            }
        }

        // Initial load
        refreshData();

        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
'''

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='CheckjeBon Data Validation Dashboard')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create dashboard
    dashboard = ValidationDashboard()
    
    # Run dashboard
    dashboard.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()