#!/usr/bin/env python3
"""Test the improved error handling in tool_grep function."""
import sys
sys.path.insert(0, 'src')
from harness import tool_grep

def test_grep_error_handling():
    """Test that tool_grep properly handles errors instead of failing silently."""
    print("Testing tool_grep error handling improvements...")
    print()
    
    # Test 1: Invalid regex (previously would return "(no matches)" silently)
    print("Test 1: Invalid regex pattern")
    result = tool_grep("[invalid", ".")
    if result.startswith("ERROR: grep failed:"):
        print("✓ Correctly returns error for invalid regex")
        print(f"  Error message: {result[:100]}...")
    else:
        print(f"✗ Failed: Expected error, got: {result[:100]}...")
    print()
    
    # Test 2: Non-existent path
    print("Test 2: Non-existent path")
    result = tool_grep("test", "/nonexistent/path/that/does/not/exist")
    if result.startswith("ERROR: grep failed:"):
        print("✓ Correctly returns error for non-existent path")
        print(f"  Error message: {result[:100]}...")
    else:
        print(f"✗ Failed: Expected error, got: {result[:100]}...")
    print()
    
    # Test 3: No matches (should return "(no matches)", not an error)
    print("Test 3: No matches (normal case)")
    result = tool_grep("thisshouldnotmatchanything12345", ".")
    if result == "(no matches)":
        print("✓ Correctly returns '(no matches)' for no matches")
    else:
        print(f"✗ Failed: Expected '(no matches)', got: {result[:100]}...")
    print()
    
    # Test 4: Valid grep
    print("Test 4: Valid grep with matches")
    result = tool_grep("def tool_grep", "src/harness.py")
    if "def tool_grep" in result and not result.startswith("ERROR"):
        print("✓ Correctly returns matches for valid grep")
        print(f"  Found {len(result.splitlines())} line(s)")
    else:
        print(f"✗ Failed: Expected matches, got: {result[:100]}...")
    print()
    
    print("All tests completed!")

if __name__ == "__main__":
    test_grep_error_handling()