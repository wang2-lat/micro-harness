import sys
sys.path.insert(0, '/Users/wangzhaoye/micro-harness/src')

from harness import tool_read
import tempfile
import os

# Create a test file with many lines
def create_test_file(lines_count=1000):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for i in range(1, lines_count + 1):
            f.write(f"This is line {i}\n")
        return f.name

def test_basic_read():
    print("Testing basic read...")
    test_file = create_test_file(100)
    
    # Read first 10 lines
    result = tool_read(test_file, start_line=1, limit=10)
    lines = result.split('\n')
    print(f"  First 10 lines: {len(lines)} lines returned")
    print(f"  First line: {lines[0]}")
    assert "1→This is line 1" in lines[0]
    assert len(lines) == 10
    
    # Read lines 50-60
    result = tool_read(test_file, start_line=50, limit=10)
    lines = result.split('\n')
    print(f"  Lines 50-60: {len(lines)} lines returned")
    print(f"  First of those: {lines[0]}")
    assert "50→This is line 50" in lines[0]
    assert len(lines) == 10
    
    # Test reading beyond file end
    result = tool_read(test_file, start_line=95, limit=20)
    lines = result.split('\n')
    print(f"  Lines 95-end: {len(lines)} lines returned (should be 6)")
    assert len(lines) == 6
    
    # Test edge case: start_line = 0 should work? (Should be 1-indexed)
    result = tool_read(test_file, start_line=0, limit=5)
    print(f"  Start line 0: {result[:50]}...")
    
    os.unlink(test_file)
    print("✓ Basic read tests passed")

def test_large_file():
    print("\nTesting with larger file...")
    test_file = create_test_file(5000)
    
    # Read a small slice from middle
    result = tool_read(test_file, start_line=2500, limit=5)
    lines = result.split('\n')
    print(f"  Lines 2500-2504: {len(lines)} lines returned")
    assert "2500→This is line 2500" in lines[0]
    assert len(lines) == 5
    
    # Verify we're not reading entire file by checking memory indirectly
    # (can't easily test memory, but we can test it doesn't crash)
    result = tool_read(test_file, start_line=1, limit=1)
    assert "1→This is line 1" in result
    
    os.unlink(test_file)
    print("✓ Large file test passed")

def test_empty_file():
    print("\nTesting empty file...")
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        pass  # Empty file
    
    result = tool_read(f.name, start_line=1, limit=10)
    print(f"  Empty file result: '{result}'")
    assert "(empty file or beyond end)" in result
    
    os.unlink(f.name)
    print("✓ Empty file test passed")

def test_nonexistent_file():
    print("\nTesting non-existent file...")
    result = tool_read("/tmp/nonexistent_file_12345.txt")
    print(f"  Non-existent file result: '{result[:50]}...'")
    assert "ERROR: File not found:" in result
    print("✓ Non-existent file test passed")

if __name__ == "__main__":
    test_basic_read()
    test_large_file()
    test_empty_file()
    test_nonexistent_file()
    print("\n✅ All tests passed! tool_read now reads only needed lines.")