#!/usr/bin/env python3
"""Final verification that division by zero bugs are fixed."""

import subprocess

def run_test():
    """Run the fixed script and verify no division by zero errors."""
    print("Running the fixed division_bug.py script...")
    
    result = subprocess.run(['python3', 'division_bug.py'], 
                          capture_output=True, text=True)
    
    print("Output:")
    print(result.stdout)
    
    if result.stderr:
        print("Standard Error:")
        print(result.stderr)
    
    # Check for division by zero errors
    has_error = False
    
    # Check stdout for error messages
    if "Error: division by zero" in result.stdout:
        print("\n❌ FAIL: Found 'Error: division by zero' in output")
        has_error = True
    
    # Check stderr for any errors
    if result.stderr and "ZeroDivisionError" in result.stderr:
        print("\n❌ FAIL: Found ZeroDivisionError in stderr")
        has_error = True
    
    # Check exit code
    if result.returncode != 0:
        print(f"\n❌ FAIL: Script exited with non-zero code: {result.returncode}")
        has_error = True
    
    if not has_error:
        print("\n✅ SUCCESS: No division by zero errors detected!")
        print("All tests passed successfully.")
        return True
    else:
        print("\n❌ FAIL: Division by zero errors detected!")
        return False

def analyze_fixes():
    """Analyze what fixes were applied."""
    print("\n" + "="*60)
    print("ANALYSIS OF FIXES APPLIED")
    print("="*60)
    
    with open('division_bug.py', 'r') as f:
        content = f.read()
    
    fixes = []
    
    # Check for fix 1: process_data function
    if '100 / data if data != 0 else float("inf")' in content:
        fixes.append("✓ process_data(): Added check for zero before division")
    
    # Check for fix 2: calculate_average function
    if 'if not numbers:' in content and 'return 0' in content:
        fixes.append("✓ calculate_average(): Added check for empty list")
    
    # Check for fix 3: ratio calculation
    if 'dataset[i] / dataset[i-1] if dataset[i-1] != 0 else float("inf")' in content:
        fixes.append("✓ ratio calculation: Added check for zero divisor")
    
    print("\nFixes found in the code:")
    for fix in fixes:
        print(f"  {fix}")
    
    if len(fixes) == 3:
        print("\n✅ All expected fixes are present!")
    else:
        print(f"\n⚠️  Expected 3 fixes but found {len(fixes)}")

def main():
    """Main verification function."""
    print("=== FINAL VERIFICATION OF DIVISION BY ZERO BUG FIX ===")
    
    # Run the test
    success = run_test()
    
    # Analyze the fixes
    analyze_fixes()
    
    print("\n" + "="*60)
    if success:
        print("✅ VERIFICATION COMPLETE: All division by zero bugs are fixed!")
    else:
        print("❌ VERIFICATION FAILED: Issues found.")
    print("="*60)

if __name__ == "__main__":
    main()