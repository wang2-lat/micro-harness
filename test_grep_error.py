#!/usr/bin/env python3
"""Test the grep error handling bug."""
import subprocess
import sys

# Simulate the tool_grep function
def tool_grep(pattern: str, path: str = ".", glob: str | None = None) -> str:
    cmd = ["rg", "-n", pattern, path]
    if glob:
        cmd.extend(["-g", glob])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = result.stdout[:4000]
        return out if out else "(no matches)"
    except FileNotFoundError:
        return "ERROR: ripgrep (rg) not installed"
    except subprocess.TimeoutExpired:
        return "ERROR: grep timeout"

# Test the error detection logic
def test_error_detection():
    # Simulate what happens in the agent loop
    result = tool_grep("test", ".", "*.py")
    result_str = str(result)[:8000]  # max_tool_output
    is_error = result_str.startswith("ERROR:")
    
    print(f"Result: {result!r}")
    print(f"Result string: {result_str!r}")
    print(f"Starts with 'ERROR:': {result_str.startswith('ERROR:')}")
    print(f"is_error flag would be: {is_error}")
    
    # Also test other error cases
    print("\n--- Testing other error formats ---")
    test_cases = [
        "ERROR: ripgrep (rg) not installed",
        "ERROR: grep timeout",
        "ERROR: File not found: test.txt",
        "ERROR: old_string not found in file",
        "ERROR: command timed out after 30s",
        "ERROR: some other error",
        "Error: lowercase error",  # This wouldn't be caught!
        "error: all lowercase",  # This wouldn't be caught!
    ]
    
    for test in test_cases:
        is_err = test.startswith("ERROR:")
        print(f"{test!r:50} -> starts with 'ERROR:': {is_err}")

if __name__ == "__main__":
    test_error_detection()