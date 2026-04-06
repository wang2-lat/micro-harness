#!/usr/bin/env python3
"""Fix division by zero bugs in Python code."""

import ast
import sys

class DivisionBugFixer(ast.NodeTransformer):
    """AST transformer to fix division by zero bugs."""
    
    def __init__(self):
        self.fixes_applied = 0
    
    def visit_BinOp(self, node):
        """Fix division operations by adding zero check."""
        if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            # Check if right operand is a variable that could be zero
            if isinstance(node.right, ast.Name):
                # Create a ternary operator: right if right != 0 else 1
                # Actually, better to wrap the division in a try-except or conditional
                # Let's create a safe division function call
                
                # Create: safe_divide(total, count)
                safe_call = ast.Call(
                    func=ast.Name(id='safe_divide', ctx=ast.Load()),
                    args=[node.left, node.right],
                    keywords=[]
                )
                
                self.fixes_applied += 1
                return safe_call
        
        return self.generic_visit(node)

def add_safe_divide_function(tree):
    """Add safe_divide function to the AST."""
    
    # Create safe_divide function
    safe_divide_func = ast.FunctionDef(
        name='safe_divide',
        args=ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(arg='numerator'),
                ast.arg(arg='denominator')
            ],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[]
        ),
        body=[
            ast.If(
                test=ast.Compare(
                    left=ast.Name(id='denominator', ctx=ast.Load()),
                    ops=[ast.NotEq()],
                    comparators=[ast.Constant(value=0)]
                ),
                body=[
                    ast.Return(
                        value=ast.BinOp(
                            left=ast.Name(id='numerator', ctx=ast.Load()),
                            op=ast.Div(),
                            right=ast.Name(id='denominator', ctx=ast.Load())
                        )
                    )
                ],
                orelse=[
                    ast.Return(
                        value=ast.Constant(value=0.0)
                    )
                ]
            )
        ],
        decorator_list=[]
    )
    
    # Insert at the beginning of the module
    tree.body.insert(0, safe_divide_func)
    return tree

def fix_file(filepath):
    """Fix division bugs in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Add safe_divide function
        tree = add_safe_divide_function(tree)
        
        # Fix division operations
        fixer = DivisionBugFixer()
        fixed_tree = fixer.visit(tree)
        ast.fix_missing_locations(fixed_tree)
        
        # Generate fixed code
        if hasattr(ast, 'unparse'):
            fixed_code = ast.unparse(fixed_tree)
        else:
            # Fallback for older Python versions
            import astor
            fixed_code = astor.to_source(fixed_tree)
        
        # Write fixed file
        fixed_filepath = filepath.replace('.py', '_fixed.py')
        with open(fixed_filepath, 'w') as f:
            f.write(fixed_code)
        
        print(f"Applied {fixer.fixes_applied} fix(es)")
        print(f"Fixed file saved as: {fixed_filepath}")
        
        return fixed_filepath
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return None

def main():
    """Main function to fix division bugs."""
    if len(sys.argv) < 2:
        print("Usage: python fix_division_bugs.py <file1.py> [file2.py ...]")
        sys.exit(1)
    
    for filepath in sys.argv[1:]:
        print(f"\nFixing {filepath}...")
        fixed_file = fix_file(filepath)
        
        if fixed_file:
            print(f"Successfully fixed {filepath}")

if __name__ == "__main__":
    main()