#!/usr/bin/env python3
"""Test that tool output truncation is configurable via HarnessConfig."""
import sys
sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

from harness import HarnessConfig, MicroHarness

# Test 1: Default config should have max_tool_output = 8000
config1 = HarnessConfig()
print(f"Test 1 - Default config:")
print(f"  max_tool_output = {config1.max_tool_output}")
assert config1.max_tool_output == 8000, f"Expected 8000, got {config1.max_tool_output}"

# Test 2: Custom config with different value
config2 = HarnessConfig(max_tool_output=100)
print(f"\nTest 2 - Custom config:")
print(f"  max_tool_output = {config2.max_tool_output}")
assert config2.max_tool_output == 100, f"Expected 100, got {config2.max_tool_output}"

# Test 3: Create MicroHarness with custom config
harness = MicroHarness(config2)
print(f"\nTest 3 - MicroHarness with custom config:")
print(f"  harness.config.max_tool_output = {harness.config.max_tool_output}")
assert harness.config.max_tool_output == 100, f"Expected 100, got {harness.config.max_tool_output}"

print("\n✅ All tests passed! Tool output truncation is configurable via HarnessConfig.")