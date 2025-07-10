#!/usr/bin/env python3
"""
Supabase Import Debugging Script
===============================

Comprehensive debugging tool to troubleshoot Supabase database import issues.
Tests each component step-by-step with detailed logging and validation.
"""

import os
import sys
import json
import time
import logging
import asyncio
import aiohttp
import traceback
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import csv
import tempfile

# Third-party imports (with error handling)
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
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("Warning: Requests not available - using aiohttp only")
    REQUESTS_AVAILABLE = False


class DatabaseDebugger:
    """Main debugging class for Supabase import issues"""
    
    def __init__(self, log_level: str = "INFO"):
        self.setup_logging(log_level)
        self.logger = logging.getLogger("supabase_debugger")
        
        # Configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.checkjebon_url = os.getenv('CHECKJEBON_URL', 'https://api.checkjebon.nl')
        
        # Initialize Supabase client
        self.supabase: Optional[Client] = None
        
        # Debug data storage
        self.debug_dir = Path("debug_output")
        self.debug_dir.mkdir(exist_ok=True)
        
        # Expected table schemas
        self.expected_schemas = {
            'categories': ['id', 'name', 'slug', 'parent_id', 'description', 'is_active', 'created_at', 'updated_at'],
            'supermarkets': ['id', 'name', 'slug', 'logo_url', 'color_primary', 'website_url', 'api_endpoint', 'is_active', 'created_at', 'updated_at'],
            'products': ['id', 'name', 'normalized_name', 'brand', 'size_text', 'ean', 'category_id', 'image_url', 'is_active', 'created_at', 'updated_at', 'description', 'unit_size', 'supermarket_id'],
            'prices': ['id', 'product_id', 'supermarket_id', 'price', 'price_per_unit', 'original_price', 'is_on_sale', 'discount_percentage', 'price_date', 'import_batch_id', 'created_at', 'updated_at', 'is_available'],
            'shopping_lists': ['id', 'name', 'description', 'user_id', 'is_active', 'created_at', 'updated_at'],
            'shopping_list_items': ['id', 'shopping_list_id', 'product_id', 'quantity', 'is_completed', 'notes', 'created_at', 'updated_at', 'supermarket_id']
        }
        
        # Test data
        self.test_data = {
            'categories': [
                {'name': 'Test Category', 'slug': 'test-category', 'description': 'Debug test category'},
            ],
            'supermarkets': [
                {'name': 'Test Supermarket', 'slug': 'test-supermarket', 'is_active': True},
            ]
        }
    
    def setup_logging(self, log_level: str):
        """Setup comprehensive logging"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        
        # File handler
        file_handler = logging.FileHandler(log_dir / f"debug_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_status(self, message: str, status: str = "INFO"):
        """Print formatted status message"""
        icons = {"SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}
        icon = icons.get(status, "•")
        print(f"{icon} {message}")
        
        # Also log to file
        if status == "ERROR":
            self.logger.error(message)
        elif status == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def save_debug_data(self, filename: str, data: Any):
        """Save debug data to file"""
        filepath = self.debug_dir / filename
        try:
            if isinstance(data, (dict, list)):
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                with open(filepath, 'w') as f:
                    f.write(str(data))
            
            self.print_status(f"Debug data saved to {filepath}", "INFO")
            return True
        except Exception as e:
            self.print_status(f"Failed to save debug data: {e}", "ERROR")
            return False
    
    def check_environment_variables(self) -> bool:
        """Check and validate environment variables"""
        self.print_header("Environment Variables Check")
        
        required_vars = {
            'SUPABASE_URL': self.supabase_url,
            'SUPABASE_KEY': self.supabase_key
        }
        
        optional_vars = {
            'CHECKJEBON_URL': self.checkjebon_url,
            'REDIS_URL': os.getenv('REDIS_URL'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
        }
        
        all_good = True
        
        # Check required variables
        for var_name, var_value in required_vars.items():
            if var_value:
                self.print_status(f"{var_name}: {var_value[:20]}...", "SUCCESS")
            else:
                self.print_status(f"{var_name}: NOT SET", "ERROR")
                all_good = False
        
        # Check optional variables
        for var_name, var_value in optional_vars.items():
            if var_value:
                self.print_status(f"{var_name}: {var_value}", "INFO")
            else:
                self.print_status(f"{var_name}: Not set (optional)", "INFO")
        
        # Save environment info
        env_info = {**required_vars, **optional_vars}
        self.save_debug_data("environment_variables.json", env_info)
        
        return all_good
    
    def check_dependencies(self) -> bool:
        """Check required dependencies"""
        self.print_header("Dependencies Check")
        
        dependencies = {
            'supabase': SUPABASE_AVAILABLE,
            'pandas': PANDAS_AVAILABLE,
            'requests': REQUESTS_AVAILABLE,
            'aiohttp': True,  # Should always be available if we got this far
            'json': True,
            'logging': True
        }
        
        all_good = True
        for dep_name, available in dependencies.items():
            if available:
                self.print_status(f"{dep_name}: Available", "SUCCESS")
            else:
                self.print_status(f"{dep_name}: Missing", "ERROR")
                all_good = False
        
        return all_good
    
    def test_network_connectivity(self) -> bool:
        """Test network connectivity to required services"""
        self.print_header("Network Connectivity Check")
        
        test_urls = [
            ('Supabase', self.supabase_url),
            ('CheckjeBon API', self.checkjebon_url),
            ('Google DNS', 'https://8.8.8.8'),
            ('Internet', 'https://httpbin.org/status/200')
        ]
        
        all_good = True
        connectivity_results = {}
        
        for service_name, url in test_urls:
            if not url:
                self.print_status(f"{service_name}: URL not configured", "WARNING")
                continue
            
            try:
                if REQUESTS_AVAILABLE:
                    import requests
                    response = requests.get(url, timeout=10)
                    if response.status_code in [200, 401, 403]:  # 401/403 means connection works
                        self.print_status(f"{service_name}: Connected (HTTP {response.status_code})", "SUCCESS")
                        connectivity_results[service_name] = "connected"
                    else:
                        self.print_status(f"{service_name}: HTTP {response.status_code}", "WARNING")
                        connectivity_results[service_name] = f"http_{response.status_code}"
                else:
                    # Fallback using asyncio
                    import asyncio
                    result = asyncio.run(self._test_url_async(url))
                    if result:
                        self.print_status(f"{service_name}: Connected", "SUCCESS")
                        connectivity_results[service_name] = "connected"
                    else:
                        self.print_status(f"{service_name}: Failed", "ERROR")
                        connectivity_results[service_name] = "failed"
                        all_good = False
                        
            except Exception as e:
                self.print_status(f"{service_name}: Error - {e}", "ERROR")
                connectivity_results[service_name] = f"error: {e}"
                all_good = False
        
        self.save_debug_data("network_connectivity.json", connectivity_results)
        return all_good
    
    async def _test_url_async(self, url: str) -> bool:
        """Test URL connectivity using aiohttp"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status in [200, 401, 403]
        except:
            return False
    
    def test_supabase_connection(self) -> bool:
        """Test Supabase connection and authentication"""
        self.print_header("Supabase Connection Test")
        
        if not SUPABASE_AVAILABLE:
            self.print_status("Supabase client not available", "ERROR")
            return False
        
        if not self.supabase_url or not self.supabase_key:
            self.print_status("Supabase credentials not configured", "ERROR")
            return False
        
        try:
            # Initialize client
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            self.print_status("Supabase client initialized", "SUCCESS")
            
            # Test basic connectivity
            result = self.supabase.table('categories').select('*').limit(1).execute()
            self.print_status("Database query successful", "SUCCESS")
            
            # Test authentication
            if hasattr(result, 'data'):
                self.print_status("Authentication successful", "SUCCESS")
                return True
            else:
                self.print_status("Authentication may have issues", "WARNING")
                return False
                
        except Exception as e:
            self.print_status(f"Supabase connection failed: {e}", "ERROR")
            self.logger.error(f"Supabase connection error: {traceback.format_exc()}")
            return False
    
    def verify_table_schemas(self) -> bool:
        """Verify table schemas match expected structure"""
        self.print_header("Table Schema Verification")
        
        if not self.supabase:
            self.print_status("Supabase client not initialized", "ERROR")
            return False
        
        schema_results = {}
        all_good = True
        
        for table_name, expected_columns in self.expected_schemas.items():
            try:
                # Get table structure by querying with limit 0
                result = self.supabase.table(table_name).select('*').limit(0).execute()
                
                if hasattr(result, 'data'):
                    self.print_status(f"Table '{table_name}': Accessible", "SUCCESS")
                    
                    # Try to get actual column info by inserting/selecting dummy data
                    try:
                        # Try a more comprehensive query to check columns
                        sample_result = self.supabase.table(table_name).select('*').limit(1).execute()
                        
                        if sample_result.data:
                            actual_columns = list(sample_result.data[0].keys())
                            missing_columns = set(expected_columns) - set(actual_columns)
                            extra_columns = set(actual_columns) - set(expected_columns)
                            
                            schema_results[table_name] = {
                                'status': 'accessible',
                                'expected_columns': expected_columns,
                                'actual_columns': actual_columns,
                                'missing_columns': list(missing_columns),
                                'extra_columns': list(extra_columns),
                                'row_count': len(sample_result.data)
                            }
                            
                            if missing_columns:
                                self.print_status(f"Table '{table_name}': Missing columns - {missing_columns}", "WARNING")
                            if extra_columns:
                                self.print_status(f"Table '{table_name}': Extra columns - {extra_columns}", "INFO")
                        else:
                            schema_results[table_name] = {
                                'status': 'empty',
                                'expected_columns': expected_columns,
                                'row_count': 0
                            }
                            self.print_status(f"Table '{table_name}': Empty (cannot verify columns)", "WARNING")
                    
                    except Exception as e:
                        schema_results[table_name] = {
                            'status': 'error',
                            'error': str(e),
                            'expected_columns': expected_columns
                        }
                        self.print_status(f"Table '{table_name}': Column check failed - {e}", "ERROR")
                        all_good = False
                
                else:
                    self.print_status(f"Table '{table_name}': Not accessible", "ERROR")
                    schema_results[table_name] = {'status': 'not_accessible'}
                    all_good = False
                    
            except Exception as e:
                self.print_status(f"Table '{table_name}': Error - {e}", "ERROR")
                schema_results[table_name] = {'status': 'error', 'error': str(e)}
                all_good = False
        
        self.save_debug_data("table_schemas.json", schema_results)
        return all_good
    
    def test_database_permissions(self) -> bool:
        """Test database permissions (read, write, update, delete)"""
        self.print_header("Database Permissions Test")
        
        if not self.supabase:
            self.print_status("Supabase client not initialized", "ERROR")
            return False
        
        permissions_results = {}
        all_good = True
        
        # Test on categories table (usually safest for testing)
        test_table = 'categories'
        test_data = {
            'name': f'DEBUG_TEST_{int(time.time())}',
            'slug': f'debug-test-{int(time.time())}',
            'description': 'Debug test category - safe to delete'
        }
        
        try:
            # Test SELECT permission
            try:
                result = self.supabase.table(test_table).select('*').limit(1).execute()
                self.print_status("SELECT permission: OK", "SUCCESS")
                permissions_results['select'] = True
            except Exception as e:
                self.print_status(f"SELECT permission: FAILED - {e}", "ERROR")
                permissions_results['select'] = False
                all_good = False
            
            # Test INSERT permission
            try:
                insert_result = self.supabase.table(test_table).insert(test_data).execute()
                if insert_result.data:
                    inserted_id = insert_result.data[0]['id']
                    self.print_status("INSERT permission: OK", "SUCCESS")
                    permissions_results['insert'] = True
                    
                    # Test UPDATE permission
                    try:
                        update_data = {'description': 'Updated debug test category'}
                        update_result = self.supabase.table(test_table).update(update_data).eq('id', inserted_id).execute()
                        self.print_status("UPDATE permission: OK", "SUCCESS")
                        permissions_results['update'] = True
                    except Exception as e:
                        self.print_status(f"UPDATE permission: FAILED - {e}", "ERROR")
                        permissions_results['update'] = False
                        all_good = False
                    
                    # Test DELETE permission
                    try:
                        delete_result = self.supabase.table(test_table).delete().eq('id', inserted_id).execute()
                        self.print_status("DELETE permission: OK", "SUCCESS")
                        permissions_results['delete'] = True
                    except Exception as e:
                        self.print_status(f"DELETE permission: FAILED - {e}", "ERROR")
                        permissions_results['delete'] = False
                        # Not necessarily a blocker for imports
                else:
                    self.print_status("INSERT permission: FAILED - No data returned", "ERROR")
                    permissions_results['insert'] = False
                    all_good = False
                    
            except Exception as e:
                self.print_status(f"INSERT permission: FAILED - {e}", "ERROR")
                permissions_results['insert'] = False
                all_good = False
        
        except Exception as e:
            self.print_status(f"Permission test failed: {e}", "ERROR")
            permissions_results['error'] = str(e)
            all_good = False
        
        self.save_debug_data("database_permissions.json", permissions_results)
        return all_good
    
    async def test_checkjebon_api(self) -> Tuple[bool, Optional[Dict]]:
        """Test CheckjeBon API access and data retrieval"""
        self.print_header("CheckjeBon API Test")
        
        test_results = {}
        
        if not self.checkjebon_url:
            self.print_status("CheckjeBon URL not configured", "ERROR")
            return False, None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test API endpoints
                endpoints_to_test = [
                    '/health',
                    '/api/v1/products',
                    '/api/v1/supermarkets',
                    '/api/v1/categories',
                    '/'  # fallback
                ]
                
                working_endpoint = None
                api_data = None
                
                for endpoint in endpoints_to_test:
                    url = f"{self.checkjebon_url.rstrip('/')}{endpoint}"
                    try:
                        self.print_status(f"Testing endpoint: {endpoint}", "INFO")
                        
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                            if response.status == 200:
                                content_type = response.headers.get('content-type', '')
                                
                                if 'application/json' in content_type:
                                    api_data = await response.json()
                                    working_endpoint = endpoint
                                    self.print_status(f"Endpoint {endpoint}: OK (JSON response)", "SUCCESS")
                                    break
                                else:
                                    text_data = await response.text()
                                    if len(text_data) > 0:
                                        working_endpoint = endpoint
                                        api_data = {'content': text_data[:500]}  # First 500 chars
                                        self.print_status(f"Endpoint {endpoint}: OK (Text response)", "SUCCESS")
                                        break
                            else:
                                self.print_status(f"Endpoint {endpoint}: HTTP {response.status}", "WARNING")
                                
                    except asyncio.TimeoutError:
                        self.print_status(f"Endpoint {endpoint}: Timeout", "WARNING")
                    except Exception as e:
                        self.print_status(f"Endpoint {endpoint}: Error - {e}", "WARNING")
                
                if working_endpoint:
                    test_results = {
                        'status': 'success',
                        'working_endpoint': working_endpoint,
                        'api_url': self.checkjebon_url,
                        'data_sample': api_data,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Try to parse and validate data structure
                    if isinstance(api_data, dict):
                        if 'products' in api_data:
                            products_count = len(api_data.get('products', []))
                            self.print_status(f"Found {products_count} products in API response", "SUCCESS")
                        
                        if 'supermarkets' in api_data:
                            supermarkets_count = len(api_data.get('supermarkets', []))
                            self.print_status(f"Found {supermarkets_count} supermarkets in API response", "SUCCESS")
                    
                    self.save_debug_data("checkjebon_api_response.json", test_results)
                    return True, api_data
                else:
                    test_results = {
                        'status': 'failed',
                        'api_url': self.checkjebon_url,
                        'error': 'No working endpoints found',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.print_status("No working CheckjeBon API endpoints found", "ERROR")
                    self.save_debug_data("checkjebon_api_error.json", test_results)
                    return False, None
                    
        except Exception as e:
            error_msg = f"CheckjeBon API test failed: {e}"
            self.print_status(error_msg, "ERROR")
            self.logger.error(f"CheckjeBon API error: {traceback.format_exc()}")
            
            test_results = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.save_debug_data("checkjebon_api_error.json", test_results)
            return False, None
    
    def test_data_parsing(self, api_data: Optional[Dict]) -> bool:
        """Test data parsing and transformation"""
        self.print_header("Data Parsing Test")
        
        if not api_data:
            self.print_status("No API data available for parsing test", "ERROR")
            return False
        
        parsing_results = {}
        all_good = True
        
        try:
            # Test parsing different data types
            data_types = ['products', 'supermarkets', 'categories', 'prices']
            
            for data_type in data_types:
                if data_type in api_data:
                    raw_data = api_data[data_type]
                    
                    if isinstance(raw_data, list) and len(raw_data) > 0:
                        sample_item = raw_data[0]
                        
                        # Basic validation
                        if isinstance(sample_item, dict):
                            parsing_results[data_type] = {
                                'status': 'success',
                                'count': len(raw_data),
                                'sample_keys': list(sample_item.keys()),
                                'sample_item': sample_item
                            }
                            self.print_status(f"{data_type}: {len(raw_data)} items, sample keys: {list(sample_item.keys())}", "SUCCESS")
                        else:
                            parsing_results[data_type] = {
                                'status': 'warning',
                                'issue': 'Items are not dictionaries',
                                'sample_type': type(sample_item).__name__
                            }
                            self.print_status(f"{data_type}: Items are not dictionaries", "WARNING")
                            all_good = False
                    else:
                        parsing_results[data_type] = {
                            'status': 'warning',
                            'issue': 'No data available',
                            'data_type': type(raw_data).__name__
                        }
                        self.print_status(f"{data_type}: No data available", "WARNING")
                else:
                    parsing_results[data_type] = {
                        'status': 'missing',
                        'issue': 'Not present in API response'
                    }
                    self.print_status(f"{data_type}: Not present in API response", "INFO")
            
            # Test data transformation
            if 'products' in api_data and api_data['products']:
                sample_product = api_data['products'][0]
                try:
                    # Test product transformation
                    transformed_product = self._transform_product_data(sample_product)
                    parsing_results['product_transformation'] = {
                        'status': 'success',
                        'original': sample_product,
                        'transformed': transformed_product
                    }
                    self.print_status("Product data transformation: OK", "SUCCESS")
                except Exception as e:
                    parsing_results['product_transformation'] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    self.print_status(f"Product data transformation failed: {e}", "ERROR")
                    all_good = False
            
            self.save_debug_data("data_parsing_results.json", parsing_results)
            
        except Exception as e:
            self.print_status(f"Data parsing test failed: {e}", "ERROR")
            self.logger.error(f"Data parsing error: {traceback.format_exc()}")
            all_good = False
        
        return all_good
    
    def _transform_product_data(self, product_data: Dict) -> Dict:
        """Transform raw product data to database format"""
        # This is a simplified transformation - adjust based on actual API structure
        transformed = {
            'name': product_data.get('name', '').strip(),
            'normalized_name': product_data.get('name', '').lower().strip(),
            'brand': product_data.get('brand', '').strip() or None,
            'size_text': product_data.get('size', '').strip() or None,
            'ean': product_data.get('ean', '').strip() or None,
            'description': product_data.get('description', '').strip() or None,
            'unit_size': product_data.get('unit_size'),
            'is_active': True
        }
        
        # Remove empty strings
        return {k: v for k, v in transformed.items() if v != ''}
    
    def test_import_simulation(self) -> bool:
        """Simulate the import process step by step"""
        self.print_header("Import Process Simulation")
        
        if not self.supabase:
            self.print_status("Supabase client not initialized", "ERROR")
            return False
        
        simulation_results = {}
        all_good = True
        
        try:
            # Step 1: Test inserting a supermarket
            test_supermarket = {
                'name': f'Debug Test Market {int(time.time())}',
                'slug': f'debug-test-market-{int(time.time())}',
                'is_active': True
            }
            
            try:
                supermarket_result = self.supabase.table('supermarkets').insert(test_supermarket).execute()
                if supermarket_result.data:
                    supermarket_id = supermarket_result.data[0]['id']
                    simulation_results['supermarket_insert'] = {
                        'status': 'success',
                        'id': supermarket_id
                    }
                    self.print_status("Test supermarket insert: OK", "SUCCESS")
                    
                    # Step 2: Test inserting a category
                    test_category = {
                        'name': f'Debug Test Category {int(time.time())}',
                        'slug': f'debug-test-category-{int(time.time())}'
                    }
                    
                    try:
                        category_result = self.supabase.table('categories').insert(test_category).execute()
                        if category_result.data:
                            category_id = category_result.data[0]['id']
                            simulation_results['category_insert'] = {
                                'status': 'success',
                                'id': category_id
                            }
                            self.print_status("Test category insert: OK", "SUCCESS")
                            
                            # Step 3: Test inserting a product
                            test_product = {
                                'name': f'Debug Test Product {int(time.time())}',
                                'normalized_name': f'debug test product {int(time.time())}',
                                'brand': 'Debug Brand',
                                'category_id': category_id,
                                'supermarket_id': supermarket_id,
                                'is_active': True
                            }
                            
                            try:
                                product_result = self.supabase.table('products').insert(test_product).execute()
                                if product_result.data:
                                    product_id = product_result.data[0]['id']
                                    simulation_results['product_insert'] = {
                                        'status': 'success',
                                        'id': product_id
                                    }
                                    self.print_status("Test product insert: OK", "SUCCESS")
                                    
                                    # Step 4: Test inserting a price
                                    test_price = {
                                        'product_id': product_id,
                                        'supermarket_id': supermarket_id,
                                        'price': 9.99,
                                        'price_date': date.today().isoformat(),
                                        'is_available': True
                                    }
                                    
                                    try:
                                        price_result = self.supabase.table('prices').insert(test_price).execute()
                                        if price_result.data:
                                            price_id = price_result.data[0]['id']
                                            simulation_results['price_insert'] = {
                                                'status': 'success',
                                                'id': price_id
                                            }
                                            self.print_status("Test price insert: OK", "SUCCESS")
                                        else:
                                            simulation_results['price_insert'] = {'status': 'failed', 'error': 'No data returned'}
                                            self.print_status("Test price insert: Failed - No data returned", "ERROR")
                                            all_good = False
                                    except Exception as e:
                                        simulation_results['price_insert'] = {'status': 'failed', 'error': str(e)}
                                        self.print_status(f"Test price insert: Failed - {e}", "ERROR")
                                        all_good = False
                                else:
                                    simulation_results['product_insert'] = {'status': 'failed', 'error': 'No data returned'}
                                    self.print_status("Test product insert: Failed - No data returned", "ERROR")
                                    all_good = False
                            except Exception as e:
                                simulation_results['product_insert'] = {'status': 'failed', 'error': str(e)}
                                self.print_status(f"Test product insert: Failed - {e}", "ERROR")
                                all_good = False
                        else:
                            simulation_results['category_insert'] = {'status': 'failed', 'error': 'No data returned'}
                            self.print_status("Test category insert: Failed - No data returned", "ERROR")
                            all_good = False
                    except Exception as e:
                        simulation_results['category_insert'] = {'status': 'failed', 'error': str(e)}
                        self.print_status(f"Test category insert: Failed - {e}", "ERROR")
                        all_good = False
                else:
                    simulation_results['supermarket_insert'] = {'status': 'failed', 'error': 'No data returned'}
                    self.print_status("Test supermarket insert: Failed - No data returned", "ERROR")
                    all_good = False
            except Exception as e:
                simulation_results['supermarket_insert'] = {'status': 'failed', 'error': str(e)}
                self.print_status(f"Test supermarket insert: Failed - {e}", "ERROR")
                all_good = False
            
            # Cleanup test data
            self._cleanup_test_data(simulation_results)
            
        except Exception as e:
            self.print_status(f"Import simulation failed: {e}", "ERROR")
            self.logger.error(f"Import simulation error: {traceback.format_exc()}")
            all_good = False
        
        self.save_debug_data("import_simulation.json", simulation_results)
        return all_good
    
    def _cleanup_test_data(self, simulation_results: Dict):
        """Clean up test data created during simulation"""
        self.print_status("Cleaning up test data...", "INFO")
        
        cleanup_order = ['price_insert', 'product_insert', 'category_insert', 'supermarket_insert']
        cleanup_tables = ['prices', 'products', 'categories', 'supermarkets']
        
        for i, result_key in enumerate(cleanup_order):
            if result_key in simulation_results and 'id' in simulation_results[result_key]:
                test_id = simulation_results[result_key]['id']
                table_name = cleanup_tables[i]
                
                try:
                    self.supabase.table(table_name).delete().eq('id', test_id).execute()
                    self.print_status(f"Cleaned up test {table_name} record", "INFO")
                except Exception as e:
                    self.print_status(f"Failed to cleanup test {table_name} record: {e}", "WARNING")
    
    def generate_debug_report(self) -> Dict:
        """Generate comprehensive debug report"""
        self.print_header("Debug Report Summary")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'debug_session_id': f"debug_{int(time.time())}",
            'environment': {
                'supabase_url_configured': bool(self.supabase_url),
                'supabase_key_configured': bool(self.supabase_key),
                'checkjebon_url': self.checkjebon_url
            },
            'test_results': {},
            'recommendations': [],
            'next_steps': []
        }
        
        # Collect all debug files
        debug_files = list(self.debug_dir.glob("*.json"))
        
        for debug_file in debug_files:
            try:
                with open(debug_file, 'r') as f:
                    data = json.load(f)
                    report['test_results'][debug_file.stem] = data
            except Exception as e:
                self.print_status(f"Could not read debug file {debug_file}: {e}", "WARNING")
        
        # Generate recommendations
        if not report['environment']['supabase_url_configured']:
            report['recommendations'].append("Configure SUPABASE_URL environment variable")
        
        if not report['environment']['supabase_key_configured']:
            report['recommendations'].append("Configure SUPABASE_KEY environment variable")
        
        # Check for common issues
        if 'database_permissions' in report['test_results']:
            perms = report['test_results']['database_permissions']
            if not perms.get('insert', False):
                report['recommendations'].append("Check database INSERT permissions - this is required for imports")
        
        if 'table_schemas' in report['test_results']:
            schemas = report['test_results']['table_schemas']
            empty_tables = [table for table, data in schemas.items() 
                          if isinstance(data, dict) and data.get('row_count', 0) == 0]
            if empty_tables:
                report['recommendations'].append(f"Tables are empty: {empty_tables}. This is expected if no imports have run successfully yet.")
        
        # Generate next steps
        if not report['test_results']:
            report['next_steps'].append("Run the debug script with proper environment variables")
        else:
            if 'import_simulation' in report['test_results']:
                sim_result = report['test_results']['import_simulation']
                if any(result.get('status') == 'success' for result in sim_result.values()):
                    report['next_steps'].append("Database operations work - check the actual import script logic")
                else:
                    report['next_steps'].append("Fix database permission or connection issues before running imports")
        
        self.save_debug_data("debug_report.json", report)
        
        # Print summary
        self.print_status(f"Debug session completed. Report saved to {self.debug_dir}/debug_report.json", "SUCCESS")
        
        if report['recommendations']:
            self.print_status("Recommendations:", "INFO")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        if report['next_steps']:
            self.print_status("Next steps:", "INFO")
            for step in report['next_steps']:
                print(f"  • {step}")
        
        return report
    
    async def run_full_debug(self) -> Dict:
        """Run complete debugging sequence"""
        self.print_header("Supabase Import Debugging Session")
        self.print_status(f"Debug session started at {datetime.now()}", "INFO")
        self.print_status(f"Debug output will be saved to: {self.debug_dir.absolute()}", "INFO")
        
        # Step 1: Environment check
        env_ok = self.check_environment_variables()
        
        # Step 2: Dependencies check
        deps_ok = self.check_dependencies()
        
        # Step 3: Network connectivity
        network_ok = self.test_network_connectivity()
        
        # Step 4: Supabase connection
        supabase_ok = self.test_supabase_connection()
        
        # Step 5: Table schema verification
        schema_ok = False
        if supabase_ok:
            schema_ok = self.verify_table_schemas()
        
        # Step 6: Database permissions
        perms_ok = False
        if supabase_ok:
            perms_ok = self.test_database_permissions()
        
        # Step 7: CheckjeBon API test
        api_ok, api_data = await self.test_checkjebon_api()
        
        # Step 8: Data parsing test
        parsing_ok = False
        if api_data:
            parsing_ok = self.test_data_parsing(api_data)
        
        # Step 9: Import simulation
        import_ok = False
        if supabase_ok and perms_ok:
            import_ok = self.test_import_simulation()
        
        # Step 10: Generate report
        report = self.generate_debug_report()
        
        # Final summary
        self.print_header("Final Summary")
        
        checks = {
            "Environment Variables": env_ok,
            "Dependencies": deps_ok,
            "Network Connectivity": network_ok,
            "Supabase Connection": supabase_ok,
            "Table Schemas": schema_ok,
            "Database Permissions": perms_ok,
            "CheckjeBon API": api_ok,
            "Data Parsing": parsing_ok,
            "Import Simulation": import_ok
        }
        
        for check_name, check_result in checks.items():
            status = "SUCCESS" if check_result else "ERROR"
            self.print_status(f"{check_name}: {'PASS' if check_result else 'FAIL'}", status)
        
        passed_checks = sum(1 for result in checks.values() if result)
        total_checks = len(checks)
        
        self.print_status(f"Overall: {passed_checks}/{total_checks} checks passed", 
                         "SUCCESS" if passed_checks == total_checks else "WARNING")
        
        return report


def create_manual_test_script():
    """Create a manual testing script for users"""
    script_content = '''#!/bin/bash
# Manual Supabase Testing Script
# ===============================

echo "Manual Supabase Database Testing"
echo "================================="

# Check environment variables
echo "1. Checking environment variables..."
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL not set"
else
    echo "✅ SUPABASE_URL: ${SUPABASE_URL:0:30}..."
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo "❌ SUPABASE_KEY not set"
else
    echo "✅ SUPABASE_KEY: ${SUPABASE_KEY:0:20}..."
fi

# Test network connectivity
echo -e "\\n2. Testing network connectivity..."
if curl -s --max-time 10 "$SUPABASE_URL" > /dev/null; then
    echo "✅ Supabase URL is reachable"
else
    echo "❌ Cannot reach Supabase URL"
fi

# Test Python dependencies
echo -e "\\n3. Testing Python dependencies..."
python3 -c "
try:
    from supabase import create_client
    print('✅ Supabase client available')
except ImportError as e:
    print(f'❌ Supabase client not available: {e}')

try:
    import aiohttp
    print('✅ aiohttp available')
except ImportError:
    print('❌ aiohttp not available')

try:
    import pandas
    print('✅ pandas available')
except ImportError:
    print('⚠️ pandas not available (optional)')
"

echo -e "\\nManual testing completed."
echo "Run 'python3 debug_import.py' for comprehensive debugging."
'''
    
    with open('manual_test.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('manual_test.sh', 0o755)
    print("✅ Created manual_test.sh script")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug Supabase import issues')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    parser.add_argument('--create-manual-test', action='store_true',
                       help='Create manual testing script')
    
    args = parser.parse_args()
    
    if args.create_manual_test:
        create_manual_test_script()
        return
    
    # Create debugger and run
    debugger = DatabaseDebugger(log_level=args.log_level)
    
    try:
        report = await debugger.run_full_debug()
        
        print(f"\n🔍 Debug session completed!")
        print(f"📁 Debug files saved to: {debugger.debug_dir.absolute()}")
        print(f"📋 Full report: {debugger.debug_dir.absolute()}/debug_report.json")
        
        return report
        
    except KeyboardInterrupt:
        print("\n🛑 Debug session interrupted by user")
        return None
    except Exception as e:
        print(f"\n💥 Debug session failed: {e}")
        logging.error(f"Debug session error: {traceback.format_exc()}")
        return None


if __name__ == "__main__":
    # Run the debugging session
    report = asyncio.run(main())
    
    if report:
        # Exit with appropriate code
        passed_checks = sum(1 for result in report.get('test_results', {}).values() 
                          if isinstance(result, dict) and result.get('status') in ['success', True])
        total_checks = len(report.get('test_results', {}))
        
        if passed_checks >= total_checks * 0.8:  # 80% pass rate
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(1)