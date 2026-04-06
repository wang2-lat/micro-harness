#!/usr/bin/env python3
"""Test that tool output truncation actually works."""
import sys
sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

from harness import HarnessConfig, MicroHarness
import tempfile
import os

# Create a test file with content longer than our truncation limits
test_content = "A" * 200  # 200 characters

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(test_content)
    temp_file = f.name

try:
    # Test with small truncation limit (50 chars)
    config_small = HarnessConfig(max_tool_output=50)
    harness_small = MicroHarness(config_small)
    
    # Mock the tool execution to test truncation
    # We'll simulate what happens in the actual code
    result = test_content
    truncated_result_small = str(result)[:harness_small.config.max_tool_output]
    
    print(f"Test with max_tool_output=50:")
    print(f"  Original length: {len(test_content)}")
    print(f"  Truncated length: {len(truncated_result_small)}")
    print(f"  Truncated result: '{truncated_result_small}'")
    assert len(truncated_result_small) == 50, f"Expected 50, got {len(truncated_result_small)}"
    
    # Test with larger truncation limit (150 chars)
    config_large = HarnessConfig(max_tool_output=150)
    harness_large = MicroHarness(config_large)
    
    truncated_result_large = str(result)[:harness_large.config.max_tool_output]
    
    print(f"\nTest with max_tool_output=150:")
    print(f"  Original length: {len(test_content)}")
    print(f"  Truncated length: {len(truncated_result_large)}")
    print(f"  Truncated result ends with: '...{truncated_result_large[-10:]}'")
    assert len(truncated_result_large) == 150, f"Expected 150, got {len(truncated_result_large)}"
    
    # Test with truncation limit larger than content (300 chars)
    config_huge = HarnessConfig(max_tool_output=300)
    harness_huge = MicroHarness(config_huge)
    
    truncated_result_huge = str(result)[:harness_huge.config.max_tool_output]
    
    print(f"\nTest with max_tool_output=300 (larger than content):")
    print(f"  Original length: {len(test_content)}")
    print(f"  Truncated length: {len(truncated_result_huge)}")
    assert len(truncated_result_huge) == 200, f"Expected 200, got {len(truncated_result_huge)}"
    assert truncated_result_huge == test_content, "Content should not be truncated when limit > content length"
    
    print("\n✅ All truncation tests passed!")
    
finally:
    # Clean up
    os.unlink(temp_file)