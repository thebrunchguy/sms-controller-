#!/usr/bin/env python3
"""
Test runner for the Monthly SMS Check-in application
"""

import os
import sys
import subprocess

def run_test(test_file):
    """Run a specific test file"""
    print(f"\n🧪 Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test completed successfully")
            print(result.stdout)
        else:
            print("❌ Test failed")
            print(result.stdout)
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Monthly SMS Check-in - Test Suite")
    print("=" * 50)
    
    # List of tests to run in order
    tests = [
        "test_airtable.py",
        "simple_table_test.py"
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if run_test(test):
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 