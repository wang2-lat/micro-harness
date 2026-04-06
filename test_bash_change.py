import sys
sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

from harness import tool_bash

# Test successful command
print("Test 1: Successful command (exit=0):")
result1 = tool_bash("echo 'test output'")
print(result1)
print("\n---\n")

# Test failing command
print("Test 2: Failing command (exit=1):")
result2 = tool_bash("false")
print(result2)
print("\n---\n")

# Test command with stderr
print("Test 3: Command with stderr (exit=1):")
result3 = tool_bash("ls /nonexistent/directory")
print(result3)
print("\n---\n")

# Test command with exit code 127 (command not found)
print("Test 4: Command not found (exit=127):")
result4 = tool_bash("nonexistentcommand123")
print(result4)