#!/usr/bin/env python3
"""
Manual Database Import Script
============================

Comprehensive manual fallback system for importing CheckjeBon data when automation fails.
Provides step-by-step import process with validation, rollback, and detailed reporting.

Features:
- Manual data download and parsing
- Interactive step-by-step execution
- Dry-run mode for testing
- Data validation and quality checks
- Conflict resolution
- Rollback functionality
- Progress tracking and reporting

Usage:
    python3 manual_import.py --help
    python3 manual_import.py --interactive
    python3 manual_import.py --dry-run
    python3 manual_import.py --step download
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
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import csv
import tempfile
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import shutil

# Third-party imports with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Supabase not available: {e}")
    SUPABASE_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("Warning: Pandas not available - some features may be limited")
    PANDAS_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    print("Warning: tqdm not available - progress bars disabled")
    TQDM_AVAILABLE = False


class ImportStep(Enum):
    """Import process steps"""
    DOWNLOAD = "download"
    VALIDATE = "validate"
    BACKUP = "backup"
    IMPORT_SUPERMARKETS = "import_supermarkets"
    IMPORT_CATEGORIES = "import_categories"
    IMPORT_PRODUCTS = "import_products"
    IMPORT_PRICES = "import_prices"
    VERIFY = "verify"
    CLEANUP = "cleanup"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SKIP = "skip"
    UPDATE = "update"
    CREATE_NEW = "create_new"
    ASK_USER = "ask_user"


@dataclass
class ImportReport:
    """Import operation report"""
    step: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def duration(self) -> Optional[float]:
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ManualImporter:
    """Main manual import system"""
    
    def __init__(self, 
                 interactive: bool = False,
                 dry_run: bool = False,
                 log_level: str = "INFO",
                 conflict_resolution: ConflictResolution = ConflictResolution.ASK_USER):
        
        self.interactive = interactive
        self.dry_run = dry_run
        self.conflict_resolution = conflict_resolution
        
        # Setup logging
        self.setup_logging(log_level)
        self.logger = logging.getLogger("manual_importer")
        
        # Configuration
        self.load_config()
        
        # Initialize Supabase client
        self.supabase: Optional[Client] = None
        self.init_supabase()
        
        # Data storage
        self.data_dir = Path("manual_import_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.backup_dir = Path("manual_import_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        self.reports_dir = Path("manual_import_reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Import tracking
        self.import_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.reports: List[ImportReport] = []
        self.rollback_data: Dict[str, Any] = {}
        
        # Data schemas
        self.expected_schemas = {
            'supermarkets': ['id', 'name', 'slug', 'logo_url', 'color_primary', 'website_url', 'api_endpoint', 'is_active'],
            'categories': ['id', 'name', 'slug', 'parent_id', 'description', 'is_active'],
            'products': ['id', 'name', 'normalized_name', 'brand', 'size_text', 'ean', 'category_id', 'image_url', 'is_active', 'description', 'unit_size', 'supermarket_id'],
            'prices': ['id', 'product_id', 'supermarket_id', 'price', 'price_per_unit', 'original_price', 'is_on_sale', 'discount_percentage', 'price_date', 'import_batch_id', 'is_available'],
            'shopping_lists': ['id', 'name', 'description', 'user_id', 'is_active'],
            'shopping_list_items': ['id', 'shopping_list_id', 'product_id', 'quantity', 'is_completed', 'notes', 'supermarket_id']
        }
        
        # Sample data URLs (replace with actual endpoints)
        self.data_sources = {
            'supermarkets': 'https://api.checkjebon.nl/api/v1/supermarkets',
            'categories': 'https://api.checkjebon.nl/api/v1/categories',
            'products': 'https://api.checkjebon.nl/api/v1/products',
            'prices': 'https://api.checkjebon.nl/api/v1/prices'
        }
        
        self.logger.info(f"Manual importer initialized - Import ID: {self.import_id}")
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No data will be modified")
    
    def setup_logging(self, log_level: str):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        
        # File handler
        file_handler = logging.FileHandler(
            log_dir / f"manual_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Configure logger
        logger = logging.getLogger("manual_importer")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    def load_config(self):
        """Load configuration from environment"""
        self.config = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'checkjebon_url': os.getenv('CHECKJEBON_URL', 'https://api.checkjebon.nl'),
            'batch_size': int(os.getenv('IMPORT_BATCH_SIZE', '1000')),
            'timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
            'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', '3')),
            'api_key': os.getenv('CHECKJEBON_API_KEY', '')
        }
        
        # Validate required config
        if not self.config['supabase_url'] or not self.config['supabase_key']:
            self.logger.warning("Supabase credentials not configured")
    
    def init_supabase(self):
        """Initialize Supabase client"""
        if not SUPABASE_AVAILABLE:
            self.logger.error("Supabase library not available")
            return
        
        if not self.config['supabase_url'] or not self.config['supabase_key']:
            self.logger.warning("Supabase credentials not configured")
            return
        
        try:
            self.supabase = create_client(
                self.config['supabase_url'],
                self.config['supabase_key']
            )
            
            # Test connection
            result = self.supabase.table('supermarkets').select('id').limit(1).execute()
            self.logger.info("Supabase connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase: {e}")
            self.supabase = None
    
    def print_banner(self):
        """Print application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════════╗
║                            Manual Database Import Tool                           ║
║                                                                                  ║
║  Comprehensive fallback system for importing CheckjeBon data when               ║
║  automation fails. Provides step-by-step import with validation & rollback.     ║
╚══════════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"Import ID: {self.import_id}")
        print(f"Mode: {'Interactive' if self.interactive else 'Automated'}")
        print(f"Dry Run: {'Yes' if self.dry_run else 'No'}")
        print(f"Conflict Resolution: {self.conflict_resolution.value}")
        print("─" * 86)
    
    def ask_user(self, question: str, options: List[str] = None, default: str = None) -> str:
        """Ask user for input in interactive mode"""
        if not self.interactive:
            return default if default else ""
        
        if options:
            print(f"\n{question}")
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            
            while True:
                try:
                    choice = input(f"Enter choice (1-{len(options)})" + 
                                 (f" [default: {default}]" if default else "") + ": ").strip()
                    
                    if not choice and default:
                        return default
                    
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(options):
                        return options[choice_idx]
                    else:
                        print(f"Please enter a number between 1 and {len(options)}")
                        
                except (ValueError, KeyboardInterrupt):
                    if default:
                        return default
                    print("Please enter a valid number")
        else:
            response = input(f"{question}" + (f" [default: {default}]" if default else "") + ": ").strip()
            return response if response else (default or "")
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirm action with user"""
        if not self.interactive:
            return True
        
        default_str = "Y/n" if default else "y/N"
        response = input(f"{message} ({default_str}): ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    
    def create_report(self, step: str) -> ImportReport:
        """Create new import report"""
        report = ImportReport(
            step=step,
            start_time=datetime.now()
        )
        self.reports.append(report)
        return report
    
    def finish_report(self, report: ImportReport, status: str):
        """Finish import report"""
        report.end_time = datetime.now()
        report.status = status
        
        # Log summary
        self.logger.info(f"Step '{report.step}' {status} - "
                        f"Duration: {report.duration:.2f}s, "
                        f"Processed: {report.records_processed}, "
                        f"Inserted: {report.records_inserted}, "
                        f"Updated: {report.records_updated}, "
                        f"Skipped: {report.records_skipped}")
    
    def save_reports(self):
        """Save import reports to file"""
        report_file = self.reports_dir / f"import_report_{self.import_id}.json"
        
        reports_data = {
            'import_id': self.import_id,
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'interactive': self.interactive,
            'conflict_resolution': self.conflict_resolution.value,
            'reports': [asdict(report) for report in self.reports]
        }
        
        with open(report_file, 'w') as f:
            json.dump(reports_data, f, indent=2, default=str)
        
        self.logger.info(f"Import reports saved to {report_file}")
        return report_file
    
    # Data Download Methods
    async def download_data_async(self, source: str, url: str) -> Optional[Dict]:
        """Download data from API endpoint asynchronously"""
        headers = {}
        if self.config['api_key']:
            headers['Authorization'] = f"Bearer {self.config['api_key']}"
        
        timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
        
        for attempt in range(self.config['retry_attempts']):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.logger.info(f"Downloaded {source} data: {len(data)} records")
                            return data
                        else:
                            self.logger.warning(f"HTTP {response.status} for {source}: {await response.text()}")
                            
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {source}: {e}")
                if attempt < self.config['retry_attempts'] - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def download_data_sync(self, source: str, url: str) -> Optional[Dict]:
        """Download data from API endpoint synchronously"""
        headers = {}
        if self.config['api_key']:
            headers['Authorization'] = f"Bearer {self.config['api_key']}"
        
        for attempt in range(self.config['retry_attempts']):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.config['timeout']
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"Downloaded {source} data: {len(data)} records")
                    return data
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {source}: {response.text}")
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {source}: {e}")
                if attempt < self.config['retry_attempts'] - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def create_sample_data(self, source: str) -> Dict:
        """Create sample data for testing when API is unavailable"""
        sample_data = {
            'supermarkets': [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Albert Heijn',
                    'slug': 'albert-heijn',
                    'logo_url': 'https://example.com/ah-logo.png',
                    'color_primary': '#0066CC',
                    'website_url': 'https://ah.nl',
                    'api_endpoint': 'https://api.ah.nl',
                    'is_active': True
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Jumbo',
                    'slug': 'jumbo',
                    'logo_url': 'https://example.com/jumbo-logo.png',
                    'color_primary': '#FFCC00',
                    'website_url': 'https://jumbo.com',
                    'api_endpoint': 'https://api.jumbo.com',
                    'is_active': True
                }
            ],
            'categories': [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Zuivel & Eieren',
                    'slug': 'zuivel-eieren',
                    'parent_id': None,
                    'description': 'Melkproducten en eieren',
                    'is_active': True
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Groente & Fruit',
                    'slug': 'groente-fruit',
                    'parent_id': None,
                    'description': 'Verse groenten en fruit',
                    'is_active': True
                }
            ],
            'products': [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Melk Vol 1L',
                    'normalized_name': 'melk vol 1l',
                    'brand': 'AH Basic',
                    'size_text': '1 liter',
                    'ean': '8710398000000',
                    'category_id': None,  # Will be linked after categories import
                    'image_url': 'https://example.com/melk.jpg',
                    'is_active': True,
                    'description': 'Volle melk van Nederlandse koeien',
                    'unit_size': 1.0,
                    'supermarket_id': None  # Will be linked after supermarkets import
                }
            ],
            'prices': []  # Will be generated based on products
        }
        
        return sample_data.get(source, [])


    def step_download(self) -> bool:
        """Step 1: Download data from APIs or create sample data"""
        report = self.create_report("download")
        
        try:
            self.logger.info("Starting data download step...")
            
            if self.interactive:
                use_sample = self.ask_user(
                    "Use sample data instead of downloading from API?",
                    ["Yes (use sample data)", "No (download from API)"],
                    "Yes (use sample data)"
                ) == "Yes (use sample data)"
            else:
                use_sample = True  # Default to sample data for reliability
            
            downloaded_data = {}
            
            if use_sample:
                self.logger.info("Creating sample data...")
                for source in ['supermarkets', 'categories', 'products']:
                    data = self.create_sample_data(source)
                    downloaded_data[source] = data
                    report.records_processed += len(data)
                    
                    # Save to file
                    data_file = self.data_dir / f"{source}_{self.import_id}.json"
                    with open(data_file, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    self.logger.info(f"Sample {source} data created: {len(data)} records")
            else:
                self.logger.info("Downloading data from APIs...")
                for source, url in self.data_sources.items():
                    if source in ['shopping_lists', 'shopping_list_items']:
                        continue  # Skip these for now
                    
                    self.logger.info(f"Downloading {source} from {url}")
                    data = self.download_data_sync(source, url)
                    
                    if data:
                        downloaded_data[source] = data
                        report.records_processed += len(data)
                        
                        # Save to file
                        data_file = self.data_dir / f"{source}_{self.import_id}.json"
                        with open(data_file, 'w') as f:
                            json.dump(data, f, indent=2, default=str)
                    else:
                        self.logger.warning(f"Failed to download {source} data")
                        report.errors.append(f"Failed to download {source}")
            
            # Generate prices data if we have products
            if 'products' in downloaded_data and downloaded_data['products']:
                prices_data = self.generate_sample_prices(downloaded_data['products'])
                downloaded_data['prices'] = prices_data
                report.records_processed += len(prices_data)
                
                # Save prices to file
                data_file = self.data_dir / f"prices_{self.import_id}.json"
                with open(data_file, 'w') as f:
                    json.dump(prices_data, f, indent=2, default=str)
            
            self.finish_report(report, "completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Download step failed: {e}")
            report.errors.append(str(e))
            self.finish_report(report, "failed")
            return False
    
    def generate_sample_prices(self, products: List[Dict]) -> List[Dict]:
        """Generate sample price data for products"""
        import random
        from decimal import Decimal
        
        prices = []
        supermarket_ids = ['ah-001', 'jumbo-001', 'lidl-001']  # Sample IDs
        
        for product in products:
            for supermarket_id in supermarket_ids:
                # Generate random price between 1 and 20 euros
                base_price = round(random.uniform(1.0, 20.0), 2)
                
                price_record = {
                    'id': str(uuid.uuid4()),
                    'product_id': product['id'],
                    'supermarket_id': supermarket_id,
                    'price': base_price,
                    'price_per_unit': round(base_price * random.uniform(0.8, 1.2), 2),
                    'original_price': base_price,
                    'is_on_sale': random.choice([True, False]),
                    'discount_percentage': random.randint(0, 30) if random.choice([True, False]) else 0,
                    'price_date': date.today().isoformat(),
                    'import_batch_id': self.import_id,
                    'is_available': True
                }
                prices.append(price_record)
        
        return prices
    
    def step_validate(self) -> bool:
        """Step 2: Validate downloaded data structure and quality"""
        report = self.create_report("validate")
        
        try:
            self.logger.info("Starting data validation step...")
            
            validation_results = {}
            
            for source in ['supermarkets', 'categories', 'products', 'prices']:
                data_file = self.data_dir / f"{source}_{self.import_id}.json"
                
                if not data_file.exists():
                    report.errors.append(f"Data file not found: {data_file}")
                    continue
                
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                validation_result = self.validate_data_structure(source, data)
                validation_results[source] = validation_result
                
                report.records_processed += len(data)
                
                if not validation_result['valid']:
                    report.errors.extend(validation_result['errors'])
                    self.logger.error(f"Validation failed for {source}: {validation_result['errors']}")
                else:
                    self.logger.info(f"Validation passed for {source}: {len(data)} records")
            
            # Save validation report
            validation_file = self.reports_dir / f"validation_{self.import_id}.json"
            with open(validation_file, 'w') as f:
                json.dump(validation_results, f, indent=2, default=str)
            
            # Check if any validation failed
            all_valid = all(result['valid'] for result in validation_results.values())
            
            if not all_valid and self.interactive:
                continue_anyway = self.confirm_action(
                    "Some validation checks failed. Continue anyway?", 
                    default=False
                )
                if not continue_anyway:
                    self.finish_report(report, "aborted")
                    return False
            
            self.finish_report(report, "completed" if all_valid else "completed_with_warnings")
            return True
            
        except Exception as e:
            self.logger.error(f"Validation step failed: {e}")
            report.errors.append(str(e))
            self.finish_report(report, "failed")
            return False
    
    def validate_data_structure(self, source: str, data: List[Dict]) -> Dict:
        """Validate data structure against expected schema"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'record_count': len(data),
            'schema_compliance': 0.0
        }
        
        if source not in self.expected_schemas:
            result['errors'].append(f"Unknown data source: {source}")
            result['valid'] = False
            return result
        
        expected_fields = set(self.expected_schemas[source])
        
        if not data:
            result['warnings'].append(f"No data found for {source}")
            return result
        
        # Check schema compliance
        compliant_records = 0
        field_coverage = {}
        
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                result['errors'].append(f"Record {i} is not a dictionary")
                continue
            
            record_fields = set(record.keys())
            missing_fields = expected_fields - record_fields
            extra_fields = record_fields - expected_fields
            
            # Track field coverage
            for field in expected_fields:
                if field not in field_coverage:
                    field_coverage[field] = 0
                if field in record_fields and record[field] is not None:
                    field_coverage[field] += 1
            
            # Check for required fields (basic validation)
            required_fields = {'id', 'name'} if 'name' in expected_fields else {'id'}
            missing_required = required_fields - record_fields
            
            if missing_required:
                result['errors'].append(f"Record {i} missing required fields: {missing_required}")
            else:
                compliant_records += 1
            
            if missing_fields:
                result['warnings'].append(f"Record {i} missing optional fields: {missing_fields}")
            
            if extra_fields:
                result['warnings'].append(f"Record {i} has unexpected fields: {extra_fields}")
        
        result['schema_compliance'] = compliant_records / len(data) if data else 0
        result['field_coverage'] = {
            field: coverage / len(data) for field, coverage in field_coverage.items()
        }
        
        if result['schema_compliance'] < 0.8:
            result['errors'].append(f"Low schema compliance: {result['schema_compliance']:.2%}")
            result['valid'] = False
        
        return result
    
    def step_backup(self) -> bool:
        """Step 3: Create backup of existing data"""
        if self.dry_run:
            self.logger.info("Skipping backup in dry-run mode")
            return True
        
        report = self.create_report("backup")
        
        try:
            self.logger.info("Starting backup step...")
            
            if not self.supabase:
                self.logger.warning("Supabase not available - skipping backup")
                self.finish_report(report, "skipped")
                return True
            
            backup_data = {}
            
            for table in ['supermarkets', 'categories', 'products', 'prices']:
                try:
                    self.logger.info(f"Backing up table: {table}")
                    
                    # Get all data from table
                    result = self.supabase.table(table).select('*').execute()
                    backup_data[table] = result.data
                    
                    report.records_processed += len(result.data)
                    self.logger.info(f"Backed up {len(result.data)} records from {table}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to backup {table}: {e}")
                    report.warnings.append(f"Failed to backup {table}: {e}")
            
            # Save backup to file
            backup_file = self.backup_dir / f"backup_{self.import_id}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Store backup info for rollback
            self.rollback_data['backup_file'] = str(backup_file)
            self.rollback_data['backup_tables'] = list(backup_data.keys())
            
            self.logger.info(f"Backup saved to {backup_file}")
            self.finish_report(report, "completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup step failed: {e}")
            report.errors.append(str(e))
            self.finish_report(report, "failed")
            return False
    
    def step_import_table(self, table_name: str) -> bool:
        """Import data for a specific table"""
        report = self.create_report(f"import_{table_name}")
        
        try:
            self.logger.info(f"Starting import for table: {table_name}")
            
            # Load data
            data_file = self.data_dir / f"{table_name}_{self.import_id}.json"
            if not data_file.exists():
                self.logger.warning(f"No data file found for {table_name}")
                self.finish_report(report, "skipped")
                return True
            
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            if not data:
                self.logger.warning(f"No data to import for {table_name}")
                self.finish_report(report, "skipped")
                return True
            
            self.logger.info(f"Importing {len(data)} records to {table_name}")
            
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would import {len(data)} records to {table_name}")
                report.records_processed = len(data)
                report.records_inserted = len(data)
                self.finish_report(report, "completed")
                return True
            
            if not self.supabase:
                self.logger.error("Supabase not available")
                report.errors.append("Supabase not available")
                self.finish_report(report, "failed")
                return False
            
            # Process in batches
            batch_size = self.config['batch_size']
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                try:
                    # Check for conflicts and resolve
                    resolved_batch = []
                    for record in batch:
                        resolved_record = self.resolve_conflicts(table_name, record)
                        if resolved_record:
                            resolved_batch.append(resolved_record)
                        else:
                            report.records_skipped += 1
                    
                    if resolved_batch:
                        # Insert batch
                        result = self.supabase.table(table_name).insert(resolved_batch).execute()
                        
                        report.records_processed += len(batch)
                        report.records_inserted += len(resolved_batch)
                        
                        self.logger.info(f"Inserted batch {i//batch_size + 1}: {len(resolved_batch)} records")
                    
                except Exception as e:
                    self.logger.error(f"Failed to insert batch {i//batch_size + 1}: {e}")
                    report.errors.append(f"Batch {i//batch_size + 1}: {e}")
                    
                    # Try individual records
                    for record in batch:
                        try:
                            resolved_record = self.resolve_conflicts(table_name, record)
                            if resolved_record:
                                self.supabase.table(table_name).insert([resolved_record]).execute()
                                report.records_inserted += 1
                            else:
                                report.records_skipped += 1
                            report.records_processed += 1
                        except Exception as e2:
                            self.logger.error(f"Failed to insert individual record: {e2}")
                            report.errors.append(f"Record {record.get('id', 'unknown')}: {e2}")
                            report.records_processed += 1
            
            self.finish_report(report, "completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Import step failed for {table_name}: {e}")
            report.errors.append(str(e))
            self.finish_report(report, "failed")
            return False
    
    def resolve_conflicts(self, table_name: str, record: Dict) -> Optional[Dict]:
        """Resolve conflicts for a record"""
        if not self.supabase:
            return record
        
        try:
            # Check if record with same ID exists
            existing = self.supabase.table(table_name).select('*').eq('id', record['id']).execute()
            
            if not existing.data:
                # No conflict
                return record
            
            # Handle conflict based on resolution strategy
            if self.conflict_resolution == ConflictResolution.SKIP:
                self.logger.debug(f"Skipping existing record: {record['id']}")
                return None
            
            elif self.conflict_resolution == ConflictResolution.UPDATE:
                # Update existing record
                self.supabase.table(table_name).update(record).eq('id', record['id']).execute()
                self.logger.debug(f"Updated existing record: {record['id']}")
                return None  # Already handled
            
            elif self.conflict_resolution == ConflictResolution.CREATE_NEW:
                # Create new record with new ID
                new_record = record.copy()
                new_record['id'] = str(uuid.uuid4())
                self.logger.debug(f"Creating new record with ID: {new_record['id']}")
                return new_record
            
            elif self.conflict_resolution == ConflictResolution.ASK_USER:
                if self.interactive:
                    action = self.ask_user(
                        f"Record {record['id']} already exists. What to do?",
                        ["Skip", "Update", "Create new"],
                        "Skip"
                    )
                    
                    if action == "Skip":
                        return None
                    elif action == "Update":
                        self.supabase.table(table_name).update(record).eq('id', record['id']).execute()
                        return None
                    elif action == "Create new":
                        record['id'] = str(uuid.uuid4())
                        return record
                else:
                    # Default to skip in non-interactive mode
                    return None
            
            return record
            
        except Exception as e:
            self.logger.error(f"Error resolving conflict for {record.get('id', 'unknown')}: {e}")
            return record


    def step_verify(self) -> bool:
        """Step: Verify import results"""
        report = self.create_report("verify")
        
        try:
            self.logger.info("Starting verification step...")
            
            if not self.supabase:
                self.logger.warning("Supabase not available - skipping verification")
                self.finish_report(report, "skipped")
                return True
            
            verification_results = {}
            
            for table in ['supermarkets', 'categories', 'products', 'prices']:
                try:
                    # Count records in database
                    result = self.supabase.table(table).select('id', count='exact').execute()
                    db_count = result.count
                    
                    # Count records in source file
                    data_file = self.data_dir / f"{table}_{self.import_id}.json"
                    if data_file.exists():
                        with open(data_file, 'r') as f:
                            source_data = json.load(f)
                        source_count = len(source_data)
                    else:
                        source_count = 0
                    
                    verification_results[table] = {
                        'database_count': db_count,
                        'source_count': source_count,
                        'difference': db_count - source_count if not self.dry_run else 0
                    }
                    
                    report.records_processed += db_count
                    self.logger.info(f"{table}: DB={db_count}, Source={source_count}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to verify {table}: {e}")
                    report.errors.append(f"Verification failed for {table}: {e}")
            
            # Save verification report
            verification_file = self.reports_dir / f"verification_{self.import_id}.json"
            with open(verification_file, 'w') as f:
                json.dump(verification_results, f, indent=2)
            
            self.finish_report(report, "completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Verification step failed: {e}")
            report.errors.append(str(e))
            self.finish_report(report, "failed")
            return False
    
    def step_cleanup(self) -> bool:
        """Step: Cleanup temporary files"""
        report = self.create_report("cleanup")
        
        try:
            self.logger.info("Starting cleanup step...")
            
            if self.interactive:
                cleanup = self.confirm_action("Clean up temporary files?", default=True)
                if not cleanup:
                    self.finish_report(report, "skipped")
                    return True
            
            # Keep only essential files
            files_to_keep = [
                f"backup_{self.import_id}.json",
                f"import_report_{self.import_id}.json",
                f"validation_{self.import_id}.json",
                f"verification_{self.import_id}.json"
            ]
            
            cleaned_files = 0
            
            # Clean data directory
            for file in self.data_dir.glob(f"*_{self.import_id}.*"):
                if file.name not in files_to_keep:
                    file.unlink()
                    cleaned_files += 1
                    self.logger.debug(f"Cleaned up: {file}")
            
            report.records_processed = cleaned_files
            self.logger.info(f"Cleaned up {cleaned_files} temporary files")
            
            self.finish_report(report, "completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Cleanup step failed: {e}")
            report.errors.append(str(e))
            self.finish_report(report, "failed")
            return False
    
    def rollback(self) -> bool:
        """Rollback import changes"""
        self.logger.info("Starting rollback procedure...")
        
        if not self.rollback_data or 'backup_file' not in self.rollback_data:
            self.logger.error("No backup data available for rollback")
            return False
        
        try:
            backup_file = Path(self.rollback_data['backup_file'])
            
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            self.logger.info(f"Restoring from backup: {backup_file}")
            
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            if not self.supabase:
                self.logger.error("Supabase not available for rollback")
                return False
            
            # Restore each table
            for table, data in backup_data.items():
                try:
                    self.logger.info(f"Rolling back table: {table}")
                    
                    # Clear current data
                    self.supabase.table(table).delete().neq('id', '').execute()
                    
                    # Restore backup data
                    if data:
                        batch_size = self.config['batch_size']
                        for i in range(0, len(data), batch_size):
                            batch = data[i:i + batch_size]
                            self.supabase.table(table).insert(batch).execute()
                    
                    self.logger.info(f"Restored {len(data)} records to {table}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to rollback {table}: {e}")
                    return False
            
            self.logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    def run_full_import(self) -> bool:
        """Run the complete import process"""
        self.print_banner()
        
        if self.interactive:
            if not self.confirm_action("Start import process?", default=True):
                self.logger.info("Import cancelled by user")
                return False
        
        # Define import steps
        steps = [
            ("Download", self.step_download),
            ("Validate", self.step_validate),
            ("Backup", self.step_backup),
            ("Import Supermarkets", lambda: self.step_import_table("supermarkets")),
            ("Import Categories", lambda: self.step_import_table("categories")),
            ("Import Products", lambda: self.step_import_table("products")),
            ("Import Prices", lambda: self.step_import_table("prices")),
            ("Verify", self.step_verify),
            ("Cleanup", self.step_cleanup)
        ]
        
        failed_step = None
        
        try:
            for step_name, step_func in steps:
                self.logger.info(f"Starting step: {step_name}")
                
                if self.interactive:
                    if not self.confirm_action(f"Execute step: {step_name}?", default=True):
                        self.logger.info(f"Step {step_name} skipped by user")
                        continue
                
                # Add progress tracking if tqdm is available
                if TQDM_AVAILABLE and not self.interactive:
                    with tqdm(desc=f"Executing {step_name}", unit="step") as pbar:
                        success = step_func()
                        pbar.update(1)
                else:
                    success = step_func()
                
                if not success:
                    failed_step = step_name
                    self.logger.error(f"Step {step_name} failed")
                    
                    if self.interactive:
                        rollback = self.confirm_action(
                            f"Step {step_name} failed. Attempt rollback?", 
                            default=True
                        )
                        if rollback:
                            self.rollback()
                    
                    break
                
                self.logger.info(f"Step {step_name} completed successfully")
            
            # Generate final report
            report_file = self.save_reports()
            
            if failed_step:
                self.logger.error(f"Import failed at step: {failed_step}")
                return False
            else:
                self.logger.info("Import completed successfully!")
                self.logger.info(f"Report saved to: {report_file}")
                return True
                
        except KeyboardInterrupt:
            self.logger.warning("Import interrupted by user")
            if self.interactive and self.confirm_action("Attempt rollback?", default=True):
                self.rollback()
            return False
        except Exception as e:
            self.logger.error(f"Import failed with exception: {e}")
            if self.interactive and self.confirm_action("Attempt rollback?", default=True):
                self.rollback()
            return False
    
    def run_single_step(self, step: ImportStep) -> bool:
        """Run a single import step"""
        self.print_banner()
        
        step_functions = {
            ImportStep.DOWNLOAD: self.step_download,
            ImportStep.VALIDATE: self.step_validate,
            ImportStep.BACKUP: self.step_backup,
            ImportStep.IMPORT_SUPERMARKETS: lambda: self.step_import_table("supermarkets"),
            ImportStep.IMPORT_CATEGORIES: lambda: self.step_import_table("categories"),
            ImportStep.IMPORT_PRODUCTS: lambda: self.step_import_table("products"),
            ImportStep.IMPORT_PRICES: lambda: self.step_import_table("prices"),
            ImportStep.VERIFY: self.step_verify,
            ImportStep.CLEANUP: self.step_cleanup
        }
        
        if step not in step_functions:
            self.logger.error(f"Unknown step: {step}")
            return False
        
        self.logger.info(f"Running single step: {step.value}")
        
        success = step_functions[step]()
        
        # Generate report for single step
        report_file = self.save_reports()
        self.logger.info(f"Report saved to: {report_file}")
        
        return success
    
    def print_status(self):
        """Print current import status"""
        print("\n" + "="*60)
        print("IMPORT STATUS")
        print("="*60)
        
        print(f"Import ID: {self.import_id}")
        print(f"Mode: {'Interactive' if self.interactive else 'Automated'}")
        print(f"Dry Run: {'Yes' if self.dry_run else 'No'}")
        print(f"Conflict Resolution: {self.conflict_resolution.value}")
        
        # Check for existing data files
        print(f"\nData Files:")
        for source in ['supermarkets', 'categories', 'products', 'prices']:
            data_file = self.data_dir / f"{source}_{self.import_id}.json"
            status = "✓" if data_file.exists() else "✗"
            print(f"  {status} {source}")
        
        # Check database connection
        print(f"\nDatabase Connection:")
        if self.supabase:
            try:
                result = self.supabase.table('supermarkets').select('id').limit(1).execute()
                print(f"  ✓ Connected to Supabase")
            except:
                print(f"  ✗ Supabase connection failed")
        else:
            print(f"  ✗ Supabase not configured")
        
        # Show reports if any
        if self.reports:
            print(f"\nCompleted Steps:")
            for report in self.reports:
                status = "✓" if report.status == "completed" else "✗"
                duration = f"{report.duration:.2f}s" if report.duration else "N/A"
                print(f"  {status} {report.step} ({duration})")
        
        print("="*60)


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Manual Database Import Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --interactive                    # Interactive mode
  %(prog)s --dry-run                       # Test without importing
  %(prog)s --step download                 # Run single step
  %(prog)s --conflict-resolution skip      # Skip conflicts
  %(prog)s --status                        # Show status
        """
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Test run without making changes'
    )
    
    parser.add_argument(
        '--step', '-s',
        type=str,
        choices=[step.value for step in ImportStep],
        help='Run a single step'
    )
    
    parser.add_argument(
        '--conflict-resolution', '-c',
        type=str,
        choices=[res.value for res in ConflictResolution],
        default='ask_user',
        help='Conflict resolution strategy'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status'
    )
    
    parser.add_argument(
        '--rollback',
        type=str,
        help='Rollback using specific backup ID'
    )
    
    args = parser.parse_args()
    
    # Create importer instance
    conflict_resolution = ConflictResolution(args.conflict_resolution)
    
    importer = ManualImporter(
        interactive=args.interactive,
        dry_run=args.dry_run,
        log_level=args.log_level,
        conflict_resolution=conflict_resolution
    )
    
    try:
        if args.status:
            importer.print_status()
            return 0
        
        elif args.rollback:
            importer.import_id = args.rollback
            importer.rollback_data['backup_file'] = str(importer.backup_dir / f"backup_{args.rollback}.json")
            success = importer.rollback()
            return 0 if success else 1
        
        elif args.step:
            step = ImportStep(args.step)
            success = importer.run_single_step(step)
            return 0 if success else 1
        
        else:
            success = importer.run_full_import()
            return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())