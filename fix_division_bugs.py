#!/usr/bin/env python3
"""Fix division by zero bugs in Python files."""

import ast
import sys
from pathlib import Path

class DivisionBugFixer(ast.NodeTransformer):
    """AST transformer to fix division by zero bugs."""
    
    def __init__(self):
        self.fixes_applied = 0
    
    def visit_BinOp(self, node):
        """Fix division operations by adding zero checks."""
        if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            # Check if we should add a guard
            if self.should_add_guard(node.right):
                # Create a conditional expression: b if b != 0 else 1 (or handle appropriately)
                # For now, we'll wrap it in a try-except or add a check
                # Let's create: (a / b) if b != 0 else 0
                self.fixes_applied += 1
                
                # Create comparison: b != 0
                compare = ast.Compare(
                    left=node.right,
                    ops=[ast.NotEq()],
                    comparators=[ast.Constant(value=0)]
                )
                
                # Create safe division: a / b
                safe_div = ast.BinOp(left=node.left, op=node.op, right=node.right)
                
                # Create default value (0 for division, could be float('inf') or other)
                default = ast.Constant(value=0)
                
                # Create conditional expression
                conditional = ast.IfExp(
                    test=compare,
                    body=safe_div,
                    orelse=default
                )
                
                return conditional
        
        return self.generic_visit(node)
    
    def should_add_guard(self, node):
        """Determine if we should add a guard for this operand."""
        if isinstance(node, ast.Constant):
            return node.value == 0
        elif isinstance(node, ast.Name):
            return True  # Variable could be zero
        elif isinstance(node, ast.Call):
            return True  # Function call could return zero
        elif isinstance(node, ast.BinOp):
            return True  # Expression could evaluate to zero
        return False

def fix_division_bugs_in_file(filepath):
    """Fix division bugs in a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        fixer = DivisionBugFixer()
        fixed_tree = fixer.visit(tree)
        
        # Add import for math if needed
        fixed_code = ast.unparse(fixed_tree)
        
        # Write backup
        backup_path = filepath + '.bak'
        with open(backup_path, 'w') as f:
            f.write(content)
        
        # Write fixed version
        with open(filepath, 'w') as f:
            f.write(fixed_code)
        
        return fixer.fixes_applied
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0

def create_safe_division_fixed_version():
    """Create a fixed version of our example with proper error handling."""
    fixed_code = '''#!/usr/bin/env python3
"""Example script with division by zero bugs FIXED."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers safely."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average

def calculate_ratio(a, b):
    """Calculate the ratio of a to b safely."""
    if b == 0:
        raise ValueError("Denominator cannot be zero")
    return a / b

def safe_divide(numerator, denominator, default=0.0):
    """Safe division with default value."""
    if denominator == 0:
        return default
    return numerator / denominator

def process_user_input():
    """Process user input safely."""
    print("Enter numbers separated by spaces (or leave empty):")
    user_input = input().strip()
    
    if user_input == "":
        numbers = []
    else:
        numbers = [float(x) for x in user_input.split()]
    
    try:
        avg = calculate_average(numbers)
        print(f"The average is: {avg}")
        return avg
    except ValueError as e:
        print(f"Error: {e}")
        return None

def main():
    """Main function to demonstrate fixed code."""
    print("=== Division by Zero Bug FIXED Demo ===")
    
    # Direct call with empty list - now handled
    print("\n1. Direct call with empty list:")
    try:
        result = calculate_average([])
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Handled gracefully: {e}")
    
    # Division by zero in ratio calculation - now handled
    print("\n2. Ratio calculation with zero denominator:")
    try:
        ratio = calculate_ratio(10, 0)
        print(f"Ratio: {ratio}")
    except ValueError as e:
        print(f"Handled gracefully: {e}")
    
    # Safe division with default
    print("\n3. Safe division with default value:")
    result = safe_divide(10, 0, default=float('inf'))
    print(f"10 / 0 (with default=inf): {result}")
    
    result = safe_divide(10, 0, default=0)
    print(f"10 / 0 (with default=0): {result}")
    
    result = safe_divide(10, 5, default=0)
    print(f"10 / 5 (with default=0): {result}")
    
    print("\n=== End of Fixed Demo ===")

if __name__ == "__main__":
    main()
'''
    
    with open('division_bug_fixed_example.py', 'w') as f:
        f.write(fixed_code)
    
    return 'division_bug_fixed_example.py'

def main():
    """Main function."""
    print("Creating fixed version of division bug example...")
    fixed_file = create_safe_division_fixed_version()
    print(f"Created: {fixed_file}")
    
    print("\nRunning fixed version...")
    print("=" * 50)
    
    # Run the fixed version
    result = bash(f"python3 {fixed_file}")
    print(result)
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("1. Created buggy script with division by zero (division_bug_example2.py)")
    print("2. Created bug finder to detect division bugs (find_division_bugs.py)")
    print("3. Created fixed version with proper error handling (division_bug_fixed_example.py)")
    print("\nThe fix includes:")
    print("  - Input validation before division")
    print("  - Custom exceptions for clear error messages")
    print("  - Safe division function with default return value")
    print("  - Try-except blocks for graceful error handling")

def bash(command):
    """Helper to run shell command."""
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + (result.stderr if result.stderr else "")
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    main()