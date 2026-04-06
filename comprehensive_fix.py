#!/usr/bin/env python3
"""Comprehensive fix for division by zero bugs."""

import re

def fix_all_division_bugs(filename):
    """Fix all division by zero bugs in a Python file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    changes_made = False
    
    # Fix 1: The process_data function
    for i, line in enumerate(lines):
        if 'value = 100 / data' in line:
            print(f"Found bug 1 at line {i+1}: {line.strip()}")
            # Replace with safe division
            lines[i] = line.replace(
                'value = 100 / data',
                'value = 100 / data if data != 0 else float("inf")'
            )
            print(f"Fixed: {lines[i].strip()}")
            changes_made = True
    
    # Fix 2: The calculate_average function
    for i, line in enumerate(lines):
        if 'average = total / count' in line:
            print(f"\nFound bug 2 at line {i+1}: {line.strip()}")
            # We need to check the context - this function should handle empty lists
            # Let's modify the whole function
            if i > 3:  # Make sure we have enough context
                # Find the function start
                func_start = i
                while func_start > 0 and 'def calculate_average' not in lines[func_start]:
                    func_start -= 1
                
                # Replace the entire function
                new_func = '''def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0  # Or float('nan') or raise an exception
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average
'''
                # Replace from func_start to find where function ends
                # Simple approach: replace a few lines
                lines[func_start] = new_func
                # Clear the next few lines (simplified approach)
                for j in range(func_start + 1, min(func_start + 10, len(lines))):
                    if lines[j].strip().startswith('def ') or lines[j].strip() == '':
                        break
                    lines[j] = ''
                
                print("Fixed calculate_average function to handle empty lists")
                changes_made = True
    
    # Fix 3: The ratio calculation in analyze_dataset
    for i, line in enumerate(lines):
        if 'ratio = dataset[i] / dataset[i-1]' in line:
            print(f"\nFound bug 3 at line {i+1}: {line.strip()}")
            # Replace with safe division
            lines[i] = line.replace(
                'ratio = dataset[i] / dataset[i-1]',
                'ratio = dataset[i] / dataset[i-1] if dataset[i-1] != 0 else float("inf")'
            )
            print(f"Fixed: {lines[i].strip()}")
            changes_made = True
    
    if changes_made:
        # Write the fixed file
        with open(filename, 'w') as f:
            f.writelines(lines)
        print(f"\nAll fixes applied to {filename}")
        return True
    else:
        print("No bugs found to fix")
        return False

def test_fixes():
    """Test that the fixes work."""
    print("Testing the fixed script...")
    try:
        import subprocess
        result = subprocess.run(['python3', 'division_bug.py'], 
                              capture_output=True, text=True)
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        # Check if there are any division by zero errors
        if "division by zero" in result.stdout or "division by zero" in result.stderr:
            print("\n❌ FAIL: Division by zero error still present!")
            return False
        else:
            print("\n✅ SUCCESS: No division by zero errors!")
            return True
    except Exception as e:
        print(f"Error running script: {e}")
        return False

def main():
    """Main function."""
    print("=== Division by Zero Bug Fixer ===\n")
    
    filename = "division_bug.py"
    
    # Apply fixes
    if fix_all_division_bugs(filename):
        print("\n" + "="*50)
        print("Verifying fixes...")
        print("="*50)
        
        if test_fixes():
            print("\n✅ All bugs fixed successfully!")
        else:
            print("\n❌ Some bugs may still exist.")
    else:
        print("No changes were made.")

if __name__ == "__main__":
    main()