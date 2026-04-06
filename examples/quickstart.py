#!/usr/bin/env python3
"""MicroHarness Quickstart - How to use in 10 lines of code."""
import sys; sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

# 1. Import
from harness import MicroHarness, HarnessConfig
# 2. Configure (optional)
config = HarnessConfig(verbose=True)
# 3. Create harness
harness = MicroHarness(config)
# 4. Run a task
result = harness.run("Create hello.txt with 'Hello from MicroHarness!'")
# 5. Check result
print(f"Success: {result.success}")
print(f"Turns: {result.turns}")
print(f"Tokens: {result.total_tokens}")
if result.success:
    with open('hello.txt') as f:
        print(f"Created: {f.read()}")