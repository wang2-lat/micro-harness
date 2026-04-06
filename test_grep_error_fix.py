#!/usr/bin/env python3
"""Test to verify grep error handling sets is_error flag correctly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harness import MicroHarness, HarnessConfig
import json

def test_grep_error():
    """Test that grep errors set is_error flag."""
    print("Testing grep error handling...")
    
    # Create a minimal test
    config = HarnessConfig(
        max_turns=2,
        verbose=False,
        critic_mode="off"
    )
    
    harness = MicroHarness(config)
    
    # We need to mock the API call since we don't have Anthropic API key
    # Instead, let's directly test the tool_grep function
    from harness import tool_grep
    
    print("\n1. Testing tool_grep directly:")
    result = tool_grep("test", ".")
    print(f"   Result: {result[:100]}")
    print(f"   Starts with ERROR?: {result.startswith('ERROR:')}")
    
    # Now let's trace through what happens in the actual execution
    print("\n2. Simulating what happens in run() method:")
    
    # Simulate the logic from lines 533-545
    result_str = str(result)[:8000]  # max_tool_output default
    is_error = result_str.startswith("ERROR:")
    
    print(f"   result_str: {result_str[:100]}")
    print(f"   is_error calculated: {is_error}")
    
    tool_result = {
        "type": "tool_result",
        "tool_use_id": "test-id",
        "content": result_str,
        "is_error": is_error,
    }
    
    print(f"   tool_result['is_error']: {tool_result['is_error']}")
    
    if is_error:
        print("   ✓ is_error is correctly set to True for grep errors")
    else:
        print("   ✗ is_error is NOT set correctly for grep errors")
    
    # Also test other tools for comparison
    print("\n3. Testing other tools for comparison:")
    from harness import tool_read, tool_edit, tool_tree
    
    # Test tool_read with non-existent file
    read_result = tool_read("/non/existent/file.txt")
    print(f"   tool_read error: {read_result[:50]}")
    print(f"   Starts with ERROR?: {read_result.startswith('ERROR:')}")
    
    # Test tool_edit with non-existent file  
    edit_result = tool_edit("/non/existent/file.txt", "old", "new")
    print(f"   tool_edit error: {edit_result[:50]}")
    print(f"   Starts with ERROR?: {edit_result.startswith('ERROR:')}")
    
    # Test tool_tree with non-existent path
    tree_result = tool_tree("/non/existent/path")
    print(f"   tool_tree error: {tree_result[:50]}")
    print(f"   Starts with ERROR?: {tree_result.startswith('ERROR:')}")

if __name__ == "__main__":
    test_grep_error()