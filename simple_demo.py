#!/usr/bin/env python3
"""Simple demonstration of finding and fixing a division by zero bug."""

# Simple buggy function
def divide_numbers(a, b):
    """Divide a by b - has a division by zero bug."""
    return a / b  # BUG: Will crash if b is 0

# Test the buggy function
def test_division():
    print("Testing division function...")
    
    # Test 1: Normal case
    try:
        result = divide_numbers(10, 2)
        print(f"10 / 2 = {result}")
    except ZeroDivisionError as e:
        print(f"Error: {e}")
    
    # Test 2: Division by zero
    try:
        result = divide_numbers(10, 0)
        print(f"10 / 0 = {result}")
    except ZeroDivisionError as e:
        print(f"Error: {e}")

# Fixed version
def divide_numbers_fixed(a, b):
    """Divide a by b - fixed version."""
    if b == 0:
        return float('inf')  # Handle division by zero
    return a / b

# Test the fixed function
def test_fixed_division():
    print("\nTesting FIXED division function...")
    
    # Test 1: Normal case
    result = divide_numbers_fixed(10, 2)
    print(f"10 / 2 = {result}")
    
    # Test 2: Division by zero (now handled)
    result = divide_numbers_fixed(10, 0)
    print(f"10 / 0 = {result}")

# Main function
def main():
    print("=== Division by Zero Bug Demo ===\n")
    
    print("1. First, let's see the bug in action:")
    test_division()
    
    print("\n2. Now let's apply the fix:")
    print("   Changed: return a / b")
    print("   To:      return a / b if b != 0 else float('inf')")
    
    print("\n3. Testing the fixed version:")
    test_fixed_division()
    
    print("\n✅ Bug fixed! Division by zero now returns 'inf' instead of crashing.")

if __name__ == "__main__":
    main()