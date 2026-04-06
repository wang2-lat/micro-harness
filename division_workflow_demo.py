#!/usr/bin/env python3
"""Complete workflow: Create bug, find it, fix it."""

import os
import sys

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)

def main():
    """Demonstrate the complete workflow."""
    print_header("DIVISION BY ZERO BUG: COMPLETE WORKFLOW")
    
    print("This demonstration shows:")
    print("1. Creating a Python script with division by zero bugs")
    print("2. Finding the bugs using static analysis")
    print("3. Fixing the bugs with proper error handling")
    print("4. Testing the fixes")
    
    # List created files
    print_header("CREATED FILES")
    
    files = [
        ("division_bug_example2.py", "Buggy script with division by zero"),
        ("find_division_bugs.py", "Bug finder using AST analysis"),
        ("division_bug_fixed_example.py", "Fixed version with error handling"),
        ("test_division_fix.py", "Comprehensive test suite"),
    ]
    
    for filename, description in files:
        if os.path.exists(filename):
            print(f"✓ {filename:35} - {description}")
        else:
            print(f"✗ {filename:35} - {description} (missing)")
    
    # Show buggy code snippet
    print_header("BUGGY CODE EXAMPLE")
    print("The buggy script contains:")
    print('''
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    average = total / count  # BUG: division by zero if numbers is empty
    return average
''')
    
    # Show bug finder output
    print_header("BUG FINDER OUTPUT")
    print("Running the bug finder on our example:")
    os.system("python3 find_division_bugs.py division_bug_example2.py 2>/dev/null | grep -A5 'division_bug_example2.py'")
    
    # Show fixed code snippet
    print_header("FIXED CODE EXAMPLE")
    print("The fixed version includes:")
    print('''
def calculate_average(numbers):
    if not numbers:  # FIX: Check before dividing
        raise ValueError("Cannot calculate average of empty list")
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average

def safe_divide(numerator, denominator, default=0.0):
    if denominator == 0:  # FIX: Handle zero denominator
        return default
    return numerator / denominator
''')
    
    # Show test results
    print_header("TEST RESULTS")
    os.system("python3 test_division_fix.py 2>&1 | tail -20")
    
    print_header("WORKFLOW COMPLETE")
    print("\nSummary of what was accomplished:")
    print("1. Created a realistic Python script with division by zero bugs")
    print("2. Built an AST-based analyzer to detect potential division bugs")
    print("3. Implemented proper fixes: input validation and safe division")
    print("4. Created comprehensive tests to verify the fixes")
    print("\nKey techniques demonstrated:")
    print("  - AST parsing for static analysis")
    print("  - Defensive programming with preconditions")
    print("  - Graceful error handling with exceptions")
    print("  - Safe defaults for division operations")
    
    print("\nTo run the complete demo yourself:")
    print("  python3 division_bug_example2.py      # See the bug")
    print("  python3 find_division_bugs.py .       # Find bugs")
    print("  python3 division_bug_fixed_example.py # See the fix")
    print("  python3 test_division_fix.py          # Run tests")

if __name__ == "__main__":
    main()