#!/usr/bin/env python3
"""Find and fix division by zero bugs in Python scripts."""

import ast
import sys

def find_division_bugs(filename):
    """Find division by zero bugs in a Python file."""
    with open(filename, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    bugs = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            # Found a division operation
            lineno = node.lineno
            col_offset = node.col_offset
            
            # Get the line of code
            lines = content.split('\n')
            if lineno <= len(lines):
                line = lines[lineno - 1]
                bugs.append({
                    'line': lineno,
                    'col': col_offset,
                    'code': line.strip(),
                    'divisor': ast.unparse(node.right) if hasattr(ast, 'unparse') else 'unknown'
                })
    
    return bugs

def fix_division_bug(filename):
    """Fix division by zero bugs in a Python file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Read the original file to understand the bug
    with open(filename, 'r') as f:
        content = f.read()
    
    # Find the buggy line
    for i, line in enumerate(lines):
        if '100 / data' in line:
            print(f"Found bug at line {i+1}: {line.strip()}")
            
            # Fix the bug by adding a check for zero
            old_line = line
            new_line = line.replace(
                'value = 100 / data',
                'value = 100 / data if data != 0 else float("inf")'
            )
            
            # Apply the fix
            lines[i] = new_line
            
            # Write the fixed file
            with open(filename, 'w') as f:
                f.writelines(lines)
            
            print(f"Fixed line {i+1}: {new_line.strip()}")
            return True
    
    return False

def main():
    """Main function to find and fix division by zero bugs."""
    if len(sys.argv) < 2:
        print("Usage: python find_fix_bug.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    print(f"Analyzing {filename} for division by zero bugs...")
    
    # Find bugs
    bugs = find_division_bugs(filename)
    
    if bugs:
        print(f"\nFound {len(bugs)} potential division by zero bug(s):")
        for i, bug in enumerate(bugs, 1):
            print(f"{i}. Line {bug['line']}: {bug['code']}")
            print(f"   Divisor: {bug['divisor']}")
    else:
        print("No division by zero bugs found.")
    
    # Fix the bug
    print(f"\nAttempting to fix bugs in {filename}...")
    if fix_division_bug(filename):
        print("Bug fixed successfully!")
        
        # Verify the fix
        print("\nVerifying the fix by running the script...")
        try:
            import subprocess
            result = subprocess.run(['python3', filename], 
                                  capture_output=True, text=True)
            print("Output:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
        except Exception as e:
            print(f"Error running script: {e}")
    else:
        print("No bug found to fix.")

if __name__ == "__main__":
    main()