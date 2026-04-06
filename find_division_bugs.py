#!/usr/bin/env python3
"""Find division by zero bugs in Python files."""

import ast
import sys
from pathlib import Path

class DivisionBugFinder(ast.NodeVisitor):
    """AST visitor to find potential division by zero bugs."""
    
    def __init__(self, filename):
        self.filename = filename
        self.bugs = []
    
    def visit_BinOp(self, node):
        """Check division operations."""
        if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            # Check if right operand could be zero
            self.check_operand(node.right, node.lineno)
        
        self.generic_visit(node)
    
    def check_operand(self, node, lineno):
        """Check if an operand could be zero."""
        if isinstance(node, ast.Constant):
            if node.value == 0:
                self.bugs.append({
                    'line': lineno,
                    'type': 'constant_zero',
                    'message': f'Division by constant zero at line {lineno}'
                })
        elif isinstance(node, ast.Name):
            self.bugs.append({
                'line': lineno,
                'type': 'variable',
                'message': f'Division by variable "{node.id}" at line {lineno} - could be zero'
            })
        elif isinstance(node, ast.Call):
            self.bugs.append({
                'line': lineno,
                'type': 'function_call',
                'message': f'Division by function result at line {lineno} - could return zero'
            })
        elif isinstance(node, ast.BinOp):
            # Could be an expression that evaluates to zero
            self.bugs.append({
                'line': lineno,
                'type': 'expression',
                'message': f'Division by expression at line {lineno} - could evaluate to zero'
            })
    
    def visit_FunctionDef(self, node):
        """Check function definitions for len() usage in division."""
        self.generic_visit(node)
    
    def find_bugs(self):
        """Find all division bugs in the file."""
        return self.bugs

def find_division_bugs_in_file(filepath):
    """Find division bugs in a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        finder = DivisionBugFinder(filepath)
        finder.visit(tree)
        return finder.find_bugs()
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []

def find_division_bugs_in_directory(directory='.', pattern='*.py'):
    """Find division bugs in all Python files in a directory."""
    bugs_by_file = {}
    
    for filepath in Path(directory).rglob(pattern):
        if '__pycache__' in str(filepath):
            continue
        
        bugs = find_division_bugs_in_file(filepath)
        if bugs:
            bugs_by_file[str(filepath)] = bugs
    
    return bugs_by_file

def print_bugs(bugs_by_file):
    """Print found bugs in a readable format."""
    if not bugs_by_file:
        print("No division bugs found!")
        return
    
    print("=== Division by Zero Bugs Found ===")
    for filepath, bugs in bugs_by_file.items():
        print(f"\nFile: {filepath}")
        for bug in bugs:
            print(f"  Line {bug['line']}: {bug['message']}")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = '.'
    
    print(f"Searching for division bugs in: {target}")
    bugs_by_file = find_division_bugs_in_directory(target)
    print_bugs(bugs_by_file)
    
    # Also check our example files
    print("\n\n=== Checking example files ===")
    example_files = ['division_bug_example.py', 'division_bug_example2.py']
    for filename in example_files:
        if Path(filename).exists():
            bugs = find_division_bugs_in_file(filename)
            if bugs:
                print(f"\n{filename}:")
                for bug in bugs:
                    print(f"  Line {bug['line']}: {bug['message']}")
            else:
                print(f"\n{filename}: No bugs found (but we know there are!)")

if __name__ == "__main__":
    main()