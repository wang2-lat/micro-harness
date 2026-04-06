#!/usr/bin/env python3
"""Quick test of all tools after fixes."""
import sys
sys.path.insert(0, 'src')
from harness import tool_read, tool_write, tool_edit, tool_bash, tool_grep, tool_tree

def test_all_tools():
    print("=== Testing all tools ===\n")
    
    # Test tool_read
    print("1. Testing tool_read...")
    result = tool_read("src/harness.py", start_line=1, limit=5)
    print(f"   First 5 lines of harness.py: {len(result.splitlines())} lines")
    
    # Test tool_grep
    print("\n2. Testing tool_grep...")
    result = tool_grep("def tool_grep", "src/harness.py")
    print(f"   Found 'def tool_grep': {len(result.splitlines())} line(s)")
    
    # Test tool_bash
    print("\n3. Testing tool_bash...")
    result = tool_bash("echo 'test'")
    print(f"   echo 'test': {result[:50]}...")
    
    # Test tool_tree
    print("\n4. Testing tool_tree...")
    result = tool_tree(".", max_depth=1)
    print(f"   tree . max_depth=1: {len(result.splitlines())} lines")
    
    # Test error cases
    print("\n5. Testing error cases...")
    result = tool_grep("[invalid", ".")
    print(f"   Invalid regex: {result.startswith('ERROR:')}")
    
    result = tool_read("/nonexistent/file/12345")
    print(f"   Non-existent file: {result.startswith('ERROR:')}")
    
    print("\n=== All tools tested ===")

if __name__ == '__main__':
    test_all_tools()