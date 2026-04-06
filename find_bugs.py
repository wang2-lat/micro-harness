#!/usr/bin/env python3
"""Script to find division by zero bugs in Python code."""

import ast
import sys

class DivisionByZeroFinder(ast.NodeVisitor):
    """AST visitor to find potential division by zero bugs."""
    
    def __init__(self):
        self.issues = []
    
    def visit_BinOp(self, node):
        """Check binary operations for division by zero."""
        if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            # Check if right operand could be zero
            if isinstance(node.right, ast.Constant):
                if node.right.value == 0:
                    self.issues.append({
                        'line': node.lineno,
                        'col': node.col_offset,
                        'issue': f"Division by literal zero at line {node.lineno}"
                    })
            # Could add more sophisticated checks here
            # (e.g., checking variable names that might be zero)
        
        self.generic_visit(node)

def find_division_by_zero_bugs(filename):
    """Find potential division by zero bugs in a Python file."""
    try:
        with open(filename, 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        finder = DivisionByZeroFinder()
        finder.visit(tree)
        
        return finder.issues
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return []

def main():
    """Main function to demonstrate bug finding."""
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = ['buggy_division.py']
    
    for filename in files:
        print(f"\nAnalyzing {filename}...")
        issues = find_division_by_zero_bugs(filename)
        
        if issues:
            print(f"Found {len(issues)} potential division by zero issue(s):")
            for issue in issues:
                print(f"  - Line {issue['line']}: {issue['issue']}")
        else:
            print("No obvious division by zero issues found.")
            print("Note: This tool only finds literal zeros. More sophisticated")
            print("      analysis would be needed for variable-based division.")

if __name__ == "__main__":
    main()