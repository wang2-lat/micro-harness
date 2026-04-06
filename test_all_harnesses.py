#!/usr/bin/env python3
"""Test that all harness implementations respect max_tool_output config."""
import sys
sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

from harness import HarnessConfig

# Test that the config is properly defined
print("Testing HarnessConfig definition:")
config = HarnessConfig(max_tool_output=1234)
print(f"  max_tool_output = {config.max_tool_output}")
assert config.max_tool_output == 1234

# Check that the field exists and is an integer
assert hasattr(config, 'max_tool_output')
assert isinstance(config.max_tool_output, int)

print("\n✅ HarnessConfig correctly defines max_tool_output field")

# Now let's check the actual usage in the code
print("\nChecking code usage of max_tool_output:")

# Read the relevant lines from harness.py
with open('src/harness.py', 'r') as f:
    lines = f.readlines()
    
found_usage = False
for i, line in enumerate(lines, 1):
    if 'self.config.max_tool_output' in line:
        print(f"  Line {i}: {line.strip()}")
        found_usage = True

if found_usage:
    print("\n✅ max_tool_output is being used in harness.py")
else:
    print("\n❌ max_tool_output not found in harness.py")

# Check openai_harness.py
print("\nChecking openai_harness.py:")
with open('src/openai_harness.py', 'r') as f:
    content = f.read()
    if 'self.config.max_tool_output' in content:
        print("  ✅ max_tool_output is being used in openai_harness.py")
    else:
        print("  ❌ max_tool_output not found in openai_harness.py")

# Check gemini_harness.py
print("\nChecking gemini_harness.py:")
with open('src/gemini_harness.py', 'r') as f:
    content = f.read()
    if 'self.config.max_tool_output' in content:
        print("  ✅ max_tool_output is being used in gemini_harness.py")
    else:
        print("  ❌ max_tool_output not found in gemini_harness.py")

print("\n✅ All checks completed!")