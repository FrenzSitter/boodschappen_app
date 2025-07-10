#!/usr/bin/env python3
"""
Comprehensive Environment Setup Verification Script
==================================================

Validates the complete environment setup for the supermarket data import system.
Checks environment variables, dependencies, database setup, external services,
file system permissions, performance, and security.

Usage:
    python3 verify_environment.py [OPTIONS]
    
Features:
    - Environment variables validation
    - Dependencies and connectivity checks
    - Database setup verification
    - External services validation
    - File system permissions
    - Performance benchmarks
    - Security validation
    - Detailed error reporting with solutions
"""

import os
import sys
import json
import time
import argparse
import logging
import asyncio
import aiohttp
import requests
import subprocess
import tempfile
import socket
import ssl
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import secrets
import platform

# Third-party imports with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    SUPABASE_ERROR = str(e)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


class CheckStatus(Enum):
    """Status of verification checks"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️  WARN"
    INFO = "ℹ️  INFO"
    SKIP = "⏭️  SKIP"


@dataclass
class CheckResult:
    """Result of a verification check"""
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = None
    solution: str = ""
    benchmark: Optional[float] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class EnvironmentVerifier:
    """Main environment verification system"""
    
    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.results: List[CheckResult] = []
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger("env_verifier")
        
        # System information
        self.system_info = self.collect_system_info()
        
        # Configuration
        self.config = self.load_configuration()
        
        self.logger.info("Environment verifier initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Suppress noisy third-party loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
    
    def collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').free,
            'timestamp': datetime.now().isoformat()
        }
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment and files"""
        config = {
            # Environment variables
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'supabase_test_url': os.getenv('SUPABASE_TEST_URL'),
            'supabase_test_key': os.getenv('SUPABASE_TEST_KEY'),
            'checkjebon_url': os.getenv('CHECKJEBON_URL', 'https://api.checkjebon.nl'),
            'checkjebon_api_key': os.getenv('CHECKJEBON_API_KEY'),
            'redis_url': os.getenv('REDIS_URL'),
            
            # AWS Configuration
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'aws_region': os.getenv('AWS_REGION'),
            'aws_s3_bucket': os.getenv('S3_BUCKET'),
            
            # GitHub Configuration
            'github_token': os.getenv('GITHUB_TOKEN'),
            'github_repo': os.getenv('GITHUB_REPOSITORY'),
            
            # Email Configuration
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': os.getenv('SMTP_PORT'),
            'email_from': os.getenv('EMAIL_FROM'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            
            # Application Configuration
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            
            # Performance Configuration
            'batch_size': int(os.getenv('IMPORT_BATCH_SIZE', '1000')),
            'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
            'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', '3')),
        }
        
        # Load from .env file if exists
        env_file = Path('.env')
        if env_file.exists():
            config['env_file_exists'] = True
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                config['env_file_size'] = len(env_content)
                config['env_file_lines'] = len(env_content.splitlines())
            except Exception as e:
                config['env_file_error'] = str(e)
        else:
            config['env_file_exists'] = False
        
        return config
    
    def add_result(self, result: CheckResult):
        """Add check result"""
        self.results.append(result)
        
        # Log result
        status_symbol = result.status.value.split()[0]
        log_message = f"{status_symbol} {result.name}: {result.message}"
        
        if result.status == CheckStatus.PASS:
            self.logger.info(log_message)
        elif result.status == CheckStatus.WARN:
            self.logger.warning(log_message)
        elif result.status == CheckStatus.FAIL:
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)
    
    # Environment Variables Checks
    def check_environment_variables(self) -> List[CheckResult]:
        """Check all required environment variables"""
        results = []
        
        # Required variables for production
        required_vars = {
            'SUPABASE_URL': {
                'value': self.config['supabase_url'],
                'description': 'Supabase project URL',
                'example': 'https://your-project.supabase.co',
                'critical': True
            },
            'SUPABASE_KEY': {
                'value': self.config['supabase_key'],
                'description': 'Supabase service role key',
                'example': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'critical': True,
                'sensitive': True
            }
        }
        
        # Optional but recommended variables
        optional_vars = {
            'SUPABASE_TEST_URL': {
                'value': self.config['supabase_test_url'],
                'description': 'Supabase test environment URL'
            },
            'SUPABASE_TEST_KEY': {
                'value': self.config['supabase_test_key'],
                'description': 'Supabase test environment key',
                'sensitive': True
            },
            'CHECKJEBON_API_KEY': {
                'value': self.config['checkjebon_api_key'],
                'description': 'CheckjeBon API key for data access',
                'sensitive': True
            },
            'REDIS_URL': {
                'value': self.config['redis_url'],
                'description': 'Redis connection URL for caching'
            },
            'AWS_ACCESS_KEY_ID': {
                'value': self.config['aws_access_key_id'],
                'description': 'AWS access key for S3 backups'
            },
            'AWS_SECRET_ACCESS_KEY': {
                'value': self.config['aws_secret_access_key'],
                'description': 'AWS secret key for S3 backups',
                'sensitive': True
            },
            'GITHUB_TOKEN': {
                'value': self.config['github_token'],
                'description': 'GitHub token for CI/CD operations',
                'sensitive': True
            }
        }
        
        # Check required variables
        all_required_present = True
        for var_name, var_info in required_vars.items():
            if not var_info['value']:
                all_required_present = False
                solution = f"Set {var_name} environment variable:\n"
                solution += f"export {var_name}=\"{var_info.get('example', 'your_value_here')}\""
                
                results.append(CheckResult(
                    name=f"Environment Variable: {var_name}",
                    status=CheckStatus.FAIL,
                    message=f"Required variable {var_name} is not set",
                    details={'description': var_info['description']},
                    solution=solution
                ))
            else:
                # Validate format for specific variables
                if var_name == 'SUPABASE_URL':
                    if not var_info['value'].startswith('https://') or not '.supabase.co' in var_info['value']:
                        results.append(CheckResult(
                            name=f"Environment Variable: {var_name}",
                            status=CheckStatus.WARN,
                            message="SUPABASE_URL format may be incorrect",
                            details={'value': var_info['value'][:50] + '...' if len(var_info['value']) > 50 else var_info['value']},
                            solution="Ensure SUPABASE_URL follows format: https://your-project.supabase.co"
                        ))
                    else:
                        results.append(CheckResult(
                            name=f"Environment Variable: {var_name}",
                            status=CheckStatus.PASS,
                            message=f"{var_name} is properly configured",
                            details={'format_valid': True}
                        ))
                elif var_name == 'SUPABASE_KEY':
                    if len(var_info['value']) < 100:  # JWT tokens are typically longer
                        results.append(CheckResult(
                            name=f"Environment Variable: {var_name}",
                            status=CheckStatus.WARN,
                            message="SUPABASE_KEY appears to be too short for a service role key",
                            solution="Ensure you're using the service_role key, not the anon key"
                        ))
                    else:
                        results.append(CheckResult(
                            name=f"Environment Variable: {var_name}",
                            status=CheckStatus.PASS,
                            message=f"{var_name} is properly configured",
                            details={'length_valid': True}
                        ))
                else:
                    results.append(CheckResult(
                        name=f"Environment Variable: {var_name}",
                        status=CheckStatus.PASS,
                        message=f"{var_name} is set",
                        details={'configured': True}
                    ))
        
        # Check optional variables
        optional_count = 0
        for var_name, var_info in optional_vars.items():
            if var_info['value']:
                optional_count += 1
                results.append(CheckResult(
                    name=f"Optional Variable: {var_name}",
                    status=CheckStatus.PASS,
                    message=f"{var_name} is configured",
                    details={'optional': True}
                ))
            else:
                results.append(CheckResult(
                    name=f"Optional Variable: {var_name}",
                    status=CheckStatus.INFO,
                    message=f"{var_name} is not set (optional)",
                    details={'description': var_info['description'], 'optional': True}
                ))
        
        # Summary result
        if all_required_present:
            results.append(CheckResult(
                name="Environment Variables Summary",
                status=CheckStatus.PASS,
                message=f"All required variables set, {optional_count}/{len(optional_vars)} optional variables configured",
                details={
                    'required_variables': len(required_vars),
                    'optional_variables': optional_count,
                    'total_configured': len(required_vars) + optional_count
                }
            ))
        else:
            results.append(CheckResult(
                name="Environment Variables Summary",
                status=CheckStatus.FAIL,
                message="Some required environment variables are missing",
                solution="Configure all required environment variables before proceeding"
            ))
        
        return results
    
    def check_env_file(self) -> CheckResult:
        """Check .env file configuration"""
        if not self.config['env_file_exists']:
            return CheckResult(
                name=".env File",
                status=CheckStatus.WARN,
                message=".env file not found",
                solution="Create .env file from .env.example:\ncp .env.example .env\n# Then edit .env with your values"
            )
        
        if 'env_file_error' in self.config:
            return CheckResult(
                name=".env File",
                status=CheckStatus.FAIL,
                message=f"Error reading .env file: {self.config['env_file_error']}",
                solution="Check .env file permissions and syntax"
            )
        
        return CheckResult(
            name=".env File",
            status=CheckStatus.PASS,
            message=f".env file found ({self.config['env_file_lines']} lines, {self.config['env_file_size']} bytes)",
            details={
                'lines': self.config['env_file_lines'],
                'size_bytes': self.config['env_file_size']
            }
        )


    # Dependencies and Connectivity Checks
    def check_python_dependencies(self) -> List[CheckResult]:
        """Check Python package dependencies"""
        results = []
        
        # Core dependencies
        core_deps = {
            'supabase': {'available': SUPABASE_AVAILABLE, 'critical': True, 'version_cmd': None},
            'requests': {'available': True, 'critical': True, 'version_cmd': None},
            'pandas': {'available': PANDAS_AVAILABLE, 'critical': False, 'version_cmd': None},
            'psycopg2': {'available': PSYCOPG2_AVAILABLE, 'critical': False, 'version_cmd': None},
            'boto3': {'available': BOTO3_AVAILABLE, 'critical': False, 'version_cmd': None},
            'aiohttp': {'available': True, 'critical': True, 'version_cmd': None},
        }
        
        # Check each dependency
        missing_critical = []
        missing_optional = []
        
        for dep_name, dep_info in core_deps.items():
            try:
                if dep_info['available']:
                    # Try to get version
                    try:
                        if dep_name == 'supabase':
                            import supabase
                            version = getattr(supabase, '__version__', 'unknown')
                        elif dep_name == 'requests':
                            import requests
                            version = requests.__version__
                        elif dep_name == 'pandas':
                            version = pd.__version__
                        elif dep_name == 'boto3':
                            import boto3
                            version = boto3.__version__
                        elif dep_name == 'aiohttp':
                            import aiohttp
                            version = aiohttp.__version__
                        elif dep_name == 'psycopg2':
                            import psycopg2
                            version = psycopg2.__version__
                        else:
                            version = 'unknown'
                    except:
                        version = 'unknown'
                    
                    results.append(CheckResult(
                        name=f"Python Package: {dep_name}",
                        status=CheckStatus.PASS,
                        message=f"{dep_name} is installed (version: {version})",
                        details={'version': version, 'critical': dep_info['critical']}
                    ))
                else:
                    if dep_info['critical']:
                        missing_critical.append(dep_name)
                        results.append(CheckResult(
                            name=f"Python Package: {dep_name}",
                            status=CheckStatus.FAIL,
                            message=f"Critical package {dep_name} is not installed",
                            solution=f"Install {dep_name}: pip install {dep_name}"
                        ))
                    else:
                        missing_optional.append(dep_name)
                        results.append(CheckResult(
                            name=f"Python Package: {dep_name}",
                            status=CheckStatus.WARN,
                            message=f"Optional package {dep_name} is not installed",
                            solution=f"Install {dep_name}: pip install {dep_name}"
                        ))
            except Exception as e:
                results.append(CheckResult(
                    name=f"Python Package: {dep_name}",
                    status=CheckStatus.FAIL,
                    message=f"Error checking {dep_name}: {e}",
                    solution=f"Install {dep_name}: pip install {dep_name}"
                ))
        
        # Requirements.txt check
        requirements_file = Path('requirements.txt')
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    req_content = f.read()
                req_lines = [line.strip() for line in req_content.splitlines() if line.strip() and not line.startswith('#')]
                
                results.append(CheckResult(
                    name="Requirements File",
                    status=CheckStatus.PASS,
                    message=f"requirements.txt found with {len(req_lines)} packages",
                    details={'package_count': len(req_lines)}
                ))
            except Exception as e:
                results.append(CheckResult(
                    name="Requirements File",
                    status=CheckStatus.WARN,
                    message=f"Error reading requirements.txt: {e}"
                ))
        else:
            results.append(CheckResult(
                name="Requirements File",
                status=CheckStatus.WARN,
                message="requirements.txt not found",
                solution="Create requirements.txt to document dependencies"
            ))
        
        return results
    
    def check_network_connectivity(self) -> List[CheckResult]:
        """Check network connectivity to external services"""
        results = []
        
        # Test endpoints
        endpoints = [
            {
                'name': 'Google DNS',
                'url': 'https://8.8.8.8',
                'port': 53,
                'protocol': 'tcp',
                'critical': True,
                'description': 'Basic internet connectivity'
            },
            {
                'name': 'Supabase API',
                'url': self.config['supabase_url'],
                'critical': True,
                'description': 'Database connectivity'
            },
            {
                'name': 'CheckjeBon API',
                'url': self.config['checkjebon_url'],
                'critical': False,
                'description': 'Data source API'
            },
            {
                'name': 'GitHub API',
                'url': 'https://api.github.com',
                'critical': False,
                'description': 'CI/CD connectivity'
            }
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            
            try:
                if endpoint['url']:
                    if endpoint['name'] == 'Google DNS':
                        # Test DNS resolution
                        socket.gethostbyname('google.com')
                        response_time = time.time() - start_time
                        
                        results.append(CheckResult(
                            name=f"Network: {endpoint['name']}",
                            status=CheckStatus.PASS,
                            message=f"DNS resolution working",
                            benchmark=response_time,
                            details={'response_time_ms': round(response_time * 1000, 2)}
                        ))
                    else:
                        # HTTP/HTTPS test
                        response = requests.get(
                            endpoint['url'],
                            timeout=self.config['request_timeout'],
                            headers={'User-Agent': 'Environment-Verifier/1.0'}
                        )
                        response_time = time.time() - start_time
                        
                        if response.status_code < 400:
                            results.append(CheckResult(
                                name=f"Network: {endpoint['name']}",
                                status=CheckStatus.PASS,
                                message=f"HTTP {response.status_code} - Connectivity OK",
                                benchmark=response_time,
                                details={
                                    'status_code': response.status_code,
                                    'response_time_ms': round(response_time * 1000, 2),
                                    'url': endpoint['url']
                                }
                            ))
                        else:
                            status = CheckStatus.FAIL if endpoint['critical'] else CheckStatus.WARN
                            results.append(CheckResult(
                                name=f"Network: {endpoint['name']}",
                                status=status,
                                message=f"HTTP {response.status_code} - {endpoint['description']} may not be accessible",
                                details={'status_code': response.status_code, 'url': endpoint['url']}
                            ))
                else:
                    results.append(CheckResult(
                        name=f"Network: {endpoint['name']}",
                        status=CheckStatus.SKIP,
                        message=f"URL not configured for {endpoint['name']}",
                        details={'description': endpoint['description']}
                    ))
                    
            except requests.exceptions.Timeout:
                status = CheckStatus.FAIL if endpoint['critical'] else CheckStatus.WARN
                results.append(CheckResult(
                    name=f"Network: {endpoint['name']}",
                    status=status,
                    message=f"Connection timeout to {endpoint['name']}",
                    solution="Check network connectivity and firewall settings"
                ))
            except requests.exceptions.ConnectionError:
                status = CheckStatus.FAIL if endpoint['critical'] else CheckStatus.WARN
                results.append(CheckResult(
                    name=f"Network: {endpoint['name']}",
                    status=status,
                    message=f"Cannot connect to {endpoint['name']}",
                    solution="Check URL configuration and network connectivity"
                ))
            except Exception as e:
                status = CheckStatus.FAIL if endpoint['critical'] else CheckStatus.WARN
                results.append(CheckResult(
                    name=f"Network: {endpoint['name']}",
                    status=status,
                    message=f"Network error: {str(e)[:100]}",
                    solution="Check network configuration and credentials"
                ))
        
        return results
    
    # Database Setup Validation
    def check_supabase_connection(self) -> List[CheckResult]:
        """Check Supabase database connection and setup"""
        results = []
        
        if not SUPABASE_AVAILABLE:
            return [CheckResult(
                name="Supabase Connection",
                status=CheckStatus.FAIL,
                message=f"Supabase library not available: {SUPABASE_ERROR}",
                solution="Install supabase: pip install supabase"
            )]
        
        if not self.config['supabase_url'] or not self.config['supabase_key']:
            return [CheckResult(
                name="Supabase Connection",
                status=CheckStatus.FAIL,
                message="Supabase credentials not configured",
                solution="Set SUPABASE_URL and SUPABASE_KEY environment variables"
            )]
        
        try:
            # Test connection
            start_time = time.time()
            client = create_client(self.config['supabase_url'], self.config['supabase_key'])
            
            # Basic connectivity test
            response = client.table('supermarkets').select('id').limit(1).execute()
            connection_time = time.time() - start_time
            
            results.append(CheckResult(
                name="Supabase Connection",
                status=CheckStatus.PASS,
                message="Successfully connected to Supabase",
                benchmark=connection_time,
                details={
                    'connection_time_ms': round(connection_time * 1000, 2),
                    'url': self.config['supabase_url']
                }
            ))
            
            # Check table structure
            table_results = self.check_database_tables(client)
            results.extend(table_results)
            
            # Check permissions
            permission_results = self.check_database_permissions(client)
            results.extend(permission_results)
            
        except Exception as e:
            error_msg = str(e)
            solution = "Check Supabase credentials and network connectivity"
            
            if "Invalid API key" in error_msg:
                solution = "Verify SUPABASE_KEY is correct and has proper permissions"
            elif "not found" in error_msg.lower():
                solution = "Verify SUPABASE_URL is correct"
            elif "timeout" in error_msg.lower():
                solution = "Check network connectivity to Supabase"
            
            results.append(CheckResult(
                name="Supabase Connection",
                status=CheckStatus.FAIL,
                message=f"Failed to connect to Supabase: {error_msg[:200]}",
                solution=solution
            ))
        
        return results
    
    def check_database_tables(self, client: Client) -> List[CheckResult]:
        """Check database table existence and structure"""
        results = []
        
        expected_tables = {
            'supermarkets': {
                'required_columns': ['id', 'name', 'slug', 'is_active'],
                'optional_columns': ['logo_url', 'color_primary', 'website_url', 'api_endpoint']
            },
            'categories': {
                'required_columns': ['id', 'name', 'slug', 'is_active'],
                'optional_columns': ['parent_id', 'description']
            },
            'products': {
                'required_columns': ['id', 'name', 'normalized_name', 'is_active'],
                'optional_columns': ['brand', 'size_text', 'ean', 'category_id', 'image_url', 'description', 'unit_size', 'supermarket_id']
            },
            'prices': {
                'required_columns': ['id', 'product_id', 'supermarket_id', 'price', 'price_date'],
                'optional_columns': ['price_per_unit', 'original_price', 'is_on_sale', 'discount_percentage', 'import_batch_id', 'is_available']
            },
            'shopping_lists': {
                'required_columns': ['id', 'name', 'is_active'],
                'optional_columns': ['description', 'user_id']
            },
            'shopping_list_items': {
                'required_columns': ['id', 'shopping_list_id', 'product_id', 'quantity'],
                'optional_columns': ['is_completed', 'notes', 'supermarket_id']
            }
        }
        
        for table_name, table_info in expected_tables.items():
            try:
                # Test table access and get sample data
                start_time = time.time()
                response = client.table(table_name).select('*').limit(5).execute()
                query_time = time.time() - start_time
                
                record_count = len(response.data)
                
                # Check if we can get the schema by examining the first record
                columns_found = []
                if response.data:
                    columns_found = list(response.data[0].keys())
                
                # Verify required columns
                missing_required = []
                for col in table_info['required_columns']:
                    if col not in columns_found:
                        missing_required.append(col)
                
                if missing_required:
                    results.append(CheckResult(
                        name=f"Database Table: {table_name}",
                        status=CheckStatus.WARN,
                        message=f"Table exists but missing required columns: {missing_required}",
                        details={
                            'record_count': record_count,
                            'columns_found': columns_found,
                            'missing_required': missing_required
                        },
                        solution=f"Run database migrations to add missing columns to {table_name}"
                    ))
                else:
                    results.append(CheckResult(
                        name=f"Database Table: {table_name}",
                        status=CheckStatus.PASS,
                        message=f"Table structure valid ({record_count} records)",
                        benchmark=query_time,
                        details={
                            'record_count': record_count,
                            'query_time_ms': round(query_time * 1000, 2),
                            'columns_found': len(columns_found),
                            'has_data': record_count > 0
                        }
                    ))
                
            except Exception as e:
                error_msg = str(e)
                if "relation does not exist" in error_msg or "table" in error_msg.lower():
                    results.append(CheckResult(
                        name=f"Database Table: {table_name}",
                        status=CheckStatus.FAIL,
                        message=f"Table {table_name} does not exist",
                        solution=f"Create table {table_name} by running database migrations:\n./scripts/run-migrations.sh"
                    ))
                else:
                    results.append(CheckResult(
                        name=f"Database Table: {table_name}",
                        status=CheckStatus.FAIL,
                        message=f"Error accessing table {table_name}: {error_msg[:150]}",
                        solution="Check database permissions and table structure"
                    ))
        
        return results
    
    def check_database_permissions(self, client: Client) -> List[CheckResult]:
        """Check database permissions"""
        results = []
        
        # Test basic CRUD operations on a test table
        test_operations = [
            {
                'name': 'SELECT',
                'test': lambda: client.table('supermarkets').select('id').limit(1).execute(),
                'critical': True
            },
            {
                'name': 'COUNT',
                'test': lambda: client.table('supermarkets').select('id', count='exact').execute(),
                'critical': True
            }
        ]
        
        # We won't test INSERT/UPDATE/DELETE in verification to avoid data modification
        
        permissions_passed = 0
        for operation in test_operations:
            try:
                start_time = time.time()
                result = operation['test']()
                exec_time = time.time() - start_time
                
                results.append(CheckResult(
                    name=f"Database Permission: {operation['name']}",
                    status=CheckStatus.PASS,
                    message=f"{operation['name']} operation successful",
                    benchmark=exec_time,
                    details={'execution_time_ms': round(exec_time * 1000, 2)}
                ))
                permissions_passed += 1
                
            except Exception as e:
                status = CheckStatus.FAIL if operation['critical'] else CheckStatus.WARN
                results.append(CheckResult(
                    name=f"Database Permission: {operation['name']}",
                    status=status,
                    message=f"{operation['name']} operation failed: {str(e)[:150]}",
                    solution="Check database user permissions and RLS policies"
                ))
        
        # Summary
        if permissions_passed == len(test_operations):
            results.append(CheckResult(
                name="Database Permissions Summary",
                status=CheckStatus.PASS,
                message=f"All {permissions_passed} permission tests passed",
                details={'operations_tested': len(test_operations), 'operations_passed': permissions_passed}
            ))
        else:
            results.append(CheckResult(
                name="Database Permissions Summary",
                status=CheckStatus.WARN,
                message=f"Only {permissions_passed}/{len(test_operations)} permission tests passed",
                solution="Review database user permissions and policies"
            ))
        
        return results


    # External Services Verification
    def check_external_services(self) -> List[CheckResult]:
        """Check external services availability and configuration"""
        results = []
        
        # GitHub API check
        if self.config['github_token']:
            try:
                headers = {'Authorization': f"token {self.config['github_token']}"}
                response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    user_data = response.json()
                    results.append(CheckResult(
                        name="External Service: GitHub API",
                        status=CheckStatus.PASS,
                        message=f"GitHub API accessible (user: {user_data.get('login', 'unknown')})",
                        details={'rate_limit_remaining': response.headers.get('X-RateLimit-Remaining')}
                    ))
                else:
                    results.append(CheckResult(
                        name="External Service: GitHub API",
                        status=CheckStatus.WARN,
                        message=f"GitHub API returned {response.status_code}",
                        solution="Check GITHUB_TOKEN validity"
                    ))
            except Exception as e:
                results.append(CheckResult(
                    name="External Service: GitHub API",
                    status=CheckStatus.WARN,
                    message=f"GitHub API check failed: {str(e)[:100]}",
                    solution="Check GITHUB_TOKEN and network connectivity"
                ))
        else:
            results.append(CheckResult(
                name="External Service: GitHub API",
                status=CheckStatus.INFO,
                message="GitHub token not configured (optional for CI/CD)"
            ))
        
        # AWS S3 check
        if self.config['aws_access_key_id'] and self.config['aws_secret_access_key']:
            try:
                import boto3
                from botocore.exceptions import ClientError, NoCredentialsError
                
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.config['aws_access_key_id'],
                    aws_secret_access_key=self.config['aws_secret_access_key'],
                    region_name=self.config['aws_region'] or 'us-east-1'
                )
                
                # Test S3 access
                response = s3_client.list_buckets()
                bucket_count = len(response['Buckets'])
                
                results.append(CheckResult(
                    name="External Service: AWS S3",
                    status=CheckStatus.PASS,
                    message=f"S3 access successful ({bucket_count} buckets accessible)",
                    details={'bucket_count': bucket_count}
                ))
                
                # Check specific bucket if configured
                if self.config['aws_s3_bucket']:
                    try:
                        s3_client.head_bucket(Bucket=self.config['aws_s3_bucket'])
                        results.append(CheckResult(
                            name="External Service: S3 Bucket",
                            status=CheckStatus.PASS,
                            message=f"Configured bucket '{self.config['aws_s3_bucket']}' is accessible",
                            details={'bucket_name': self.config['aws_s3_bucket']}
                        ))
                    except ClientError as e:
                        error_code = e.response['Error']['Code']
                        if error_code == '404':
                            solution = f"Create bucket '{self.config['aws_s3_bucket']}' or update S3_BUCKET config"
                        else:
                            solution = "Check bucket permissions and AWS credentials"
                        
                        results.append(CheckResult(
                            name="External Service: S3 Bucket",
                            status=CheckStatus.WARN,
                            message=f"Configured bucket not accessible: {error_code}",
                            solution=solution
                        ))
                
            except ImportError:
                results.append(CheckResult(
                    name="External Service: AWS S3",
                    status=CheckStatus.WARN,
                    message="boto3 not installed - S3 backups unavailable",
                    solution="Install boto3: pip install boto3"
                ))
            except NoCredentialsError:
                results.append(CheckResult(
                    name="External Service: AWS S3",
                    status=CheckStatus.WARN,
                    message="AWS credentials invalid",
                    solution="Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
                ))
            except Exception as e:
                results.append(CheckResult(
                    name="External Service: AWS S3",
                    status=CheckStatus.WARN,
                    message=f"S3 check failed: {str(e)[:100]}",
                    solution="Check AWS credentials and region configuration"
                ))
        else:
            results.append(CheckResult(
                name="External Service: AWS S3",
                status=CheckStatus.INFO,
                message="AWS credentials not configured (optional for backups)"
            ))
        
        return results
    
    # File System Checks
    def check_file_system(self) -> List[CheckResult]:
        """Check file system permissions and setup"""
        results = []
        
        # Check required directories
        required_dirs = [
            {'path': 'logs', 'purpose': 'Application logging'},
            {'path': 'manual_import_data', 'purpose': 'Import data storage'},
            {'path': 'manual_import_backups', 'purpose': 'Database backups'},
            {'path': 'manual_import_reports', 'purpose': 'Import reports'},
            {'path': 'debug_output', 'purpose': 'Debug information'}
        ]
        
        for dir_info in required_dirs:
            dir_path = Path(dir_info['path'])
            
            try:
                if dir_path.exists():
                    if dir_path.is_dir():
                        # Check write permissions
                        test_file = dir_path / f".write_test_{int(time.time())}"
                        try:
                            test_file.write_text("test")
                            test_file.unlink()
                            
                            # Get directory size
                            total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                            file_count = len(list(dir_path.rglob('*')))
                            
                            results.append(CheckResult(
                                name=f"Directory: {dir_info['path']}",
                                status=CheckStatus.PASS,
                                message=f"Directory exists with write permissions ({file_count} files, {total_size} bytes)",
                                details={
                                    'path': str(dir_path.absolute()),
                                    'file_count': file_count,
                                    'size_bytes': total_size,
                                    'purpose': dir_info['purpose']
                                }
                            ))
                        except PermissionError:
                            results.append(CheckResult(
                                name=f"Directory: {dir_info['path']}",
                                status=CheckStatus.FAIL,
                                message=f"Directory exists but no write permission",
                                solution=f"Fix permissions: chmod 755 {dir_path}"
                            ))
                    else:
                        results.append(CheckResult(
                            name=f"Directory: {dir_info['path']}",
                            status=CheckStatus.FAIL,
                            message=f"Path exists but is not a directory",
                            solution=f"Remove file and create directory: rm {dir_path} && mkdir {dir_path}"
                        ))
                else:
                    # Try to create directory
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        results.append(CheckResult(
                            name=f"Directory: {dir_info['path']}",
                            status=CheckStatus.PASS,
                            message=f"Directory created successfully",
                            details={'path': str(dir_path.absolute()), 'purpose': dir_info['purpose']}
                        ))
                    except PermissionError:
                        results.append(CheckResult(
                            name=f"Directory: {dir_info['path']}",
                            status=CheckStatus.FAIL,
                            message=f"Cannot create directory - permission denied",
                            solution=f"Create directory with proper permissions: mkdir -p {dir_path}"
                        ))
            except Exception as e:
                results.append(CheckResult(
                    name=f"Directory: {dir_info['path']}",
                    status=CheckStatus.FAIL,
                    message=f"Error checking directory: {str(e)[:100]}",
                    solution=f"Manually create directory: mkdir -p {dir_path}"
                ))
        
        # Check disk space
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            if free_gb < 1:
                status = CheckStatus.FAIL
                message = f"Critical: Only {free_gb:.1f} GB free space remaining"
                solution = "Free up disk space before proceeding"
            elif free_gb < 5:
                status = CheckStatus.WARN
                message = f"Low disk space: {free_gb:.1f} GB free ({used_percent:.1f}% used)"
                solution = "Consider freeing up disk space"
            else:
                status = CheckStatus.PASS
                message = f"Sufficient disk space: {free_gb:.1f} GB free ({used_percent:.1f}% used)"
                solution = ""
            
            results.append(CheckResult(
                name="Disk Space",
                status=status,
                message=message,
                solution=solution,
                details={
                    'free_gb': round(free_gb, 2),
                    'total_gb': round(total_gb, 2),
                    'used_percent': round(used_percent, 2)
                }
            ))
            
        except Exception as e:
            results.append(CheckResult(
                name="Disk Space",
                status=CheckStatus.WARN,
                message=f"Could not check disk space: {str(e)[:100]}"
            ))
        
        return results
    
    # Performance Benchmarks
    def run_performance_benchmarks(self) -> List[CheckResult]:
        """Run performance benchmarks"""
        results = []
        
        if self.quick:
            results.append(CheckResult(
                name="Performance Benchmarks",
                status=CheckStatus.SKIP,
                message="Skipped in quick mode"
            ))
            return results
        
        # CPU benchmark
        try:
            start_time = time.time()
            # Simple CPU intensive task
            for _ in range(100000):
                hash('benchmark_test')
            cpu_time = time.time() - start_time
            
            if cpu_time > 1.0:
                status = CheckStatus.WARN
                message = f"CPU performance may be slow ({cpu_time:.3f}s for benchmark)"
            else:
                status = CheckStatus.PASS
                message = f"CPU performance acceptable ({cpu_time:.3f}s for benchmark)"
            
            results.append(CheckResult(
                name="Performance: CPU",
                status=status,
                message=message,
                benchmark=cpu_time,
                details={'benchmark_time_ms': round(cpu_time * 1000, 2)}
            ))
        except Exception as e:
            results.append(CheckResult(
                name="Performance: CPU",
                status=CheckStatus.WARN,
                message=f"CPU benchmark failed: {str(e)[:100]}"
            ))
        
        # Memory check
        try:
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_percent = memory.percent
            
            if memory_gb < 2:
                status = CheckStatus.WARN
                message = f"Low memory: {memory_gb:.1f} GB total"
                solution = "Consider upgrading system memory"
            elif memory_percent > 90:
                status = CheckStatus.WARN
                message = f"High memory usage: {memory_percent:.1f}% used"
                solution = "Close unnecessary applications"
            else:
                status = CheckStatus.PASS
                message = f"Memory OK: {memory_gb:.1f} GB total, {memory_percent:.1f}% used"
                solution = ""
            
            results.append(CheckResult(
                name="Performance: Memory",
                status=status,
                message=message,
                solution=solution,
                details={
                    'total_gb': round(memory_gb, 2),
                    'used_percent': round(memory_percent, 2),
                    'available_gb': round(memory.available / (1024**3), 2)
                }
            ))
        except Exception as e:
            results.append(CheckResult(
                name="Performance: Memory",
                status=CheckStatus.WARN,
                message=f"Memory check failed: {str(e)[:100]}"
            ))
        
        # Database performance (if available)
        if SUPABASE_AVAILABLE and self.config['supabase_url'] and self.config['supabase_key']:
            try:
                client = create_client(self.config['supabase_url'], self.config['supabase_key'])
                
                # Simple query benchmark
                start_time = time.time()
                response = client.table('supermarkets').select('id').limit(10).execute()
                query_time = time.time() - start_time
                
                if query_time > 2.0:
                    status = CheckStatus.WARN
                    message = f"Database queries may be slow ({query_time:.3f}s)"
                    solution = "Check database performance and network latency"
                else:
                    status = CheckStatus.PASS
                    message = f"Database performance acceptable ({query_time:.3f}s)"
                    solution = ""
                
                results.append(CheckResult(
                    name="Performance: Database Query",
                    status=status,
                    message=message,
                    solution=solution,
                    benchmark=query_time,
                    details={'query_time_ms': round(query_time * 1000, 2)}
                ))
            except Exception as e:
                results.append(CheckResult(
                    name="Performance: Database Query",
                    status=CheckStatus.INFO,
                    message=f"Database benchmark skipped: {str(e)[:100]}"
                ))
        
        return results
    
    # Security Validation
    def check_security(self) -> List[CheckResult]:
        """Check security configuration"""
        results = []
        
        # Check for sensitive data in environment
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential'
        ]
        
        # Check if .env file contains sensitive data
        env_file = Path('.env')
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                # Check file permissions
                file_stat = env_file.stat()
                file_mode = oct(file_stat.st_mode)[-3:]
                
                if file_mode != '600':
                    results.append(CheckResult(
                        name="Security: .env File Permissions",
                        status=CheckStatus.WARN,
                        message=f".env file permissions are {file_mode} (should be 600)",
                        solution="Fix permissions: chmod 600 .env"
                    ))
                else:
                    results.append(CheckResult(
                        name="Security: .env File Permissions",
                        status=CheckStatus.PASS,
                        message=".env file has secure permissions (600)"
                    ))
                
                # Check for example values
                example_patterns = ['your_', 'example_', 'changeme', 'replace_', 'todo']
                found_examples = []
                for pattern in example_patterns:
                    if pattern.lower() in env_content.lower():
                        found_examples.append(pattern)
                
                if found_examples:
                    results.append(CheckResult(
                        name="Security: .env Configuration",
                        status=CheckStatus.WARN,
                        message=f".env file may contain example values: {found_examples}",
                        solution="Replace example values with actual credentials"
                    ))
                else:
                    results.append(CheckResult(
                        name="Security: .env Configuration",
                        status=CheckStatus.PASS,
                        message=".env file appears to be properly configured"
                    ))
                    
            except Exception as e:
                results.append(CheckResult(
                    name="Security: .env File Check",
                    status=CheckStatus.WARN,
                    message=f"Could not check .env file: {str(e)[:100]}"
                ))
        
        # Check SSL/TLS for external connections
        external_urls = [
            self.config['supabase_url'],
            self.config['checkjebon_url']
        ]
        
        for url in external_urls:
            if url and url.startswith('https://'):
                try:
                    # Extract hostname
                    hostname = url.replace('https://', '').split('/')[0]
                    
                    # Check SSL certificate
                    context = ssl.create_default_context()
                    with socket.create_connection((hostname, 443), timeout=10) as sock:
                        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                            cert = ssock.getpeercert()
                            
                            # Check certificate expiry
                            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                            days_until_expiry = (not_after - datetime.now()).days
                            
                            if days_until_expiry < 30:
                                status = CheckStatus.WARN
                                message = f"SSL certificate for {hostname} expires in {days_until_expiry} days"
                                solution = "Monitor certificate renewal"
                            else:
                                status = CheckStatus.PASS
                                message = f"SSL certificate for {hostname} is valid ({days_until_expiry} days remaining)"
                                solution = ""
                            
                            results.append(CheckResult(
                                name=f"Security: SSL Certificate ({hostname})",
                                status=status,
                                message=message,
                                solution=solution,
                                details={'expires_in_days': days_until_expiry}
                            ))
                            
                except Exception as e:
                    results.append(CheckResult(
                        name=f"Security: SSL Certificate ({url})",
                        status=CheckStatus.WARN,
                        message=f"Could not verify SSL certificate: {str(e)[:100]}"
                    ))
        
        return results
    
    # Main execution methods
    def run_all_checks(self) -> Dict[str, List[CheckResult]]:
        """Run all verification checks"""
        all_results = {}
        
        self.logger.info("Starting comprehensive environment verification...")
        
        # Environment variables
        self.logger.info("Checking environment variables...")
        env_results = self.check_environment_variables()
        env_results.append(self.check_env_file())
        all_results['environment'] = env_results
        
        for result in env_results:
            self.add_result(result)
        
        # Dependencies
        self.logger.info("Checking dependencies...")
        dep_results = self.check_python_dependencies()
        all_results['dependencies'] = dep_results
        
        for result in dep_results:
            self.add_result(result)
        
        # Network connectivity
        self.logger.info("Checking network connectivity...")
        network_results = self.check_network_connectivity()
        all_results['network'] = network_results
        
        for result in network_results:
            self.add_result(result)
        
        # Database
        self.logger.info("Checking database setup...")
        db_results = self.check_supabase_connection()
        all_results['database'] = db_results
        
        for result in db_results:
            self.add_result(result)
        
        # External services
        self.logger.info("Checking external services...")
        ext_results = self.check_external_services()
        all_results['external_services'] = ext_results
        
        for result in ext_results:
            self.add_result(result)
        
        # File system
        self.logger.info("Checking file system...")
        fs_results = self.check_file_system()
        all_results['file_system'] = fs_results
        
        for result in fs_results:
            self.add_result(result)
        
        # Performance
        self.logger.info("Running performance benchmarks...")
        perf_results = self.run_performance_benchmarks()
        all_results['performance'] = perf_results
        
        for result in perf_results:
            self.add_result(result)
        
        # Security
        self.logger.info("Checking security configuration...")
        sec_results = self.check_security()
        all_results['security'] = sec_results
        
        for result in sec_results:
            self.add_result(result)
        
        return all_results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive report"""
        # Count results by status
        status_counts = {status: 0 for status in CheckStatus}
        for result in self.results:
            status_counts[result.status] += 1
        
        # Calculate overall score
        total_checks = len(self.results)
        passed_checks = status_counts[CheckStatus.PASS]
        failed_checks = status_counts[CheckStatus.FAIL]
        
        if total_checks > 0:
            success_rate = (passed_checks / total_checks) * 100
        else:
            success_rate = 0
        
        # Determine overall status
        if failed_checks == 0 and status_counts[CheckStatus.WARN] == 0:
            overall_status = "EXCELLENT"
        elif failed_checks == 0:
            overall_status = "GOOD"
        elif failed_checks <= 2:
            overall_status = "FAIR"
        else:
            overall_status = "POOR"
        
        # Performance summary
        benchmarks = [r for r in self.results if r.benchmark is not None]
        avg_benchmark = sum(r.benchmark for r in benchmarks) / len(benchmarks) if benchmarks else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'overall_status': overall_status,
            'success_rate': round(success_rate, 2),
            'summary': {
                'total_checks': total_checks,
                'passed': status_counts[CheckStatus.PASS],
                'failed': status_counts[CheckStatus.FAIL],
                'warnings': status_counts[CheckStatus.WARN],
                'info': status_counts[CheckStatus.INFO],
                'skipped': status_counts[CheckStatus.SKIP]
            },
            'performance': {
                'average_benchmark_time': round(avg_benchmark, 3),
                'benchmark_count': len(benchmarks)
            },
            'results': [asdict(result) for result in self.results]
        }
    
    def print_summary(self):
        """Print verification summary"""
        report = self.generate_report()
        
        print("\n" + "="*80)
        print("ENVIRONMENT VERIFICATION SUMMARY")
        print("="*80)
        
        print(f"Overall Status: {report['overall_status']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        print(f"System: {self.system_info['platform']}")
        print(f"Python: {self.system_info['python_version']}")
        
        print(f"\nResults Summary:")
        summary = report['summary']
        print(f"  ✅ Passed:   {summary['passed']}")
        print(f"  ❌ Failed:   {summary['failed']}")
        print(f"  ⚠️  Warnings: {summary['warnings']}")
        print(f"  ℹ️  Info:     {summary['info']}")
        print(f"  ⏭️  Skipped:  {summary['skipped']}")
        print(f"  📊 Total:    {summary['total_checks']}")
        
        if report['performance']['benchmark_count'] > 0:
            print(f"\nPerformance:")
            print(f"  Average benchmark time: {report['performance']['average_benchmark_time']:.3f}s")
        
        # Show critical failures
        critical_failures = [r for r in self.results if r.status == CheckStatus.FAIL]
        if critical_failures:
            print(f"\n❌ Critical Issues ({len(critical_failures)}):")
            for failure in critical_failures[:5]:  # Show first 5
                print(f"  • {failure.name}: {failure.message}")
                if failure.solution:
                    print(f"    Solution: {failure.solution}")
            
            if len(critical_failures) > 5:
                print(f"  ... and {len(critical_failures) - 5} more")
        
        # Show warnings
        warnings = [r for r in self.results if r.status == CheckStatus.WARN]
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings[:3]:  # Show first 3
                print(f"  • {warning.name}: {warning.message}")
        
        print("\n" + "="*80)
        
        if critical_failures:
            print("❌ VERIFICATION FAILED - Fix critical issues before proceeding")
            return False
        elif warnings:
            print("⚠️  VERIFICATION PASSED WITH WARNINGS - Review warnings")
            return True
        else:
            print("✅ VERIFICATION PASSED - Environment is ready")
            return True


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Environment Setup Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Run all checks
  %(prog)s --quick                      # Skip performance benchmarks  
  %(prog)s --verbose                    # Detailed output
  %(prog)s --output report.json         # Save detailed report
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Skip time-consuming checks (performance benchmarks)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save detailed report to JSON file'
    )
    
    parser.add_argument(
        '--format',
        choices=['summary', 'detailed', 'json'],
        default='summary',
        help='Output format'
    )
    
    args = parser.parse_args()
    
    # Create verifier
    verifier = EnvironmentVerifier(verbose=args.verbose, quick=args.quick)
    
    try:
        # Run all checks
        results = verifier.run_all_checks()
        
        # Generate report
        report = verifier.generate_report()
        
        # Output based on format
        if args.format == 'json':
            print(json.dumps(report, indent=2, default=str))
        elif args.format == 'detailed':
            for category, cat_results in results.items():
                print(f"\n{category.upper().replace('_', ' ')}:")
                print("-" * 50)
                for result in cat_results:
                    print(f"{result.status.value} {result.name}")
                    print(f"    {result.message}")
                    if result.solution:
                        print(f"    Solution: {result.solution}")
                    if result.benchmark:
                        print(f"    Benchmark: {result.benchmark:.3f}s")
        else:
            # Summary format (default)
            success = verifier.print_summary()
            
            # Save detailed report if requested
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                print(f"\nDetailed report saved to: {args.output}")
            
            return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\nVerification interrupted by user")
        return 1
    except Exception as e:
        print(f"Verification failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())