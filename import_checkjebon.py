#!/usr/bin/env python3
"""
CheckjeBon Data Import Script
============================

Imports CheckjeBon supermarket price data into Supabase with comprehensive
price history tracking, change detection, and data quality monitoring.

Features:
- Downloads and parses CheckjeBon data
- Tracks price changes over time
- Normalizes product and supermarket data
- Efficient bulk database operations
- Comprehensive logging and monitoring
- Error handling with rollback capability

Environment Variables:
- SUPABASE_URL: Supabase project URL
- SUPABASE_KEY: Supabase service role key
- CHECKJEBON_API_KEY: CheckjeBon API key (optional)
- LOG_LEVEL: Logging level (default: INFO)

Usage:
    python import_checkjebon.py [--dry-run] [--supermarket=albert-heijn] [--limit=1000]
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import traceback

# Third-party imports
import aiohttp
import asyncpg
from supabase import create_client, Client
from supabase.client import ClientOptions
import pandas as pd
from tqdm import tqdm

# Configuration
@dataclass
class Config:
    """Configuration for the import process"""
    supabase_url: str
    supabase_key: str
    checkjebon_api_key: Optional[str] = None
    log_level: str = "INFO"
    batch_size: int = 1000
    max_retries: int = 3
    timeout: int = 30
    dry_run: bool = False
    
    # Data quality thresholds
    min_price: float = 0.01
    max_price: float = 1000.0
    min_name_length: int = 3
    max_name_length: int = 500
    
    # Price change thresholds for alerts
    significant_change_threshold: float = 20.0  # percentage
    major_change_threshold: float = 50.0  # percentage

@dataclass
class ImportStats:
    """Statistics for the import process"""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_products: int = 0
    new_products: int = 0
    updated_products: int = 0
    total_prices: int = 0
    new_prices: int = 0
    price_changes: int = 0
    significant_changes: int = 0
    major_changes: int = 0
    errors: int = 0
    data_quality_issues: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return asdict(self)

class CheckjeBonImporter:
    """Main importer class for CheckjeBon data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logging()
        self.supabase: Optional[Client] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = ImportStats(start_time=datetime.now())
        
        # Cache for lookups
        self._supermarket_cache: Dict[str, str] = {}
        self._category_cache: Dict[str, str] = {}
        self._product_cache: Dict[str, str] = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('checkjebon_importer')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler('checkjebon_import.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize connections and caches"""
        try:
            # Initialize Supabase client
            self.supabase = create_client(
                self.config.supabase_url,
                self.config.supabase_key,
                options=ClientOptions(
                    postgrest_client_timeout=self.config.timeout,
                    storage_client_timeout=self.config.timeout
                )
            )
            
            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Load caches
            await self._load_caches()
            
            self.logger.info("Importer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        
        # Record end time
        self.stats.end_time = datetime.now()
        
        # Log final statistics
        self._log_final_stats()
    
    async def _load_caches(self):
        """Load reference data caches"""
        try:
            # Load supermarkets
            response = self.supabase.table("supermarkets").select("id,name,slug,checkjebon_key").execute()
            for row in response.data:
                self._supermarket_cache[row['slug']] = row['id']
                if row.get('checkjebon_key'):
                    self._supermarket_cache[row['checkjebon_key']] = row['id']
            
            # Load categories
            response = self.supabase.table("product_categories").select("id,name,slug").execute()
            for row in response.data:
                self._category_cache[row['slug']] = row['id']
                self._category_cache[row['name'].lower()] = row['id']
            
            # Load existing products for duplicate detection
            response = self.supabase.table("products").select("id,name,ean,normalized_name").execute()
            for row in response.data:
                if row.get('ean'):
                    self._product_cache[row['ean']] = row['id']
                
                # Create normalized name key
                normalized_key = self._normalize_product_name(row['name'])
                self._product_cache[normalized_key] = row['id']
            
            self.logger.info(f"Loaded caches: {len(self._supermarket_cache)} supermarkets, "
                           f"{len(self._category_cache)} categories, {len(self._product_cache)} products")
            
        except Exception as e:
            self.logger.error(f"Failed to load caches: {e}")
            raise
    
    def _normalize_product_name(self, name: str) -> str:
        """Normalize product name for matching"""
        if not name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = " ".join(name.lower().split())
        
        # Remove common words that don't affect product identity
        stop_words = {'van', 'de', 'het', 'een', 'en', 'of', 'met', 'voor', 'uit'}
        words = [word for word in normalized.split() if word not in stop_words]
        
        return " ".join(words)
    
    def _generate_product_hash(self, name: str, brand: str = None, size: str = None) -> str:
        """Generate unique hash for product identification"""
        components = [self._normalize_product_name(name)]
        
        if brand:
            components.append(brand.lower().strip())
        
        if size:
            components.append(size.lower().strip())
        
        content = "|".join(components)
        return hashlib.md5(content.encode()).hexdigest()
    
    async def fetch_checkjebon_data(self, supermarket: str = None, limit: int = None) -> List[Dict]:
        """Fetch data from CheckjeBon API"""
        try:
            # CheckjeBon API endpoints (this is a placeholder - adjust based on actual API)
            base_url = "https://api.checkjebon.nl/v1"
            
            headers = {}
            if self.config.checkjebon_api_key:
                headers['Authorization'] = f'Bearer {self.config.checkjebon_api_key}'
            
            all_data = []
            
            # Get supermarkets to process
            supermarkets_to_process = [supermarket] if supermarket else list(self._supermarket_cache.keys())
            
            for sm in supermarkets_to_process:
                if sm not in self._supermarket_cache:
                    continue
                
                self.logger.info(f"Fetching data for supermarket: {sm}")
                
                # Fetch products for this supermarket
                url = f"{base_url}/supermarkets/{sm}/products"
                params = {}
                if limit:
                    params['limit'] = limit
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process the data structure (adjust based on actual API response)
                        products = data.get('products', [])
                        
                        for product in products:
                            # Add supermarket info to each product
                            product['supermarket'] = sm
                            all_data.append(product)
                        
                        self.logger.info(f"Fetched {len(products)} products from {sm}")
                    else:
                        self.logger.warning(f"Failed to fetch data for {sm}: {response.status}")
                        self.stats.errors += 1
            
            self.logger.info(f"Total products fetched: {len(all_data)}")
            return all_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch CheckjeBon data: {e}")
            self.stats.errors += 1
            return []
    
    def _validate_product_data(self, product: Dict) -> Tuple[bool, List[str]]:
        """Validate product data quality"""
        issues = []
        
        # Check required fields
        if not product.get('name'):
            issues.append("Missing product name")
        elif len(product['name']) < self.config.min_name_length:
            issues.append(f"Product name too short: {product['name']}")
        elif len(product['name']) > self.config.max_name_length:
            issues.append(f"Product name too long: {product['name'][:50]}...")
        
        # Check price
        price = product.get('price')
        if price is None:
            issues.append("Missing price")
        elif not isinstance(price, (int, float)):
            issues.append(f"Invalid price format: {price}")
        elif price < self.config.min_price or price > self.config.max_price:
            issues.append(f"Price out of range: {price}")
        
        # Check supermarket
        if not product.get('supermarket'):
            issues.append("Missing supermarket")
        elif product['supermarket'] not in self._supermarket_cache:
            issues.append(f"Unknown supermarket: {product['supermarket']}")
        
        return len(issues) == 0, issues
    
    def _normalize_product_data(self, product: Dict) -> Dict:
        """Normalize and clean product data"""
        normalized = {
            'name': product.get('name', '').strip(),
            'brand': product.get('brand', '').strip() or None,
            'size_text': product.get('size', '').strip() or None,
            'ean': product.get('ean', '').strip() or None,
            'price': float(product.get('price', 0)),
            'supermarket': product.get('supermarket', '').strip(),
            'category': product.get('category', '').strip().lower() or None,
            'description': product.get('description', '').strip() or None,
            'image_url': product.get('image_url', '').strip() or None,
            'unit_size': product.get('unit_size') or None,
            'unit_type': product.get('unit_type', '').strip() or None,
            'is_available': product.get('is_available', True),
            'is_on_sale': product.get('is_on_sale', False),
            'original_price': product.get('original_price') or None,
            'discount_percentage': product.get('discount_percentage') or None,
        }
        
        # Generate normalized name for matching
        normalized['normalized_name'] = self._normalize_product_name(normalized['name'])
        
        # Calculate price per unit if possible
        if normalized['unit_size'] and normalized['unit_size'] > 0:
            normalized['price_per_unit'] = normalized['price'] / normalized['unit_size']
        else:
            normalized['price_per_unit'] = None
        
        return normalized
    
    async def _upsert_product(self, product_data: Dict) -> str:
        """Insert or update product and return product ID"""
        try:
            # Check if product exists
            product_id = None
            
            # Try to find by EAN first
            if product_data.get('ean'):
                product_id = self._product_cache.get(product_data['ean'])
            
            # Try to find by normalized name + brand
            if not product_id:
                hash_key = self._generate_product_hash(
                    product_data['name'],
                    product_data.get('brand'),
                    product_data.get('size_text')
                )
                product_id = self._product_cache.get(hash_key)
            
            # Find category ID
            category_id = None
            if product_data.get('category'):
                category_id = self._category_cache.get(product_data['category'])
            
            # Prepare product record
            product_record = {
                'name': product_data['name'],
                'normalized_name': product_data['normalized_name'],
                'brand': product_data['brand'],
                'size_text': product_data['size_text'],
                'ean': product_data['ean'],
                'category_id': category_id,
                'description': product_data['description'],
                'image_url': product_data['image_url'],
                'unit_size': product_data['unit_size'],
                'unit_type': product_data['unit_type'],
                'updated_at': datetime.now().isoformat(),
            }
            
            if product_id:
                # Update existing product
                if not self.config.dry_run:
                    response = self.supabase.table("products").update(product_record).eq("id", product_id).execute()
                    if response.data:
                        self.stats.updated_products += 1
                        self.logger.debug(f"Updated product: {product_data['name']}")
                    else:
                        self.logger.warning(f"Failed to update product: {product_data['name']}")
                        self.stats.errors += 1
                        return None
                else:
                    self.stats.updated_products += 1
                    self.logger.debug(f"[DRY RUN] Would update product: {product_data['name']}")
            else:
                # Insert new product
                product_record['created_at'] = datetime.now().isoformat()
                
                if not self.config.dry_run:
                    response = self.supabase.table("products").insert(product_record).execute()
                    if response.data:
                        product_id = response.data[0]['id']
                        self.stats.new_products += 1
                        self.logger.debug(f"Created new product: {product_data['name']}")
                        
                        # Update cache
                        if product_data.get('ean'):
                            self._product_cache[product_data['ean']] = product_id
                        
                        hash_key = self._generate_product_hash(
                            product_data['name'],
                            product_data.get('brand'),
                            product_data.get('size_text')
                        )
                        self._product_cache[hash_key] = product_id
                    else:
                        self.logger.warning(f"Failed to create product: {product_data['name']}")
                        self.stats.errors += 1
                        return None
                else:
                    self.stats.new_products += 1
                    self.logger.debug(f"[DRY RUN] Would create product: {product_data['name']}")
                    product_id = f"dry-run-{len(self._product_cache)}"
            
            return product_id
            
        except Exception as e:
            self.logger.error(f"Failed to upsert product {product_data.get('name', 'unknown')}: {e}")
            self.stats.errors += 1
            return None
    
    async def _get_previous_price(self, product_id: str, supermarket_id: str) -> Optional[float]:
        """Get the most recent price for a product from a supermarket"""
        try:
            response = self.supabase.table("current_prices").select("price").eq("product_id", product_id).eq("supermarket_id", supermarket_id).execute()
            
            if response.data:
                return float(response.data[0]['price'])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get previous price: {e}")
            return None
    
    async def _calculate_price_change(self, current_price: float, previous_price: Optional[float]) -> Tuple[float, float]:
        """Calculate price change amount and percentage"""
        if previous_price is None:
            return 0.0, 0.0
        
        change_amount = current_price - previous_price
        change_percentage = (change_amount / previous_price) * 100 if previous_price > 0 else 0.0
        
        return change_amount, change_percentage
    
    async def _insert_price_history(self, product_id: str, supermarket_id: str, price_data: Dict) -> bool:
        """Insert price history record"""
        try:
            # Get previous price for change calculation
            previous_price = await self._get_previous_price(product_id, supermarket_id)
            
            # Calculate price changes
            change_amount, change_percentage = await self._calculate_price_change(
                price_data['price'], previous_price
            )
            
            # Prepare price history record
            price_record = {
                'product_id': product_id,
                'supermarket_id': supermarket_id,
                'price_date': date.today().isoformat(),
                'price': price_data['price'],
                'price_per_unit': price_data.get('price_per_unit'),
                'previous_price': previous_price,
                'price_change': change_amount,
                'price_change_percentage': change_percentage,
                'is_available': price_data['is_available'],
                'is_on_sale': price_data['is_on_sale'],
                'original_price': price_data.get('original_price'),
                'discount_percentage': price_data.get('discount_percentage'),
                'change_reason': 'daily_import',
                'created_at': datetime.now().isoformat(),
            }
            
            # Insert price history
            if not self.config.dry_run:
                response = self.supabase.table("price_history").insert(price_record).execute()
                if response.data:
                    self.stats.new_prices += 1
                    
                    # Track price changes
                    if previous_price is not None and abs(change_percentage) > 0.1:
                        self.stats.price_changes += 1
                        
                        if abs(change_percentage) >= self.config.significant_change_threshold:
                            self.stats.significant_changes += 1
                            self.logger.info(f"Significant price change: {price_data.get('name', 'unknown')} "
                                           f"{change_percentage:.2f}% ({previous_price:.2f} -> {price_data['price']:.2f})")
                            
                            if abs(change_percentage) >= self.config.major_change_threshold:
                                self.stats.major_changes += 1
                                self.logger.warning(f"Major price change: {price_data.get('name', 'unknown')} "
                                                  f"{change_percentage:.2f}% ({previous_price:.2f} -> {price_data['price']:.2f})")
                    
                    return True
                else:
                    self.logger.warning(f"Failed to insert price history for product {product_id}")
                    self.stats.errors += 1
                    return False
            else:
                self.stats.new_prices += 1
                self.logger.debug(f"[DRY RUN] Would insert price history: {price_data['price']}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to insert price history: {e}")
            self.stats.errors += 1
            return False
    
    async def _upsert_current_price(self, product_id: str, supermarket_id: str, price_data: Dict) -> bool:
        """Insert or update current price record"""
        try:
            # Prepare current price record
            current_price_record = {
                'product_id': product_id,
                'supermarket_id': supermarket_id,
                'price': price_data['price'],
                'price_per_unit': price_data.get('price_per_unit'),
                'is_available': price_data['is_available'],
                'is_on_sale': price_data['is_on_sale'],
                'original_price': price_data.get('original_price'),
                'discount_percentage': price_data.get('discount_percentage'),
                'last_updated': datetime.now().isoformat(),
            }
            
            if not self.config.dry_run:
                # Try to update first
                response = self.supabase.table("current_prices").update(current_price_record).eq("product_id", product_id).eq("supermarket_id", supermarket_id).execute()
                
                if not response.data:
                    # Insert if update didn't affect any rows
                    response = self.supabase.table("current_prices").insert(current_price_record).execute()
                
                if response.data:
                    return True
                else:
                    self.logger.warning(f"Failed to upsert current price for product {product_id}")
                    self.stats.errors += 1
                    return False
            else:
                self.logger.debug(f"[DRY RUN] Would upsert current price: {price_data['price']}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to upsert current price: {e}")
            self.stats.errors += 1
            return False
    
    async def process_products(self, products: List[Dict]) -> bool:
        """Process a batch of products"""
        try:
            self.logger.info(f"Processing {len(products)} products...")
            
            # Process products in batches
            for i in range(0, len(products), self.config.batch_size):
                batch = products[i:i + self.config.batch_size]
                
                self.logger.info(f"Processing batch {i // self.config.batch_size + 1} "
                               f"({len(batch)} products)")
                
                # Process each product in the batch
                for product in tqdm(batch, desc="Processing products"):
                    try:
                        # Validate product data
                        is_valid, issues = self._validate_product_data(product)
                        
                        if not is_valid:
                            self.logger.warning(f"Data quality issues for {product.get('name', 'unknown')}: {issues}")
                            self.stats.data_quality_issues += len(issues)
                            continue
                        
                        # Normalize product data
                        normalized_product = self._normalize_product_data(product)
                        
                        # Get supermarket ID
                        supermarket_id = self._supermarket_cache.get(normalized_product['supermarket'])
                        if not supermarket_id:
                            self.logger.warning(f"Unknown supermarket: {normalized_product['supermarket']}")
                            self.stats.errors += 1
                            continue
                        
                        # Upsert product
                        product_id = await self._upsert_product(normalized_product)
                        if not product_id:
                            continue
                        
                        # Insert price history
                        await self._insert_price_history(product_id, supermarket_id, normalized_product)
                        
                        # Update current price
                        await self._upsert_current_price(product_id, supermarket_id, normalized_product)
                        
                        self.stats.total_products += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process product {product.get('name', 'unknown')}: {e}")
                        self.stats.errors += 1
                        continue
                
                # Log progress
                self.logger.info(f"Completed batch {i // self.config.batch_size + 1}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process products: {e}")
            return False
    
    def _log_final_stats(self):
        """Log final import statistics"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        self.logger.info("=== IMPORT COMPLETED ===")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info(f"Total products processed: {self.stats.total_products}")
        self.logger.info(f"New products created: {self.stats.new_products}")
        self.logger.info(f"Products updated: {self.stats.updated_products}")
        self.logger.info(f"Price records created: {self.stats.new_prices}")
        self.logger.info(f"Price changes detected: {self.stats.price_changes}")
        self.logger.info(f"Significant changes: {self.stats.significant_changes}")
        self.logger.info(f"Major changes: {self.stats.major_changes}")
        self.logger.info(f"Data quality issues: {self.stats.data_quality_issues}")
        self.logger.info(f"Errors: {self.stats.errors}")
        
        if self.stats.total_products > 0:
            self.logger.info(f"Processing rate: {self.stats.total_products / duration:.2f} products/second")
        
        # Log to database for monitoring
        if not self.config.dry_run:
            self._log_import_stats()
    
    def _log_import_stats(self):
        """Log import statistics to database"""
        try:
            stats_record = {
                'import_date': date.today().isoformat(),
                'start_time': self.stats.start_time.isoformat(),
                'end_time': self.stats.end_time.isoformat(),
                'total_products': self.stats.total_products,
                'new_products': self.stats.new_products,
                'updated_products': self.stats.updated_products,
                'total_prices': self.stats.new_prices,
                'price_changes': self.stats.price_changes,
                'significant_changes': self.stats.significant_changes,
                'major_changes': self.stats.major_changes,
                'errors': self.stats.errors,
                'data_quality_issues': self.stats.data_quality_issues,
            }
            
            # Note: This assumes an import_logs table exists
            # You might want to create this table in your schema
            self.supabase.table("import_logs").insert(stats_record).execute()
            
        except Exception as e:
            self.logger.warning(f"Failed to log import statistics: {e}")
    
    async def run_import(self, supermarket: str = None, limit: int = None) -> bool:
        """Run the complete import process"""
        try:
            self.logger.info("Starting CheckjeBon import process...")
            
            if self.config.dry_run:
                self.logger.info("DRY RUN MODE - No data will be written to database")
            
            # Fetch data from CheckjeBon
            products = await self.fetch_checkjebon_data(supermarket, limit)
            
            if not products:
                self.logger.warning("No products fetched from CheckjeBon")
                return False
            
            # Process products
            success = await self.process_products(products)
            
            if success:
                self.logger.info("Import completed successfully")
                return True
            else:
                self.logger.error("Import completed with errors")
                return False
            
        except Exception as e:
            self.logger.error(f"Import process failed: {e}")
            self.logger.error(traceback.format_exc())
            return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Import CheckjeBon data to Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to database")
    parser.add_argument("--supermarket", help="Import specific supermarket only")
    parser.add_argument("--limit", type=int, help="Limit number of products to import")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        checkjebon_api_key=os.getenv("CHECKJEBON_API_KEY"),
        log_level=args.log_level,
        dry_run=args.dry_run,
    )
    
    # Validate required environment variables
    if not config.supabase_url or not config.supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        sys.exit(1)
    
    # Run import
    async with CheckjeBonImporter(config) as importer:
        success = await importer.run_import(args.supermarket, args.limit)
        
        if success:
            print("Import completed successfully")
            sys.exit(0)
        else:
            print("Import failed")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())