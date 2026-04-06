#!/usr/bin/env python3
"""Test the tree tool as requested in the task."""

import sys
sys.path.insert(0, 'src')

from harness import tool_tree

print("Testing tree tool as requested: tool_tree('.', 2)")
print("=" * 60)
result = tool_tree(".", 2)
print(result)
print("=" * 60)
print("Test completed successfully!")