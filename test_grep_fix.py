#!/usr/bin/env python3
"""Test the tool_grep error handling fix."""
import sys
sys.path.insert(0, 'src')
from harness import tool_grep

def test_cases():
    print("=== Testing tool_grep error handling ===\n")
    
    # Test 1: Normal successful grep
    print("1. Normal grep (should show matches):")
    result = tool_grep('def tool_', 'src/harness.py')
    print(f"   Result: {result[:100]}..." if len(result) > 100 else f"   Result: {result}")
    print()
    
    # Test 2: No matches
    print("2. No matches (should show '(no matches)'):")
    result = tool_grep('nonexistentpatternxyz123', 'src/harness.py')
    print(f"   Result: {result}")
    print()
    
    # Test 3: Invalid regex pattern
    print("3. Invalid regex pattern (should show ERROR):")
    result = tool_grep('def[', 'src/harness.py')
    print(f"   Result: {result}")
    print()
    
    # Test 4: Invalid path
    print("4. Invalid path (should show ERROR):")
    result = tool_grep('def', '/nonexistent/path/that/does/not/exist')
    print(f"   Result: {result}")
    print()
    
    # Test 5: Valid glob pattern
    print("5. Valid glob pattern (should show matches):")
    result = tool_grep('import', '.', glob='*.py')
    print(f"   Result: {result[:100]}..." if len(result) > 100 else f"   Result: {result[:200]}")
    print()
    
    # Test 6: Empty pattern (should match everything)
    print("6. Empty pattern (should match all lines):")
    result = tool_grep('', 'src/harness.py')
    print(f"   Result length: {len(result)} chars")
    print(f"   First 100 chars: {result[:100]}...")
    print()
    
    print("=== All tests completed ===")

if __name__ == '__main__':
    test_cases()