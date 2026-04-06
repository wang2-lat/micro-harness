#!/usr/bin/env python3
"""Example script with division by zero bugs FIXED."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers safely."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average

def calculate_ratio(a, b):
    """Calculate the ratio of a to b safely."""
    if b == 0:
        raise ValueError("Denominator cannot be zero")
    return a / b

def safe_divide(numerator, denominator, default=0.0):
    """Safe division with default value."""
    if denominator == 0:
        return default
    return numerator / denominator

def process_user_input():
    """Process user input safely."""
    print("Enter numbers separated by spaces (or leave empty):")
    user_input = input().strip()
    
    if user_input == "":
        numbers = []
    else:
        numbers = [float(x) for x in user_input.split()]
    
    try:
        avg = calculate_average(numbers)
        print(f"The average is: {avg}")
        return avg
    except ValueError as e:
        print(f"Error: {e}")
        return None

def main():
    """Main function to demonstrate fixed code."""
    print("=== Division by Zero Bug FIXED Demo ===")
    
    # Direct call with empty list - now handled
    print("\n1. Direct call with empty list:")
    try:
        result = calculate_average([])
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Handled gracefully: {e}")
    
    # Division by zero in ratio calculation - now handled
    print("\n2. Ratio calculation with zero denominator:")
    try:
        ratio = calculate_ratio(10, 0)
        print(f"Ratio: {ratio}")
    except ValueError as e:
        print(f"Handled gracefully: {e}")
    
    # Safe division with default
    print("\n3. Safe division with default value:")
    result = safe_divide(10, 0, default=float('inf'))
    print(f"10 / 0 (with default=inf): {result}")
    
    result = safe_divide(10, 0, default=0)
    print(f"10 / 0 (with default=0): {result}")
    
    result = safe_divide(10, 5, default=0)
    print(f"10 / 5 (with default=0): {result}")
    
    print("\n=== End of Fixed Demo ===")

if __name__ == "__main__":
    main()