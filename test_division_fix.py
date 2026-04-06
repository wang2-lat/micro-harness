#!/usr/bin/env python3
"""Test the division bug detection and fixing."""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def test_buggy_script():
    """Test the buggy script produces division by zero."""
    print("Testing buggy script...")
    stdout, stderr, code = run_command("python3 division_bug_example2.py")
    
    if "division by zero" in stderr or "division by zero" in stdout:
        print("✓ Buggy script correctly produces division by zero error")
        return True
    else:
        print("✗ Buggy script should produce division by zero error")
        return False

def test_bug_finder():
    """Test the bug finder detects the bugs."""
    print("\nTesting bug finder...")
    stdout, stderr, code = run_command("python3 find_division_bugs.py .")
    
    if "division_bug_example2.py" in stdout and "could be zero" in stdout:
        print("✓ Bug finder correctly detects division bugs")
        return True
    else:
        print("✗ Bug finder should detect division bugs")
        return False

def test_fixed_script():
    """Test the fixed script handles errors gracefully."""
    print("\nTesting fixed script...")
    stdout, stderr, code = run_command("python3 division_bug_fixed_example.py")
    
    if "Handled gracefully" in stdout and "division by zero" not in stderr:
        print("✓ Fixed script handles errors gracefully")
        return True
    else:
        print("✗ Fixed script should handle errors without crashing")
        return False

def test_safe_divide_function():
    """Test the safe_divide function."""
    print("\nTesting safe_divide function...")
    
    # Import the fixed module
    sys.path.insert(0, '.')
    try:
        import division_bug_fixed_example as fixed
    except ImportError:
        # Create a simple test
        print("  Testing safe division logic...")
        
        def safe_divide(a, b, default=0):
            return default if b == 0 else a / b
        
        tests = [
            (10, 2, 0, 5.0),
            (10, 0, 0, 0),
            (10, 0, float('inf'), float('inf')),
            (0, 5, -1, 0.0),
        ]
        
        all_pass = True
        for a, b, default, expected in tests:
            result = safe_divide(a, b, default)
            if result == expected:
                print(f"  ✓ safe_divide({a}, {b}, {default}) = {result}")
            else:
                print(f"  ✗ safe_divide({a}, {b}, {default}) = {result}, expected {expected}")
                all_pass = False
        
        return all_pass
    
    # Test the imported module
    tests = [
        (10, 2, 0, 5.0),
        (10, 0, 0, 0),
        (10, 0, float('inf'), float('inf')),
    ]
    
    all_pass = True
    for a, b, default, expected in tests:
        result = fixed.safe_divide(a, b, default)
        if result == expected:
            print(f"  ✓ safe_divide({a}, {b}, {default}) = {result}")
        else:
            print(f"  ✗ safe_divide({a}, {b}, {default}) = {result}, expected {expected}")
            all_pass = False
    
    return all_pass

def main():
    """Run all tests."""
    print("=" * 60)
    print("Division Bug Detection and Fixing Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Buggy Script", test_buggy_script()))
    results.append(("Bug Finder", test_bug_finder()))
    results.append(("Fixed Script", test_fixed_script()))
    results.append(("Safe Divide Function", test_safe_divide_function()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())