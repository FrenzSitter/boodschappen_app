#!/usr/bin/env python3
"""
Test script for CheckjeBon to Supabase import
=============================================

This script tests the import functionality without making database changes.
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_data_download():
    """Test data download functionality"""
    print("🧪 Testing data download...")
    
    try:
        from supabase_import import CheckjeBonImporter
        
        # Mock environment variables for testing
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test_key'
        
        # Create importer instance
        importer = CheckjeBonImporter(
            supabase_url=os.environ['SUPABASE_URL'],
            supabase_key=os.environ['SUPABASE_KEY'],
            dry_run=True
        )
        
        # Test data download
        data = importer.download_checkjebon_data()
        
        print(f"✅ Successfully downloaded {len(data)} entries")
        
        # Analyze first few entries
        if data:
            print("\n📊 Sample data structure:")
            sample = data[0]
            print(json.dumps(sample, indent=2, ensure_ascii=False)[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Data download test failed: {e}")
        return False

def test_category_inference():
    """Test category inference functionality"""
    print("\n🧪 Testing category inference...")
    
    try:
        from supabase_import import CheckjeBonImporter
        
        # Mock environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test_key'
        
        # Create importer instance
        importer = CheckjeBonImporter(
            supabase_url=os.environ['SUPABASE_URL'],
            supabase_key=os.environ['SUPABASE_KEY'],
            dry_run=True
        )
        
        # Test category inference
        test_products = [
            "AH Melk halfvol 1 liter",
            "Coca Cola 330ml",
            "Albert Heijn Brood wit",
            "Campina Yoghurt aardbei",
            "Heineken Bier 6 pack",
            "Bananen per kilo",
            "Gehakt rundvlees 500g"
        ]
        
        print("Product categorization results:")
        for product in test_products:
            category = importer.infer_category(product)
            brand = importer.extract_brand(product)
            print(f"• {product}")
            print(f"  Category: {category or 'Unknown'}")
            print(f"  Brand: {brand or 'Unknown'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Category inference test failed: {e}")
        return False

def test_size_parsing():
    """Test size parsing functionality"""
    print("\n🧪 Testing size parsing...")
    
    try:
        from supabase_import import CheckjeBonImporter
        
        # Mock environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test_key'
        
        # Create importer instance
        importer = CheckjeBonImporter(
            supabase_url=os.environ['SUPABASE_URL'],
            supabase_key=os.environ['SUPABASE_KEY'],
            dry_run=True
        )
        
        # Test size parsing
        test_sizes = [
            "500ml",
            "1 kg",
            "250 gram",
            "5 x 250ml",
            "1,5 liter",
            "750g",
            "6 stuks",
            "330ml blik"
        ]
        
        print("Size parsing results:")
        for size_text in test_sizes:
            size, unit = importer.parse_size_info(size_text)
            print(f"• '{size_text}' → {size} {unit}")
        
        return True
        
    except Exception as e:
        print(f"❌ Size parsing test failed: {e}")
        return False

def test_product_normalization():
    """Test product name normalization"""
    print("\n🧪 Testing product normalization...")
    
    try:
        from supabase_import import CheckjeBonImporter
        
        # Mock environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test_key'
        
        # Create importer instance
        importer = CheckjeBonImporter(
            supabase_url=os.environ['SUPABASE_URL'],
            supabase_key=os.environ['SUPABASE_KEY'],
            dry_run=True
        )
        
        # Test normalization
        test_names = [
            "AH Melk halfvol 1L",
            "Coca-Cola® Original 330ml",
            "Albert Heijn Brood wit (vers)",
            "Campina Yoghurt aardbei 150g",
            "Heineken® Bier 6-pack"
        ]
        
        print("Name normalization results:")
        for name in test_names:
            normalized = importer.normalize_product_name(name)
            print(f"• '{name}' → '{normalized}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Product normalization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 CheckjeBon Import Test Suite")
    print("=" * 50)
    
    tests = [
        ("Data Download", test_data_download),
        ("Category Inference", test_category_inference),
        ("Size Parsing", test_size_parsing),
        ("Product Normalization", test_product_normalization)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} passed")
                passed += 1
            else:
                print(f"❌ {test_name} failed")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"🧪 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())