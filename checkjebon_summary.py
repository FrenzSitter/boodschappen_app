#!/usr/bin/env python3
"""
CheckjeBon Data Summary
======================
Quick analysis script to understand the CheckjeBon dataset structure
"""

import json
import requests
from collections import defaultdict, Counter

def analyze_checkjebon_data():
    """Download and analyze CheckjeBon data"""
    
    # Download data
    print("📡 Downloading CheckjeBon dataset...")
    url = "https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Downloaded {len(data)} supermarket entries\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Analyze structure
    total_products = 0
    supermarkets = {}
    sample_products = []
    
    for entry in data:
        supermarket_name = entry.get('n', 'Unknown')
        variants = entry.get('d', [])
        products_count = len(variants)
        
        supermarkets[supermarket_name] = products_count
        total_products += products_count
        
        # Collect sample products
        if len(sample_products) < 10 and variants:
            for variant in variants[:2]:  # First 2 variants
                sample_products.append({
                    'supermarket': supermarket_name,
                    'name': variant.get('n', ''),
                    'price': variant.get('p', 0),
                    'size': variant.get('s', ''),
                    'link': variant.get('l', '')
                })
                if len(sample_products) >= 10:
                    break
    
    # Print analysis
    print("📊 DATASET ANALYSIS")
    print("="*50)
    print(f"Total supermarkets: {len(supermarkets)}")
    print(f"Total products: {total_products:,}")
    print()
    
    print("🏪 SUPERMARKETS & PRODUCT COUNTS:")
    for name, count in sorted(supermarkets.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {name}: {count:,} products")
    print()
    
    print("🛍️ SAMPLE PRODUCTS:")
    for i, product in enumerate(sample_products[:5], 1):
        print(f"  {i}. {product['name']}")
        print(f"     Price: €{product['price']}")
        print(f"     Size: {product['size']}")
        print(f"     Store: {product['supermarket']}")
        print()
    
    print("📋 DATA STRUCTURE:")
    if sample_products:
        print("Each supermarket entry contains:")
        print("  • 'n': Supermarket name")
        print("  • 'd': Array of products with:")
        print("    - 'n': Product name")
        print("    - 'p': Price (EUR)")
        print("    - 's': Size/quantity")
        print("    - 'l': Product identifier/link")
    
    print(f"\n🎯 IMPORT SUMMARY:")
    print(f"This dataset contains {total_products:,} products across {len(supermarkets)} Dutch supermarkets.")
    print("Perfect for importing into your Supabase database!")

if __name__ == "__main__":
    analyze_checkjebon_data()