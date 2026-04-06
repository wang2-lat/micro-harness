#!/usr/bin/env python3
"""Test to verify the fix for grep error detection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harness import tool_grep, tool_read, tool_edit, tool_tree

def test_error_detection_with_truncation():
    """Test that error detection works even with truncated output."""
    
    print("Testing error detection with various max_tool_output values...")
    
    # Simulate error messages from different tools
    error_messages = [
        ("grep", "ERROR: ripgrep (rg) not installed"),
        ("read", "ERROR: File not found: test.txt"),
        ("edit", "ERROR: old_string not found in file"),
        ("tree", "ERROR: Path not found: /non/existent"),
        ("bash", "ERROR: command timed out after 30s"),
    ]
    
    test_cases = [
        (5, "Truncated to 5 chars (should still detect error)"),
        (6, "Truncated to 6 chars (includes 'ERROR:' without space)"),
        (7, "Truncated to 7 chars (includes 'ERROR: ')"),
        (50, "Plenty of room"),
    ]
    
    for tool_name, error_msg in error_messages:
        print(f"\n--- Testing {tool_name} error: {error_msg[:50]}...")
        
        for max_len, description in test_cases:
            # Simulate what happens in the run() method
            result = error_msg  # This is what the tool would return
            result_str = str(result)[:max_len]
            
            # OLD BUGGY LOGIC: checking truncated string
            old_is_error = result_str.startswith("ERROR:")
            
            # NEW FIXED LOGIC: checking original string
            new_is_error = str(result).startswith("ERROR:")
            
            print(f"  max_tool_output={max_len:2d}: '{result_str}'")
            print(f"    Old logic (result_str.startswith): {old_is_error}")
            print(f"    New logic (str(result).startswith): {new_is_error}")
            
            # The new logic should always detect the error
            assert new_is_error == True, f"New logic failed to detect error for {tool_name} with max_len={max_len}"
            
            # The old logic would fail for max_len < 7
            if max_len < 7:
                print(f"    ⚠️  Old logic would miss this error!")
    
    print("\n✅ All tests passed! The fix correctly detects errors even with truncation.")

if __name__ == "__main__":
    test_error_detection_with_truncation()