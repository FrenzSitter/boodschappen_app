#!/usr/bin/env python3
"""
CheckjeBon to Supabase Importer
===============================

Automated import script for CheckjeBon data into Supabase database.
Designed for daily automated runs with robust error handling.

Requirements:
- Environment variables: SUPABASE_URL, SUPABASE_KEY
- Python packages: supabase, requests, python-dateutil

Usage:
    python supabase_import.py [--dry-run] [--verbose] [--batch-size=50]

Author: Generated for boodschappen_app
Date: 2025-01-09
"""

import json
import requests
import os
import sys
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import argparse
import re
from collections import defaultdict

# Import Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)

# Configuration
CHECKJEBON_DATA_URL = "https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json"
DEFAULT_BATCH_SIZE = 50
LOG_FILE = "supabase_import.log"

@dataclass
class ImportStats:
    """Statistics tracking for import process"""
    total_downloaded: int = 0
    products_processed: int = 0
    products_inserted: int = 0
    products_updated: int = 0
    products_skipped: int = 0
    supermarkets_processed: int = 0
    categories_created: int = 0
    errors: int = 0
    start_time: datetime = None
    end_time: datetime = None
    
    def duration(self) -> str:
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return f"{delta.total_seconds():.2f}s"
        return "Unknown"

class CheckjeBonImporter:
    """Main importer class for CheckjeBon data"""
    
    def __init__(self, supabase_url: str, supabase_key: str, batch_size: int = DEFAULT_BATCH_SIZE, dry_run: bool = False):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.stats = ImportStats()
        self.logger = self._setup_logging()
        
        # Initialize Supabase client
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.logger.info(f"✅ Connected to Supabase at {supabase_url}")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise
        
        # Cache for lookups
        self.supermarket_cache = {}
        self.category_cache = {}
        self.existing_products = set()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def download_checkjebon_data(self) -> List[Dict]:
        """Download the latest CheckjeBon dataset"""
        self.logger.info("📡 Downloading CheckjeBon dataset...")
        
        try:
            response = requests.get(CHECKJEBON_DATA_URL, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.stats.total_downloaded = len(data)
            self.logger.info(f"✅ Downloaded {len(data)} entries from CheckjeBon")
            
            return data
            
        except requests.RequestException as e:
            self.logger.error(f"❌ Failed to download CheckjeBon data: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse JSON data: {e}")
            raise
    
    def load_caches(self):
        """Load reference data into caches for fast lookups"""
        self.logger.info("🔄 Loading reference data...")
        
        try:
            # Load supermarkets
            response = self.supabase.table('supermarkets').select('*').execute()
            for supermarket in response.data:
                self.supermarket_cache[supermarket['checkjebon_key']] = supermarket
                self.supermarket_cache[supermarket['slug']] = supermarket
            
            # Load categories
            response = self.supabase.table('categories').select('*').execute()
            for category in response.data:
                self.category_cache[category['slug']] = category
                self.category_cache[category['name']] = category
            
            # Load existing products (for duplicate detection)
            response = self.supabase.table('products').select('checkjebon_link').execute()
            self.existing_products = {product['checkjebon_link'] for product in response.data if product['checkjebon_link']}
            
            self.logger.info(f"✅ Loaded {len(self.supermarket_cache)} supermarkets, {len(self.category_cache)} categories, {len(self.existing_products)} existing products")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load caches: {e}")
            raise
    
    def ensure_supermarket_exists(self, checkjebon_key: str) -> Optional[str]:
        """Ensure supermarket exists, create if needed"""
        if checkjebon_key in self.supermarket_cache:
            return self.supermarket_cache[checkjebon_key]['id']
        
        # Create new supermarket
        supermarket_data = {
            'name': checkjebon_key.upper(),
            'slug': checkjebon_key.lower(),
            'checkjebon_key': checkjebon_key,
            'is_active': True,
            'has_online_data': True,
            'last_data_update': datetime.now(timezone.utc).isoformat()
        }
        
        if not self.dry_run:
            try:
                response = self.supabase.table('supermarkets').insert(supermarket_data).execute()
                supermarket_id = response.data[0]['id']
                self.supermarket_cache[checkjebon_key] = response.data[0]
                self.logger.info(f"✅ Created new supermarket: {checkjebon_key}")
                return supermarket_id
            except Exception as e:
                self.logger.error(f"❌ Failed to create supermarket {checkjebon_key}: {e}")
                self.stats.errors += 1
                return None
        else:
            self.logger.info(f"[DRY RUN] Would create supermarket: {checkjebon_key}")
            return "dry-run-id"
    
    def infer_category(self, product_name: str) -> Optional[str]:
        """Infer product category from Dutch product name"""
        name_lower = product_name.lower()
        
        # Category mapping based on Dutch keywords
        category_keywords = {
            'zuivel-eieren': ['melk', 'yoghurt', 'kaas', 'boter', 'ei', 'eieren', 'kwark', 'room', 'vla', 'karnemelk'],
            'brood-gebak': ['brood', 'stokbrood', 'croissant', 'beschuit', 'cake', 'koek', 'taart', 'gebak'],
            'groente-fruit': ['appel', 'banaan', 'tomaat', 'ui', 'wortel', 'sla', 'komkommer', 'paprika', 'fruit', 'groente', 'aardappel'],
            'vlees-vis-vegetarisch': ['vlees', 'kip', 'vis', 'gehakt', 'worst', 'ham', 'vegetarisch', 'vegan', 'zalm', 'kalkoen'],
            'dranken': ['cola', 'sap', 'water', 'bier', 'koffie', 'thee', 'wijn', 'frisdrank', 'spa', 'limonade'],
            'diepvries': ['diepvries', 'frozen', 'ijs', 'ijsje', 'bevroren'],
            'houdbaar': ['pasta', 'rijst', 'meel', 'suiker', 'conserven', 'blik', 'pot', 'sauce'],
            'snacks-snoep': ['chips', 'koekjes', 'chocolade', 'snoep', 'noten', 'reep', 'drop'],
            'verzorging': ['shampoo', 'tandpasta', 'zeep', 'deodorant', 'parfum', 'creme', 'gel', 'lotion'],
            'huishouden': ['wasmiddel', 'afwasmiddel', 'toiletpapier', 'keukenrol', 'schoonmaak', 'was', 'allesreiniger'],
            'baby-kind': ['baby', 'luier', 'flesvoeding', 'kindje', 'pampers'],
            'dieren': ['hond', 'kat', 'voer', 'dier', 'brokken']
        }
        
        for category_slug, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                if category_slug in self.category_cache:
                    return self.category_cache[category_slug]['id']
        
        # Default to 'Houdbaar' if no category found
        return self.category_cache.get('houdbaar', {}).get('id')
    
    def extract_brand(self, product_name: str) -> Optional[str]:
        """Extract brand from Dutch product name"""
        name_lower = product_name.lower()
        
        # Common Dutch brands
        brands = [
            'ah', 'albert heijn', 'campina', 'douwe egberts', 'coca cola', 'coca-cola',
            'heineken', 'unilever', 'nestlé', 'nestle', 'danone', 'friesche vlag',
            'verkade', 'liga', 'calvé', 'calve', 'knorr', 'maggi', 'hero',
            'jumbo', 'plus', 'etos', 'hema', 'bavaria', 'grolsch', 'amstel',
            'ben & jerry', 'magnum', 'cornetto', 'lipton', 'pickwick'
        ]
        
        for brand in brands:
            if brand in name_lower:
                return brand.title()
        
        # Try to extract first word as potential brand
        first_word = product_name.split()[0] if product_name.split() else None
        if first_word and len(first_word) > 2 and first_word.isalpha():
            return first_word.title()
        
        return None
    
    def parse_size_info(self, size_text: str) -> Tuple[Optional[float], Optional[str]]:
        """Parse size information from Dutch size text"""
        if not size_text:
            return None, None
        
        # Common patterns in Dutch size descriptions
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(ml|l|liter|gram|g|kg|kilogram|stuks?|st)',
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|l|gram|g|kg)',
            r'(\d+(?:\.\d+)?)\s*(ml|l|gram|g|kg)'
        ]
        
        size_text_lower = size_text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, size_text_lower)
            if match:
                if len(match.groups()) == 2:
                    size, unit = match.groups()
                    return float(size), unit.lower()
                elif len(match.groups()) == 3:
                    # Handle "5 x 250ml" format
                    count, size, unit = match.groups()
                    return float(count) * float(size), unit.lower()
        
        return None, None
    
    def normalize_product_name(self, name: str) -> str:
        """Normalize product name for search and comparison"""
        if not name:
            return ""
        
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()
    
    def create_product_record(self, product_data: Dict, supermarket_id: str) -> Dict:
        """Create a product record for database insertion"""
        name = product_data.get('n', '').strip()
        checkjebon_link = product_data.get('l', '').strip()
        price = product_data.get('p', 0)
        size_text = product_data.get('s', '').strip()
        
        # Parse size information
        package_size, package_unit = self.parse_size_info(size_text)
        
        # Infer category and brand
        category_id = self.infer_category(name)
        brand = self.extract_brand(name)
        
        # Calculate price per unit if possible
        price_per_unit = None
        if price and package_size and package_size > 0:
            if package_unit in ['kg', 'kilogram']:
                price_per_unit = price / package_size
            elif package_unit in ['l', 'liter']:
                price_per_unit = price / package_size
            elif package_unit in ['g', 'gram']:
                price_per_unit = price / (package_size / 1000)  # Convert to per kg
            elif package_unit in ['ml']:
                price_per_unit = price / (package_size / 1000)  # Convert to per liter
        
        # Create product record
        product_record = {
            'name': name,
            'normalized_name': self.normalize_product_name(name),
            'brand': brand,
            'checkjebon_link': checkjebon_link,
            'source_supermarket_id': supermarket_id,
            'category_id': category_id,
            'auto_category': self.infer_category(name),
            'size_text': size_text,
            'package_size': package_size,
            'package_unit': package_unit,
            'brand_extracted': brand,
            'is_active': True,
            'quality_score': 100,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create price record
        price_record = {
            'price': float(price) if price else 0.0,
            'price_per_unit': price_per_unit,
            'currency': 'EUR',
            'is_available': True,
            'is_on_sale': False,
            'data_source': 'checkjebon',
            'confidence_score': 100,
            'checkjebon_link': checkjebon_link,
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        return {'product': product_record, 'price': price_record}
    
    def process_batch(self, batch_data: List[Dict]) -> None:
        """Process a batch of products"""
        products_to_insert = []
        prices_to_insert = []
        
        for entry in batch_data:
            supermarket_key = entry.get('n', 'unknown')
            variants = entry.get('d', [])
            
            if not variants:
                continue
            
            # Ensure supermarket exists
            supermarket_id = self.ensure_supermarket_exists(supermarket_key)
            if not supermarket_id:
                continue
            
            # Process each variant
            for variant in variants:
                checkjebon_link = variant.get('l', '')
                
                # Skip if already exists (unless updating)
                if checkjebon_link in self.existing_products:
                    self.stats.products_skipped += 1
                    continue
                
                # Create product record
                try:
                    record = self.create_product_record(variant, supermarket_id)
                    products_to_insert.append(record['product'])
                    
                    # We'll add price after product insertion
                    prices_to_insert.append({
                        'price_data': record['price'],
                        'checkjebon_link': checkjebon_link
                    })
                    
                    self.stats.products_processed += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing product {variant.get('n', 'unknown')}: {e}")
                    self.stats.errors += 1
        
        # Insert products
        if products_to_insert and not self.dry_run:
            try:
                self.logger.info(f"📥 Inserting {len(products_to_insert)} products...")
                
                # Use upsert for handling duplicates
                response = self.supabase.table('products').upsert(
                    products_to_insert,
                    on_conflict='checkjebon_link'
                ).execute()
                
                inserted_products = response.data
                self.stats.products_inserted += len(inserted_products)
                
                # Create product ID mapping for prices
                product_id_map = {}
                for product in inserted_products:
                    product_id_map[product['checkjebon_link']] = product['id']
                
                # Insert prices
                prices_to_insert_final = []
                for price_info in prices_to_insert:
                    checkjebon_link = price_info['checkjebon_link']
                    if checkjebon_link in product_id_map:
                        price_data = price_info['price_data']
                        price_data['product_id'] = product_id_map[checkjebon_link]
                        price_data['supermarket_id'] = supermarket_id
                        prices_to_insert_final.append(price_data)
                
                if prices_to_insert_final:
                    self.logger.info(f"💰 Inserting {len(prices_to_insert_final)} prices...")
                    self.supabase.table('product_prices').upsert(
                        prices_to_insert_final,
                        on_conflict='product_id,supermarket_id'
                    ).execute()
                
                self.logger.info(f"✅ Batch processed: {len(products_to_insert)} products, {len(prices_to_insert_final)} prices")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to insert batch: {e}")
                self.stats.errors += 1
        
        elif products_to_insert and self.dry_run:
            self.logger.info(f"[DRY RUN] Would insert {len(products_to_insert)} products")
    
    def run_import(self) -> ImportStats:
        """Run the complete import process"""
        self.stats.start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 Starting CheckjeBon import process...")
        
        try:
            # Download data
            data = self.download_checkjebon_data()
            
            # Load caches
            self.load_caches()
            
            # Process data in batches
            total_batches = (len(data) + self.batch_size - 1) // self.batch_size
            
            for i in range(0, len(data), self.batch_size):
                batch_num = (i // self.batch_size) + 1
                batch_data = data[i:i + self.batch_size]
                
                self.logger.info(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch_data)} entries)")
                self.process_batch(batch_data)
                
                # Small delay to prevent overwhelming the database
                if not self.dry_run:
                    time.sleep(0.1)
            
            self.stats.end_time = datetime.now(timezone.utc)
            self.logger.info(f"✅ Import process completed in {self.stats.duration()}")
            
        except Exception as e:
            self.logger.error(f"❌ Import process failed: {e}")
            self.stats.errors += 1
            raise
        
        return self.stats
    
    def print_summary(self):
        """Print import summary"""
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        print(f"Total downloaded entries: {self.stats.total_downloaded:,}")
        print(f"Products processed: {self.stats.products_processed:,}")
        print(f"Products inserted: {self.stats.products_inserted:,}")
        print(f"Products updated: {self.stats.products_updated:,}")
        print(f"Products skipped: {self.stats.products_skipped:,}")
        print(f"Errors encountered: {self.stats.errors:,}")
        print(f"Duration: {self.stats.duration()}")
        print(f"Processing rate: {self.stats.products_processed / max(1, float(self.stats.duration().replace('s', ''))):.2f} products/second")
        
        if self.stats.errors > 0:
            print(f"\n⚠️  {self.stats.errors} errors occurred. Check {LOG_FILE} for details.")
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No actual database changes made")
        
        print("\n✅ Import process completed!")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Import CheckjeBon data to Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Run without making database changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        print("Export them like this:")
        print("export SUPABASE_URL='your_supabase_url'")
        print("export SUPABASE_KEY='your_supabase_key'")
        sys.exit(1)
    
    # Adjust logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize importer
        importer = CheckjeBonImporter(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        
        # Run import
        stats = importer.run_import()
        
        # Print summary
        importer.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if stats.errors == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()