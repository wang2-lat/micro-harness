#!/usr/bin/env python3
"""Find division by zero bugs in Python code."""

import ast
import sys

class DivisionBugFinder(ast.NodeVisitor):
    """AST visitor to find potential division by zero bugs."""
    
    def __init__(self):
        self.bugs = []
        self.current_file = ""
    
    def visit_BinOp(self, node):
        """Check binary operations for division by zero."""
        if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            # Check if right operand could be zero
            if self._could_be_zero(node.right):
                self.bugs.append({
                    'file': self.current_file,
                    'line': node.lineno,
                    'col': node.col_offset,
                    'operation': ast.unparse(node) if hasattr(ast, 'unparse') else "division",
                    'right_operand': ast.unparse(node.right) if hasattr(ast, 'unparse') else str(node.right)
                })
        
        self.generic_visit(node)
    
    def _could_be_zero(self, node):
        """Check if an AST node could evaluate to zero."""
        # Check for literal zero
        if isinstance(node, ast.Constant):
            return node.value == 0
        
        # Check for variable named zero, len() of something, etc.
        if isinstance(node, ast.Name):
            return node.id in ['zero', 'count', 'n', 'size', 'length']
        
        # Check for function call that could return zero (like len())
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == 'len':
                    return True
        
        # Check for subtraction that could result in zero
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Sub):
                return True
        
        return False
    
    def find_bugs(self, filepath):
        """Find bugs in a file."""
        self.current_file = filepath
        self.bugs = []
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            self.visit(tree)
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
        
        return self.bugs

def main():
    """Main function to find division bugs."""
    if len(sys.argv) < 2:
        print("Usage: python find_division_bugs.py <file1.py> [file2.py ...]")
        sys.exit(1)
    
    finder = DivisionBugFinder()
    
    for filepath in sys.argv[1:]:
        print(f"\nChecking {filepath}...")
        bugs = finder.find_bugs(filepath)
        
        if bugs:
            print(f"Found {len(bugs)} potential division by zero bug(s):")
            for bug in bugs:
                print(f"  Line {bug['line']}, Col {bug['col']}: {bug['operation']}")
                print(f"    Right operand: {bug['right_operand']}")
        else:
            print("No division by zero bugs found.")

if __name__ == "__main__":
    main()