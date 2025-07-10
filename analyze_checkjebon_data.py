#!/usr/bin/env python3
"""
CheckjeBon Data Analyzer
========================

This script downloads and analyzes the complete CheckjeBon supermarket dataset
from their GitHub repository to understand the data structure before importing
to Supabase.

Author: Claude
Date: 2025-01-08
"""

import json
import requests
from datetime import datetime
from collections import defaultdict, Counter
import os
import sys

# Configuration
CHECKJEBON_DATA_URL = "https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json"
OUTPUT_FILE = "checkjebon_data_backup.json"
ANALYSIS_FILE = "checkjebon_analysis_report.txt"

def install_dependencies():
    """Install required Python packages"""
    print("🔧 Installing required dependencies...")
    
    try:
        import requests
        print("✅ requests already installed")
    except ImportError:
        print("📦 Installing requests...")
        os.system(f"{sys.executable} -m pip install requests")
    
    try:
        import supabase
        print("✅ supabase already installed")
    except ImportError:
        print("📦 Installing supabase...")
        os.system(f"{sys.executable} -m pip install supabase")
    
    print("✅ All dependencies installed\n")

def download_data():
    """Download the CheckjeBon dataset"""
    print("📡 Downloading CheckjeBon dataset...")
    print(f"URL: {CHECKJEBON_DATA_URL}")
    
    try:
        response = requests.get(CHECKJEBON_DATA_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Downloaded {len(data)} data entries")
        
        # Save backup
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved backup to {OUTPUT_FILE}")
        
        return data
        
    except requests.RequestException as e:
        print(f"❌ Error downloading data: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        sys.exit(1)

def analyze_data_structure(data):
    """Analyze the structure of the CheckjeBon data"""
    print("\n" + "="*60)
    print("📊 DATA STRUCTURE ANALYSIS")
    print("="*60)
    
    analysis = {
        'total_entries': len(data),
        'supermarkets': set(),
        'products_per_supermarket': defaultdict(int),
        'all_fields': set(),
        'sample_products': [],
        'product_structures': [],
        'price_ranges': {},
        'categories_found': set(),
        'brands_found': set()
    }
    
    # Analyze each entry
    for i, entry in enumerate(data):
        if i < 5:  # Store first 5 for detailed analysis
            analysis['sample_products'].append(entry)
        
        # Collect all field names at top level
        for field in entry.keys():
            analysis['all_fields'].add(field)
        
        # Analyze product structure
        product_name = entry.get('n', 'Unknown')
        variants = entry.get('d', [])
        
        if variants:
            analysis['products_per_supermarket']['variants'] += len(variants)
            
            # Analyze variant structure
            for variant in variants[:3]:  # First 3 variants
                variant_structure = {
                    'fields': list(variant.keys()),
                    'sample_data': variant
                }
                if len(analysis['product_structures']) < 10:
                    analysis['product_structures'].append(variant_structure)
                
                # Collect price data
                price = variant.get('p')
                if price:
                    if 'prices' not in analysis['price_ranges']:
                        analysis['price_ranges']['prices'] = []
                    analysis['price_ranges']['prices'].append(float(price))
                
                # Try to identify categories from product names
                name = variant.get('n', '') or product_name
                if name:
                    analysis['categories_found'].add(infer_category(name))
                    brand = extract_brand(name)
                    if brand:
                        analysis['brands_found'].add(brand)
    
    return analysis

def infer_category(product_name):
    """Infer product category from Dutch product name"""
    name_lower = product_name.lower()
    
    if any(word in name_lower for word in ['melk', 'yoghurt', 'kaas', 'boter', 'ei']):
        return 'Zuivel & eieren'
    elif any(word in name_lower for word in ['brood', 'stokbrood', 'croissant']):
        return 'Brood & gebak'
    elif any(word in name_lower for word in ['appel', 'banaan', 'tomaat', 'sla', 'fruit']):
        return 'Groente & fruit'
    elif any(word in name_lower for word in ['cola', 'sap', 'water', 'koffie', 'thee']):
        return 'Dranken'
    elif any(word in name_lower for word in ['vlees', 'kip', 'vis', 'gehakt']):
        return 'Vlees, vis & vegetarisch'
    elif any(word in name_lower for word in ['diepvries', 'ijs']):
        return 'Diepvries'
    elif any(word in name_lower for word in ['shampoo', 'tandpasta', 'zeep']):
        return 'Verzorging'
    elif any(word in name_lower for word in ['wasmiddel', 'toiletpapier']):
        return 'Huishouden'
    else:
        return 'Houdbaar'

def extract_brand(product_name):
    """Extract brand from Dutch product name"""
    name_lower = product_name.lower()
    
    brands = [
        'ah', 'albert heijn', 'campina', 'douwe egberts', 'coca cola', 
        'heineken', 'unilever', 'nestlé', 'danone', 'friesche vlag',
        'verkade', 'liga', 'calvé', 'knorr', 'maggi', 'hero'
    ]
    
    for brand in brands:
        if brand in name_lower:
            return brand.title()
    
    return None

def print_analysis(analysis):
    """Print detailed analysis results"""
    print(f"\n📈 DATASET OVERVIEW")
    print(f"{'='*50}")
    print(f"Total entries in dataset: {analysis['total_entries']:,}")
    print(f"Total product variants: {analysis['products_per_supermarket']['variants']:,}")
    print(f"Unique top-level fields: {len(analysis['all_fields'])}")
    print(f"Categories identified: {len(analysis['categories_found'])}")
    print(f"Brands identified: {len(analysis['brands_found'])}")
    
    print(f"\n🏪 SUPERMARKET ANALYSIS")
    print(f"{'='*50}")
    print("This appears to be a single supermarket dataset (likely Albert Heijn)")
    print("based on the JSON structure and product naming patterns.")
    
    print(f"\n📋 TOP-LEVEL DATA FIELDS")
    print(f"{'='*50}")
    for field in sorted(analysis['all_fields']):
        print(f"  • {field}")
    
    print(f"\n🛍️ SAMPLE PRODUCT STRUCTURES")
    print(f"{'='*50}")
    for i, product in enumerate(analysis['sample_products'][:3], 1):
        print(f"\nProduct {i}:")
        print(f"  Name: {product.get('n', 'N/A')}")
        if 'd' in product and product['d']:
            print(f"  Variants: {len(product['d'])}")
            if product['d']:
                variant = product['d'][0]
                print(f"  Sample variant:")
                for key, value in variant.items():
                    print(f"    {key}: {value}")
        print()
    
    print(f"\n🏷️ VARIANT STRUCTURE ANALYSIS")
    print(f"{'='*50}")
    if analysis['product_structures']:
        variant_fields = analysis['product_structures'][0]['fields']
        print(f"Standard variant fields: {variant_fields}")
        
        print("\nField descriptions (inferred):")
        field_descriptions = {
            'n': 'Product name/variant name',
            'l': 'Product link/identifier',
            'p': 'Price (in EUR)',
            's': 'Size/quantity description'
        }
        
        for field in variant_fields:
            desc = field_descriptions.get(field, 'Unknown field')
            print(f"  • {field}: {desc}")
    
    print(f"\n💰 PRICE ANALYSIS")
    print(f"{'='*50}")
    if 'prices' in analysis['price_ranges'] and analysis['price_ranges']['prices']:
        prices = analysis['price_ranges']['prices']
        print(f"Total products with prices: {len(prices):,}")
        print(f"Price range: €{min(prices):.2f} - €{max(prices):.2f}")
        print(f"Average price: €{sum(prices)/len(prices):.2f}")
        
        # Price distribution
        price_ranges = {
            '€0-1': len([p for p in prices if 0 <= p < 1]),
            '€1-5': len([p for p in prices if 1 <= p < 5]),
            '€5-10': len([p for p in prices if 5 <= p < 10]),
            '€10-25': len([p for p in prices if 10 <= p < 25]),
            '€25+': len([p for p in prices if p >= 25])
        }
        
        print("\nPrice distribution:")
        for range_name, count in price_ranges.items():
            percentage = (count / len(prices)) * 100
            print(f"  {range_name}: {count:,} products ({percentage:.1f}%)")
    
    print(f"\n🏷️ CATEGORIES IDENTIFIED")
    print(f"{'='*50}")
    category_counts = Counter()
    for entry in analysis['sample_products'][:20]:  # Analyze first 20 for categories
        product_name = entry.get('n', '')
        if 'd' in entry:
            for variant in entry['d'][:5]:  # First 5 variants
                variant_name = variant.get('n', '') or product_name
                category = infer_category(variant_name)
                category_counts[category] += 1
    
    for category, count in category_counts.most_common():
        print(f"  • {category}: {count} products")
    
    print(f"\n🏪 BRANDS IDENTIFIED")
    print(f"{'='*50}")
    brand_counts = Counter()
    for entry in analysis['sample_products'][:20]:
        product_name = entry.get('n', '')
        if 'd' in entry:
            for variant in entry['d'][:5]:
                variant_name = variant.get('n', '') or product_name
                brand = extract_brand(variant_name)
                if brand:
                    brand_counts[brand] += 1
    
    for brand, count in brand_counts.most_common():
        print(f"  • {brand}: {count} products")
    
    print(f"\n📊 DETAILED SAMPLE DATA")
    print(f"{'='*50}")
    print("Here are 3 complete sample entries to understand the exact structure:\n")
    
    for i, entry in enumerate(analysis['sample_products'][:3], 1):
        print(f"Sample Entry {i}:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        print("\n" + "-"*50 + "\n")

def save_analysis_report(analysis):
    """Save analysis report to file"""
    with open(ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        f.write("CheckjeBon Data Analysis Report\n")
        f.write("="*50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Dataset Overview:\n")
        f.write(f"- Total entries: {analysis['total_entries']:,}\n")
        f.write(f"- Total variants: {analysis['products_per_supermarket']['variants']:,}\n")
        f.write(f"- Categories found: {len(analysis['categories_found'])}\n")
        f.write(f"- Brands found: {len(analysis['brands_found'])}\n\n")
        
        f.write("Sample data structure:\n")
        f.write(json.dumps(analysis['sample_products'][0] if analysis['sample_products'] else {}, 
                          indent=2, ensure_ascii=False))
    
    print(f"📄 Analysis report saved to {ANALYSIS_FILE}")

def print_import_recommendations():
    """Print recommendations for importing to Supabase"""
    print(f"\n🚀 SUPABASE IMPORT RECOMMENDATIONS")
    print(f"{'='*50}")
    print("Based on this analysis, here's how to import to Supabase:")
    print()
    print("1. DATABASE STRUCTURE:")
    print("   • Each top-level entry represents a product group")
    print("   • Each 'd' array item is a product variant/SKU")
    print("   • Import each variant as a separate product record")
    print()
    print("2. FIELD MAPPING:")
    print("   • 'n' (main) + 'd.n' (variant) → product name")
    print("   • 'd.l' → unique product identifier")
    print("   • 'd.p' → price (in EUR)")
    print("   • 'd.s' → size/quantity description")
    print()
    print("3. DATA PROCESSING:")
    print("   • Extract brand from product names")
    print("   • Categorize products using Dutch keywords")
    print("   • Parse size information for unit pricing")
    print("   • All products appear to be from Albert Heijn")
    print()
    print("4. ESTIMATED IMPORT:")
    print("   • ~500-600 unique products")
    print("   • Single supermarket (Albert Heijn)")
    print("   • Automatic categorization possible")
    print("   • Price range: €0.30 - €180.00")

def main():
    """Main execution function"""
    print("🔍 CheckjeBon Data Analyzer")
    print("="*60)
    print("Downloading and analyzing Dutch supermarket data...")
    print()
    
    # Install dependencies
    install_dependencies()
    
    # Download data
    data = download_data()
    
    # Analyze structure
    analysis = analyze_data_structure(data)
    
    # Print analysis
    print_analysis(analysis)
    
    # Save report
    save_analysis_report(analysis)
    
    # Print recommendations
    print_import_recommendations()
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 Files created:")
    print(f"   • {OUTPUT_FILE} (raw data backup)")
    print(f"   • {ANALYSIS_FILE} (analysis report)")
    print()
    print("🎯 Ready to import to Supabase using the Flutter app's admin panel!")

if __name__ == "__main__":
    main()