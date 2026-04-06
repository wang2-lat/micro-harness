#!/usr/bin/env python3
"""Test tree tool through the harness system."""

import sys
sys.path.insert(0, 'src')

from harness import MicroHarness

# Create a simple test
harness = MicroHarness()
# We'll just test that the tool is in the dispatch table
from harness import TOOL_DISPATCH

print("Checking if tree tool is in TOOL_DISPATCH...")
if "tree" in TOOL_DISPATCH:
    print("✓ tree tool is in TOOL_DISPATCH")
    print(f"  Function: {TOOL_DISPATCH['tree']}")
else:
    print("✗ tree tool is NOT in TOOL_DISPATCH")

print("\nChecking if tree tool is in TOOLS_SCHEMA...")
from harness import TOOLS_SCHEMA
tree_tools = [t for t in TOOLS_SCHEMA if t["name"] == "tree"]
if tree_tools:
    print(f"✓ tree tool is in TOOLS_SCHEMA")
    print(f"  Description: {tree_tools[0]['description']}")
else:
    print("✗ tree tool is NOT in TOOLS_SCHEMA")

print("\nTesting direct function call...")
from harness import tool_tree
result = tool_tree(".", 2)
print(f"✓ tool_tree('.', 2) returned {len(result.splitlines())} lines")
print("\nFirst 5 lines of output:")
for i, line in enumerate(result.splitlines()[:5]):
    print(f"  {line}")