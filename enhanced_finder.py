#!/usr/bin/env python3
"""Enhanced bug finder that checks for guard conditions."""

import ast
import sys

class EnhancedDivisionFinder(ast.NodeVisitor):
    """AST visitor to find division by zero with basic guard checking."""
    
    def __init__(self):
        self.bugs = []
        self.guarded_vars = set()
    
    def visit_If(self, node):
        """Check if statements for variable guards."""
        # Check if this is a guard for a variable
        if isinstance(node.test, ast.Compare):
            # Check for comparisons like x == 0 or x != 0
            left = node.test.left
            ops = node.test.ops
            comparators = node.test.comparators
            
            for i, op in enumerate(ops):
                if isinstance(op, ast.Eq) or isinstance(op, ast.NotEq):
                    comparator = comparators[i]
                    if isinstance(comparator, ast.Constant) and comparator.value == 0:
                        if isinstance(left, ast.Name):
                            # This variable is being checked against zero
                            var_name = left.id
                            # Store that this variable is guarded in this branch
                            # Note: This is simplified - real analysis would track scope
                            self.guarded_vars.add(var_name)
        
        self.generic_visit(node)
    
    def visit_BinOp(self, node):
        """Check binary operations for division by zero."""
        if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            divisor = node.right
            
            # Check if divisor is a constant zero
            if isinstance(divisor, ast.Constant) and divisor.value == 0:
                self.bugs.append({
                    'line': node.lineno,
                    'col': node.col_offset,
                    'severity': 'CRITICAL',
                    'message': f"Division by literal zero at line {node.lineno}"
                })
            
            # Check if divisor is a variable
            elif isinstance(divisor, ast.Name):
                var_name = divisor.id
                
                # Check if this variable is guarded against zero
                if var_name in self.guarded_vars:
                    self.bugs.append({
                        'line': node.lineno,
                        'col': node.col_offset,
                        'severity': 'LOW',
                        'message': f"Division by variable '{var_name}' at line {node.lineno} - appears to be guarded"
                    })
                else:
                    self.bugs.append({
                        'line': node.lineno,
                        'col': node.col_offset,
                        'severity': 'HIGH',
                        'message': f"Division by variable '{var_name}' at line {node.lineno} - could be zero (no guard found)"
                    })
        
        self.generic_visit(node)

def analyze_file_enhanced(filename):
    """Analyze a file with enhanced detection."""
    print(f"Enhanced analysis of {filename} for division by zero bugs...")
    print("=" * 60)
    
    try:
        with open(filename, 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        finder = EnhancedDivisionFinder()
        finder.visit(tree)
        
        bugs = finder.bugs
        
        if not bugs:
            print("No division by zero bugs found.")
            return
        
        print(f"Found {len(bugs)} potential division by zero issue(s):")
        print()
        
        # Read the file to show context
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'LOW': 2}
        bugs.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        for bug in bugs:
            line_num = bug['line']
            col = bug['col']
            severity = bug['severity']
            message = bug['message']
            
            print(f"[{severity}] Line {line_num}, Column {col}: {message}")
            
            # Show the line with context
            start = max(0, line_num - 2)
            end = min(len(lines), line_num + 1)
            
            for i in range(start, end):
                prefix = ">>> " if i + 1 == line_num else "    "
                print(f"{prefix}{i+1:3d}: {lines[i].rstrip()}")
            
            print()
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except SyntaxError as e:
        print(f"Error: Syntax error in '{filename}': {e}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python enhanced_finder.py <filename>")
        print("Example: python enhanced_finder.py division_bug_example.py")
        sys.exit(1)
    
    filename = sys.argv[1]
    analyze_file_enhanced(filename)

if __name__ == "__main__":
    main()