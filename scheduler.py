#!/usr/bin/env python3
"""
Automated Scheduler for Price History System
===========================================

Handles scheduled tasks for data import, monitoring, and maintenance
using cron-like scheduling with proper error handling and logging.
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from threading import Thread, Event
import schedule
import asyncio
from contextlib import asynccontextmanager

from import_checkjebon import CheckjeBonImporter
from monitoring_system import create_monitor
from backup.backup_manager import BackupManager


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    name: str
    schedule: str
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutes
    timeout: int = 3600  # 1 hour
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class TaskScheduler:
    """Main scheduler for all automated tasks"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.tasks: List[ScheduledTask] = []
        self.shutdown_event = Event()
        self.running_tasks: Dict[str, Thread] = {}
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Initialize task definitions
        self._setup_tasks()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_level = self.config.get('LOG_LEVEL', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/logs/scheduler.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger('scheduler')
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()
    
    def _setup_tasks(self):
        """Setup all scheduled tasks"""
        # Daily import task
        import_schedule = self.config.get('IMPORT_SCHEDULE', '0 6 * * *')
        self.add_task(ScheduledTask(
            name="daily_import",
            schedule=import_schedule,
            function=self._run_daily_import,
            timeout=7200  # 2 hours
        ))
        
        # Monitoring task
        monitoring_schedule = self.config.get('MONITORING_SCHEDULE', '0 */6 * * *')
        self.add_task(ScheduledTask(
            name="monitoring_check",
            schedule=monitoring_schedule,
            function=self._run_monitoring_check,
            timeout=1800  # 30 minutes
        ))
        
        # Daily backup task
        backup_schedule = self.config.get('BACKUP_SCHEDULE', '0 2 * * *')
        self.add_task(ScheduledTask(
            name="daily_backup",
            schedule=backup_schedule,
            function=self._run_daily_backup,
            timeout=3600  # 1 hour
        ))
        
        # Weekly maintenance task
        self.add_task(ScheduledTask(
            name="weekly_maintenance",
            schedule="0 1 * * 0",  # Sunday 1 AM
            function=self._run_weekly_maintenance,
            timeout=5400  # 1.5 hours
        ))
        
        # Health check task
        self.add_task(ScheduledTask(
            name="health_check",
            schedule="*/5 * * * *",  # Every 5 minutes
            function=self._run_health_check,
            timeout=300  # 5 minutes
        ))
    
    def add_task(self, task: ScheduledTask):
        """Add a task to the scheduler"""
        if task.enabled:
            self.tasks.append(task)
            self.logger.info(f"Added task: {task.name} with schedule: {task.schedule}")
    
    def _run_task_with_retry(self, task: ScheduledTask):
        """Run a task with retry logic"""
        for attempt in range(task.max_retries + 1):
            try:
                self.logger.info(f"Running task: {task.name} (attempt {attempt + 1})")
                
                # Set up timeout
                start_time = time.time()
                result = task.function(*task.args, **task.kwargs)
                duration = time.time() - start_time
                
                self.logger.info(f"Task {task.name} completed successfully in {duration:.2f}s")
                return result
                
            except Exception as e:
                self.logger.error(f"Task {task.name} failed (attempt {attempt + 1}): {e}")
                
                if attempt < task.max_retries:
                    self.logger.info(f"Retrying task {task.name} in {task.retry_delay}s...")
                    time.sleep(task.retry_delay)
                else:
                    self.logger.error(f"Task {task.name} failed after {task.max_retries + 1} attempts")
                    # Send alert about failed task
                    self._send_task_failure_alert(task.name, str(e))
    
    def _run_daily_import(self):
        """Run daily CheckjeBon import"""
        self.logger.info("Starting daily import...")
        
        # Run async import
        asyncio.run(self._async_daily_import())
    
    async def _async_daily_import(self):
        """Async wrapper for daily import"""
        try:
            async with CheckjeBonImporter() as importer:
                result = await importer.run_import()
                
                self.logger.info(f"Import completed: {result['products_processed']} products, "
                               f"{result['prices_updated']} prices updated")
                
                # Send success notification
                await self._send_import_success_notification(result)
                
        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            raise
    
    def _run_monitoring_check(self):
        """Run monitoring checks"""
        self.logger.info("Starting monitoring check...")
        
        try:
            monitor = create_monitor(
                supabase_url=os.getenv('SUPABASE_URL'),
                supabase_key=os.getenv('SUPABASE_KEY')
            )
            
            result = monitor.run_full_monitoring()
            
            self.logger.info(f"Monitoring completed: {result['alerts_triggered']} alerts triggered")
            
            # Generate and send reports if needed
            if result.get('alerts_triggered', 0) > 0:
                daily_report = monitor.generate_daily_report()
                monitor.send_report_notification(daily_report)
                
        except Exception as e:
            self.logger.error(f"Monitoring check failed: {e}")
            raise
    
    def _run_daily_backup(self):
        """Run daily backup"""
        self.logger.info("Starting daily backup...")
        
        try:
            backup_manager = BackupManager(
                supabase_url=os.getenv('SUPABASE_URL'),
                supabase_key=os.getenv('SUPABASE_KEY')
            )
            
            result = backup_manager.run_daily_backup()
            
            self.logger.info(f"Backup completed: {result['backup_size_mb']} MB, "
                           f"saved to {result['backup_location']}")
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise
    
    def _run_weekly_maintenance(self):
        """Run weekly maintenance tasks"""
        self.logger.info("Starting weekly maintenance...")
        
        try:
            monitor = create_monitor(
                supabase_url=os.getenv('SUPABASE_URL'),
                supabase_key=os.getenv('SUPABASE_KEY')
            )
            
            result = monitor.run_data_maintenance()
            
            self.logger.info(f"Maintenance completed: {result['operations']['total_operations']} operations")
            
        except Exception as e:
            self.logger.error(f"Maintenance failed: {e}")
            raise
    
    def _run_health_check(self):
        """Run health check"""
        try:
            monitor = create_monitor(
                supabase_url=os.getenv('SUPABASE_URL'),
                supabase_key=os.getenv('SUPABASE_KEY')
            )
            
            freshness_result = monitor.check_data_freshness()
            
            if freshness_result['hours_since_import'] > 26:
                self.logger.warning("Data freshness check failed - import may be overdue")
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    def _send_task_failure_alert(self, task_name: str, error: str):
        """Send alert about task failure"""
        try:
            monitor = create_monitor(
                supabase_url=os.getenv('SUPABASE_URL'),
                supabase_key=os.getenv('SUPABASE_KEY')
            )
            
            alert_subject = f"Task Failure Alert: {task_name}"
            alert_body = f"""
            Task: {task_name}
            Status: FAILED
            Error: {error}
            Time: {datetime.now().isoformat()}
            
            Please investigate and resolve the issue.
            """
            
            recipients = os.getenv('ALERT_RECIPIENTS', '').split(',')
            if recipients:
                monitor.send_email_notification(
                    subject=alert_subject,
                    body=alert_body,
                    recipients=recipients
                )
                
        except Exception as e:
            self.logger.error(f"Failed to send task failure alert: {e}")
    
    async def _send_import_success_notification(self, result: Dict):
        """Send success notification for import"""
        try:
            subject = f"Daily Import Success - {result['products_processed']} products processed"
            body = f"""
            Daily import completed successfully:
            
            Products processed: {result['products_processed']}
            Prices updated: {result['prices_updated']}
            Price changes detected: {result['price_changes']}
            Duration: {result['duration_minutes']:.1f} minutes
            
            System is operating normally.
            """
            
            # Only send if configured
            if os.getenv('SEND_SUCCESS_NOTIFICATIONS', 'false').lower() == 'true':
                monitor = create_monitor(
                    supabase_url=os.getenv('SUPABASE_URL'),
                    supabase_key=os.getenv('SUPABASE_KEY')
                )
                
                recipients = os.getenv('REPORT_RECIPIENTS', '').split(',')
                if recipients:
                    monitor.send_email_notification(
                        subject=subject,
                        body=body,
                        recipients=recipients
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to send success notification: {e}")
    
    def _parse_cron_schedule(self, cron_expr: str) -> str:
        """Convert cron expression to schedule format"""
        # This is a simplified parser - in production, use a proper cron parser
        parts = cron_expr.split()
        
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
        
        minute, hour, day, month, weekday = parts
        
        # Convert to schedule format
        if minute == "0" and hour != "*":
            if weekday != "*":
                return f"weekly.{weekday}.at(\"{hour}:00\")"
            elif day != "*":
                return f"monthly.at(\"{hour}:00\")"
            else:
                return f"daily.at(\"{hour}:00\")"
        elif minute != "*" and hour != "*":
            return f"daily.at(\"{hour}:{minute}\")"
        elif minute.startswith("*/"):
            interval = int(minute[2:])
            return f"every({interval}).minutes"
        else:
            return f"every().hour"
    
    def start(self):
        """Start the scheduler"""
        self.logger.info("Starting task scheduler...")
        
        # Schedule all tasks
        for task in self.tasks:
            try:
                # Parse cron schedule and add to schedule
                self._schedule_task(task)
                self.logger.info(f"Scheduled task: {task.name}")
            except Exception as e:
                self.logger.error(f"Failed to schedule task {task.name}: {e}")
        
        # Main scheduling loop
        while not self.shutdown_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)
        
        self.logger.info("Scheduler stopped")
    
    def _schedule_task(self, task: ScheduledTask):
        """Schedule a single task"""
        def task_wrapper():
            # Run task in separate thread to avoid blocking
            if task.name not in self.running_tasks:
                thread = Thread(
                    target=self._run_task_with_retry,
                    args=(task,),
                    name=f"task-{task.name}"
                )
                thread.daemon = True
                self.running_tasks[task.name] = thread
                thread.start()
            else:
                self.logger.warning(f"Task {task.name} is already running, skipping...")
        
        # Parse cron schedule
        parts = task.schedule.split()
        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            
            if minute == "0" and hour != "*" and weekday == "*":
                # Daily at specific hour
                schedule.every().day.at(f"{hour}:00").do(task_wrapper)
            elif minute.startswith("*/"):
                # Every X minutes
                interval = int(minute[2:])
                schedule.every(interval).minutes.do(task_wrapper)
            elif minute == "0" and hour.startswith("*/"):
                # Every X hours
                interval = int(hour[2:])
                schedule.every(interval).hours.do(task_wrapper)
            else:
                # Specific time
                if minute != "*" and hour != "*":
                    schedule.every().day.at(f"{hour}:{minute}").do(task_wrapper)
    
    def stop(self):
        """Stop the scheduler"""
        self.logger.info("Stopping scheduler...")
        self.shutdown_event.set()
        
        # Wait for running tasks to complete
        for task_name, thread in self.running_tasks.items():
            if thread.is_alive():
                self.logger.info(f"Waiting for task {task_name} to complete...")
                thread.join(timeout=30)
                if thread.is_alive():
                    self.logger.warning(f"Task {task_name} did not complete within timeout")


def main():
    """Main entry point"""
    config = {
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'IMPORT_SCHEDULE': os.getenv('IMPORT_SCHEDULE', '0 6 * * *'),
        'MONITORING_SCHEDULE': os.getenv('MONITORING_SCHEDULE', '0 */6 * * *'),
        'BACKUP_SCHEDULE': os.getenv('BACKUP_SCHEDULE', '0 2 * * *'),
    }
    
    scheduler = TaskScheduler(config)
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()
    except Exception as e:
        logging.error(f"Scheduler failed: {e}")
        scheduler.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()