#!/usr/bin/env python3
"""Test the tree tool implementation."""

import sys
sys.path.insert(0, 'src')

from harness import tool_tree

print("Testing tree tool...")
print("=" * 60)

# Test 1: Current directory with default max_depth
print("Test 1: Current directory (default max_depth=3)")
result = tool_tree()
print(result)
print()

# Test 2: Current directory with max_depth=1
print("Test 2: Current directory (max_depth=1)")
result = tool_tree(max_depth=1)
print(result)
print()

# Test 3: Current directory with max_depth=2
print("Test 3: Current directory (max_depth=2)")
result = tool_tree(max_depth=2)
print(result)
print()

# Test 4: Test with src directory
print("Test 4: src directory (max_depth=2)")
result = tool_tree("src", max_depth=2)
print(result)
print()

# Test 5: Test non-existent directory
print("Test 5: Non-existent directory")
result = tool_tree("non_existent_dir")
print(result)
print()

# Test 6: Test file instead of directory
print("Test 6: File instead of directory")
result = tool_tree("src/harness.py")
print(result)