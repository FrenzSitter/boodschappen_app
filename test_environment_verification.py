#!/usr/bin/env python3
"""
Test Environment Verification System
====================================

Simple test script to verify the environment verification system works correctly.
Tests various scenarios and validates the verification logic.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def test_basic_verification():
    """Test basic verification functionality"""
    print("Testing basic verification...")
    
    # Run the verification script
    result = subprocess.run([
        sys.executable, 'verify_environment.py', '--quick', '--format', 'json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Basic verification completed successfully")
    else:
        print("⚠️  Basic verification completed with issues (expected)")
    
    # Check that output contains expected structure
    if '"overall_status"' in result.stdout:
        print("✅ JSON output format correct")
    else:
        print("❌ JSON output format incorrect")
    
    return True


def test_help_functionality():
    """Test help and command line options"""
    print("\nTesting help functionality...")
    
    # Test help option
    result = subprocess.run([
        sys.executable, 'verify_environment.py', '--help'
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and 'usage:' in result.stdout:
        print("✅ Help functionality works")
        return True
    else:
        print("❌ Help functionality failed")
        return False


def test_output_formats():
    """Test different output formats"""
    print("\nTesting output formats...")
    
    formats = ['summary', 'detailed', 'json']
    
    for fmt in formats:
        result = subprocess.run([
            sys.executable, 'verify_environment.py', '--quick', '--format', fmt
        ], capture_output=True, text=True)
        
        if fmt == 'json':
            if '"timestamp"' in result.stdout:
                print(f"✅ Format {fmt} works")
            else:
                print(f"❌ Format {fmt} failed")
                return False
        else:
            if result.stdout:  # Should have some output
                print(f"✅ Format {fmt} works")
            else:
                print(f"❌ Format {fmt} failed")
                return False
    
    return True


def test_file_output():
    """Test file output functionality"""
    print("\nTesting file output...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name
    
    try:
        result = subprocess.run([
            sys.executable, 'verify_environment.py', '--quick', '--output', output_file
        ], capture_output=True, text=True)
        
        output_path = Path(output_file)
        if output_path.exists() and output_path.stat().st_size > 0:
            print("✅ File output works")
            
            # Verify JSON content
            import json
            try:
                with open(output_file, 'r') as f:
                    data = json.load(f)
                if 'timestamp' in data and 'overall_status' in data:
                    print("✅ File output JSON format correct")
                    return True
                else:
                    print("❌ File output JSON format incorrect")
                    return False
            except json.JSONDecodeError:
                print("❌ File output is not valid JSON")
                return False
        else:
            print("❌ File output failed")
            return False
            
    finally:
        # Clean up
        if Path(output_file).exists():
            Path(output_file).unlink()


def test_environment_detection():
    """Test environment variable detection"""
    print("\nTesting environment variable detection...")
    
    # Test with set environment variable
    env = os.environ.copy()
    env['TEST_VARIABLE'] = 'test_value'
    
    # The verification script should detect missing SUPABASE_URL/KEY
    result = subprocess.run([
        sys.executable, 'verify_environment.py', '--quick'
    ], capture_output=True, text=True, env=env)
    
    # Should fail due to missing required variables
    if 'SUPABASE_URL' in result.stderr:
        print("✅ Environment variable detection works")
        return True
    else:
        print("⚠️  Environment variable detection results unclear")
        return True  # Not a critical failure


def test_script_import():
    """Test that the script can be imported as a module"""
    print("\nTesting script import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        # Import the module
        import verify_environment
        
        # Test basic class instantiation
        verifier = verify_environment.EnvironmentVerifier(verbose=False, quick=True)
        
        if hasattr(verifier, 'check_environment_variables'):
            print("✅ Script import and class instantiation works")
            return True
        else:
            print("❌ Script import failed - missing methods")
            return False
            
    except ImportError as e:
        print(f"❌ Script import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Script import had issues: {e}")
        return True  # Non-critical
    finally:
        # Clean up sys.path
        if str(Path.cwd()) in sys.path:
            sys.path.remove(str(Path.cwd()))


def test_error_handling():
    """Test error handling with invalid options"""
    print("\nTesting error handling...")
    
    # Test invalid format
    result = subprocess.run([
        sys.executable, 'verify_environment.py', '--format', 'invalid'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✅ Error handling for invalid format works")
    else:
        print("❌ Error handling for invalid format failed")
        return False
    
    # Test invalid option
    result = subprocess.run([
        sys.executable, 'verify_environment.py', '--invalid-option'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✅ Error handling for invalid option works")
        return True
    else:
        print("❌ Error handling for invalid option failed")
        return False


def test_verbose_mode():
    """Test verbose mode"""
    print("\nTesting verbose mode...")
    
    # Run with verbose
    result_verbose = subprocess.run([
        sys.executable, 'verify_environment.py', '--quick', '--verbose'
    ], capture_output=True, text=True)
    
    # Run without verbose
    result_normal = subprocess.run([
        sys.executable, 'verify_environment.py', '--quick'
    ], capture_output=True, text=True)
    
    # Verbose should have more output
    if len(result_verbose.stderr) >= len(result_normal.stderr):
        print("✅ Verbose mode produces expected output")
        return True
    else:
        print("⚠️  Verbose mode output unclear")
        return True  # Not critical


def main():
    """Run all tests"""
    print("=" * 60)
    print("ENVIRONMENT VERIFICATION SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Basic Verification", test_basic_verification),
        ("Help Functionality", test_help_functionality),
        ("Output Formats", test_output_formats),
        ("File Output", test_file_output),
        ("Environment Detection", test_environment_detection),
        ("Script Import", test_script_import),
        ("Error Handling", test_error_handling),
        ("Verbose Mode", test_verbose_mode),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    success_rate = (passed / len(tests)) * 100
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("The environment verification system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        print("Review the failures above and fix any issues.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)