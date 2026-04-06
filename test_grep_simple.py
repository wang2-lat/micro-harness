#!/usr/bin/env python3
"""Test harness with grep error - simpler version."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the tool execution directly
print("Testing tool_grep directly...")
from src.harness import tool_grep, TOOL_DISPATCH

# Test 1: Direct call
result = tool_grep("test", ".", "*.py")
print(f"Result: {result!r}")
print(f"Starts with ERROR:: {result.startswith('ERROR:')}")
print(f"Type of result: {type(result)}")

# Test 2: Through dispatch
print("\nTesting through TOOL_DISPATCH...")
fn = TOOL_DISPATCH["grep"]
result2 = fn(pattern="test", path=".", glob="*.py")
print(f"Result: {result2!r}")
print(f"Starts with ERROR:: {result2.startswith('ERROR:')}")

# Test 3: Simulate agent loop logic
print("\nSimulating agent loop logic...")
result_str = str(result2)[:8000]  # max_tool_output default
is_error = result_str.startswith("ERROR:")
print(f"result_str: {result_str!r}")
print(f"is_error: {is_error}")

# Test 4: Check all error messages from tools
print("\nChecking all tool error messages...")
from src.harness import tool_read, tool_write, tool_edit, tool_bash, tool_tree

# Simulate errors
test_cases = [
    ("tool_read", lambda: tool_read("/nonexistent/file.txt")),
    ("tool_edit", lambda: tool_edit("/nonexistent/file.txt", "old", "new")),
    ("tool_bash", lambda: tool_bash("sleep 100", timeout=0.1)),  # Should timeout
    ("tool_grep", lambda: tool_grep("test")),  # ripgrep not installed
    ("tool_tree", lambda: tool_tree("/nonexistent/path")),
]

for name, func in test_cases:
    try:
        result = func()
        print(f"{name:20} -> {result!r}")
        print(f"  Starts with ERROR:: {result.startswith('ERROR:')}")
    except Exception as e:
        print(f"{name:20} -> Exception: {e}")