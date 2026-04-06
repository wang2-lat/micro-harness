import sys
sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

# Temporarily revert to original implementation to test
import itertools

def original_tool_read(path: str, start_line: int = 1, limit: int = 500) -> str:
    """Original implementation for comparison"""
    from pathlib import Path
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: File not found: {path}"
    try:
        lines = p.read_text().splitlines()
    except Exception as e:
        return f"ERROR: {e}"
    end = min(start_line - 1 + limit, len(lines))
    numbered = [f"{i+1:5}→{lines[i]}" for i in range(start_line - 1, end)]
    return "\n".join(numbered) if numbered else "(empty file)"

# Test with a small file
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    for i in range(1, 6):
        f.write(f"Line {i}\n")

print("Testing original implementation with start_line=0:")
result = original_tool_read(f.name, start_line=0, limit=3)
print(f"Result: '{result}'")

print("\nTesting original implementation with start_line=1:")
result = original_tool_read(f.name, start_line=1, limit=3)
print(f"Result: '{result}'")

os.unlink(f.name)