#!/usr/bin/env python3
"""
Test Script for Manual Import Tool
=================================

Simple test script to verify the manual import tool functionality
without requiring actual database connections.
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from manual_import import ManualImporter, ConflictResolution, ImportStep


def test_initialization():
    """Test importer initialization"""
    print("Testing importer initialization...")
    
    importer = ManualImporter(
        interactive=False,
        dry_run=True,
        log_level="INFO",
        conflict_resolution=ConflictResolution.SKIP
    )
    
    assert importer.dry_run == True
    assert importer.interactive == False
    assert importer.conflict_resolution == ConflictResolution.SKIP
    assert importer.import_id.startswith("manual_")
    
    print("✓ Initialization test passed")


def test_sample_data_generation():
    """Test sample data generation"""
    print("Testing sample data generation...")
    
    importer = ManualImporter(dry_run=True)
    
    # Test supermarkets data
    supermarkets = importer.create_sample_data("supermarkets")
    assert isinstance(supermarkets, list)
    assert len(supermarkets) > 0
    assert all('id' in sm and 'name' in sm for sm in supermarkets)
    
    # Test categories data
    categories = importer.create_sample_data("categories")
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert all('id' in cat and 'name' in cat for cat in categories)
    
    # Test products data
    products = importer.create_sample_data("products")
    assert isinstance(products, list)
    assert len(products) > 0
    assert all('id' in prod and 'name' in prod for prod in products)
    
    print("✓ Sample data generation test passed")


def test_data_validation():
    """Test data validation functionality"""
    print("Testing data validation...")
    
    importer = ManualImporter(dry_run=True)
    
    # Test valid data
    valid_data = [
        {
            'id': 'test-1',
            'name': 'Test Supermarket',
            'slug': 'test-supermarket',
            'is_active': True
        }
    ]
    
    result = importer.validate_data_structure("supermarkets", valid_data)
    assert result['valid'] == True
    assert result['record_count'] == 1
    
    # Test invalid data
    invalid_data = [
        {
            'name': 'Test Supermarket'  # Missing required 'id' field
        }
    ]
    
    result = importer.validate_data_structure("supermarkets", invalid_data)
    assert result['valid'] == False
    assert len(result['errors']) > 0
    
    print("✓ Data validation test passed")


def test_download_step():
    """Test download step functionality"""
    print("Testing download step...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        importer = ManualImporter(dry_run=True)
        importer.data_dir = Path(temp_dir)
        
        # Mock interactive responses
        with patch.object(importer, 'ask_user', return_value="Yes (use sample data)"):
            success = importer.step_download()
        
        assert success == True
        
        # Check that data files were created
        for source in ['supermarkets', 'categories', 'products', 'prices']:
            data_file = importer.data_dir / f"{source}_{importer.import_id}.json"
            assert data_file.exists(), f"Data file not created: {data_file}"
            
            # Verify file contents
            with open(data_file, 'r') as f:
                data = json.load(f)
            assert isinstance(data, list)
    
    print("✓ Download step test passed")


def test_validation_step():
    """Test validation step functionality"""
    print("Testing validation step...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        importer = ManualImporter(dry_run=True)
        importer.data_dir = Path(temp_dir)
        importer.reports_dir = Path(temp_dir)
        
        # Create sample data files
        sample_data = {
            'supermarkets': [{'id': 'test-1', 'name': 'Test Market', 'slug': 'test'}],
            'categories': [{'id': 'cat-1', 'name': 'Test Category', 'slug': 'test-cat'}],
            'products': [{'id': 'prod-1', 'name': 'Test Product'}],
            'prices': [{'id': 'price-1', 'product_id': 'prod-1', 'price': 1.99}]
        }
        
        for source, data in sample_data.items():
            data_file = importer.data_dir / f"{source}_{importer.import_id}.json"
            with open(data_file, 'w') as f:
                json.dump(data, f)
        
        success = importer.step_validate()
        assert success == True
        
        # Check validation report was created
        validation_file = importer.reports_dir / f"validation_{importer.import_id}.json"
        assert validation_file.exists()
    
    print("✓ Validation step test passed")


def test_conflict_resolution():
    """Test conflict resolution functionality"""
    print("Testing conflict resolution...")
    
    importer = ManualImporter(dry_run=True)
    
    # Mock Supabase client
    mock_supabase = Mock()
    mock_result = Mock()
    mock_result.data = []  # No existing data
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    importer.supabase = mock_supabase
    
    test_record = {'id': 'test-1', 'name': 'Test Record'}
    
    # Test no conflict scenario
    resolved = importer.resolve_conflicts("test_table", test_record)
    assert resolved == test_record
    
    # Test conflict scenario
    mock_result.data = [{'id': 'test-1', 'name': 'Existing Record'}]  # Existing data
    
    importer.conflict_resolution = ConflictResolution.SKIP
    resolved = importer.resolve_conflicts("test_table", test_record)
    assert resolved is None
    
    importer.conflict_resolution = ConflictResolution.CREATE_NEW
    resolved = importer.resolve_conflicts("test_table", test_record)
    assert resolved is not None
    assert resolved['id'] != test_record['id']  # Should have new ID
    
    print("✓ Conflict resolution test passed")


def test_report_generation():
    """Test report generation functionality"""
    print("Testing report generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        importer = ManualImporter(dry_run=True)
        importer.reports_dir = Path(temp_dir)
        
        # Create a sample report
        report = importer.create_report("test_step")
        report.records_processed = 10
        report.records_inserted = 8
        report.records_skipped = 2
        importer.finish_report(report, "completed")
        
        # Save reports
        report_file = importer.save_reports()
        assert report_file.exists()
        
        # Verify report contents
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        assert report_data['import_id'] == importer.import_id
        assert len(report_data['reports']) == 1
        assert report_data['reports'][0]['step'] == 'test_step'
        assert report_data['reports'][0]['records_processed'] == 10
    
    print("✓ Report generation test passed")


def test_command_line_parsing():
    """Test command line argument parsing"""
    print("Testing command line parsing...")
    
    # Import the main function
    from manual_import import main
    
    # Test with mock arguments
    test_args = [
        'manual_import.py',
        '--dry-run',
        '--conflict-resolution', 'skip',
        '--log-level', 'DEBUG'
    ]
    
    with patch('sys.argv', test_args):
        with patch('manual_import.ManualImporter') as mock_importer:
            mock_instance = Mock()
            mock_instance.run_full_import.return_value = True
            mock_importer.return_value = mock_instance
            
            result = main()
            assert result == 0
            
            # Verify importer was created with correct parameters
            mock_importer.assert_called_once()
            call_args = mock_importer.call_args
            assert call_args[1]['dry_run'] == True
            assert call_args[1]['log_level'] == 'DEBUG'
    
    print("✓ Command line parsing test passed")


def run_all_tests():
    """Run all tests"""
    print("Running Manual Import Tool Tests...")
    print("=" * 50)
    
    tests = [
        test_initialization,
        test_sample_data_generation,
        test_data_validation,
        test_download_step,
        test_validation_step,
        test_conflict_resolution,
        test_report_generation,
        test_command_line_parsing
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)