#!/usr/bin/env python3
"""
Email Notification System for CheckjeBon Import
===============================================

This module provides email notification functionality for import failures
and status updates.
"""

import smtplib
import ssl
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging
from typing import Optional, List
import json

# Configuration
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_TIMEOUT = 30

class EmailNotifier:
    """Email notification system for CheckjeBon imports"""
    
    def __init__(self, 
                 smtp_host: str = None,
                 smtp_port: int = DEFAULT_SMTP_PORT,
                 smtp_user: str = None,
                 smtp_password: str = None,
                 from_email: str = None,
                 enabled: bool = True):
        
        self.smtp_host = smtp_host or os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(smtp_port or os.getenv('EMAIL_SMTP_PORT', DEFAULT_SMTP_PORT))
        self.smtp_user = smtp_user or os.getenv('EMAIL_SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('EMAIL_SMTP_PASSWORD')
        self.from_email = from_email or os.getenv('EMAIL_FROM', self.smtp_user)
        self.enabled = enabled and (os.getenv('EMAIL_ENABLED', 'false').lower() == 'true')
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Validate configuration
        if self.enabled:
            self._validate_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for email notifications"""
        logger = logging.getLogger('email_notifier')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _validate_config(self) -> None:
        """Validate email configuration"""
        if not self.smtp_host:
            raise ValueError("SMTP host is required")
        if not self.smtp_user:
            raise ValueError("SMTP user is required")
        if not self.smtp_password:
            raise ValueError("SMTP password is required")
        if not self.from_email:
            raise ValueError("From email is required")
    
    def send_email(self, 
                   to_emails: List[str],
                   subject: str,
                   body: str,
                   html_body: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Send email notification
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of file paths to attach (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.info("Email notifications disabled")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=DEFAULT_SMTP_TIMEOUT) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def send_failure_notification(self, 
                                  to_emails: List[str],
                                  exit_code: int,
                                  duration: int,
                                  error_details: str,
                                  log_file: str = None) -> bool:
        """
        Send failure notification email
        
        Args:
            to_emails: List of recipient email addresses
            exit_code: Exit code of failed process
            duration: Duration of failed process in seconds
            error_details: Error details
            log_file: Path to log file (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"CheckjeBon Import Failed - Exit Code {exit_code}"
        
        # Create text body
        text_body = f"""
CheckjeBon Import Failure Report
===============================

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Exit Code: {exit_code}
Duration: {duration} seconds
Host: {os.uname().nodename}

Error Details:
{error_details}

Log File: {log_file or 'N/A'}

Please investigate and resolve the issue.

This is an automated message from the CheckjeBon import system.
"""
        
        # Create HTML body
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8d7da; padding: 15px; border-radius: 5px; }}
        .content {{ margin: 20px 0; }}
        .error-box {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #dc3545; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 CheckjeBon Import Failed</h2>
        <p><strong>Exit Code:</strong> {exit_code}</p>
    </div>
    
    <div class="content">
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Duration:</strong> {duration} seconds</p>
        <p><strong>Host:</strong> {os.uname().nodename}</p>
        
        <div class="error-box">
            <h3>Error Details:</h3>
            <pre>{error_details}</pre>
        </div>
        
        <p><strong>Log File:</strong> {log_file or 'N/A'}</p>
    </div>
    
    <div class="footer">
        <p>This is an automated message from the CheckjeBon import system.</p>
        <p>Please investigate and resolve the issue.</p>
    </div>
</body>
</html>
"""
        
        # Attach log file if available
        attachments = []
        if log_file and os.path.exists(log_file):
            attachments.append(log_file)
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=text_body,
            html_body=html_body,
            attachments=attachments
        )
    
    def send_success_notification(self, 
                                  to_emails: List[str],
                                  duration: int,
                                  statistics: dict) -> bool:
        """
        Send success notification email
        
        Args:
            to_emails: List of recipient email addresses
            duration: Duration of successful process in seconds
            statistics: Import statistics dictionary
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "CheckjeBon Import Completed Successfully"
        
        # Format statistics
        stats_text = "\n".join([f"  {key}: {value}" for key, value in statistics.items()])
        
        # Create text body
        text_body = f"""
CheckjeBon Import Success Report
===============================

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration} seconds
Host: {os.uname().nodename}

Import Statistics:
{stats_text}

The import completed successfully!

This is an automated message from the CheckjeBon import system.
"""
        
        # Create HTML body
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #d4edda; padding: 15px; border-radius: 5px; }}
        .content {{ margin: 20px 0; }}
        .stats-box {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>✅ CheckjeBon Import Successful</h2>
        <p><strong>Duration:</strong> {duration} seconds</p>
    </div>
    
    <div class="content">
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Host:</strong> {os.uname().nodename}</p>
        
        <div class="stats-box">
            <h3>Import Statistics:</h3>
            <ul>
                {"".join([f"<li><strong>{key}:</strong> {value}</li>" for key, value in statistics.items()])}
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p>This is an automated message from the CheckjeBon import system.</p>
        <p>The import completed successfully!</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=text_body,
            html_body=html_body
        )
    
    def test_email_config(self, to_email: str) -> bool:
        """
        Test email configuration by sending a test email
        
        Args:
            to_email: Email address to send test email to
            
        Returns:
            bool: True if test email sent successfully, False otherwise
        """
        subject = "CheckjeBon Email Test"
        body = f"""
This is a test email from the CheckjeBon import system.

Configuration Test Results:
- SMTP Host: {self.smtp_host}
- SMTP Port: {self.smtp_port}
- From Email: {self.from_email}
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, the configuration is working correctly!
"""
        
        return self.send_email(
            to_emails=[to_email],
            subject=subject,
            body=body
        )

def main():
    """Command line interface for email notifications"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CheckjeBon Email Notifications')
    parser.add_argument('action', choices=['test', 'failure', 'success'],
                        help='Action to perform')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--exit-code', type=int, help='Exit code for failure notification')
    parser.add_argument('--duration', type=int, help='Duration in seconds')
    parser.add_argument('--error-details', help='Error details for failure notification')
    parser.add_argument('--log-file', help='Log file path')
    parser.add_argument('--stats', help='Statistics JSON for success notification')
    
    args = parser.parse_args()
    
    # Initialize notifier
    notifier = EmailNotifier()
    
    if not notifier.enabled:
        print("Email notifications are disabled")
        sys.exit(0)
    
    try:
        if args.action == 'test':
            success = notifier.test_email_config(args.to)
            
        elif args.action == 'failure':
            success = notifier.send_failure_notification(
                to_emails=[args.to],
                exit_code=args.exit_code or 1,
                duration=args.duration or 0,
                error_details=args.error_details or "No error details provided",
                log_file=args.log_file
            )
            
        elif args.action == 'success':
            stats = {}
            if args.stats:
                stats = json.loads(args.stats)
            
            success = notifier.send_success_notification(
                to_emails=[args.to],
                duration=args.duration or 0,
                statistics=stats
            )
        
        if success:
            print("Email sent successfully!")
            sys.exit(0)
        else:
            print("Failed to send email")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()