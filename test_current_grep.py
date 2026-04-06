#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
from harness import tool_grep

print("=== Testing current tool_grep implementation ===")
print()

# Test 1: Valid grep
print("1. Valid grep:")
result = tool_grep("def tool_grep", "src/harness.py")
print(f"   Result: {result[:100]}...")
print(f"   Starts with ERROR?: {result.startswith('ERROR:')}")
print()

# Test 2: No matches
print("2. No matches:")
result = tool_grep("thisshouldnotmatchanything12345", "src/harness.py")
print(f"   Result: {result}")
print(f"   Starts with ERROR?: {result.startswith('ERROR:')}")
print()

# Test 3: Invalid regex
print("3. Invalid regex:")
result = tool_grep("[invalid", "src/harness.py")
print(f"   Result: {result[:200]}")
print(f"   Starts with ERROR?: {result.startswith('ERROR:')}")
print()

# Test 4: Non-existent path
print("4. Non-existent path:")
result = tool_grep("test", "/nonexistent/path/that/does/not/exist")
print(f"   Result: {result[:200]}")
print(f"   Starts with ERROR?: {result.startswith('ERROR:')}")
print()

# Test 5: What if we simulate ripgrep not installed?
# We can't easily test this, but the code handles FileNotFoundError

print("=== Analysis ===")
print("The function seems to handle errors by returning strings starting with 'ERROR:'")
print("The agent loop checks for 'ERROR:' prefix to set is_error flag")
print("So errors should be properly reported, not silent.")