#!/usr/bin/env python3
"""Example script with a division by zero bug."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    average = total / count  # Division by zero if numbers is empty
    return average

def calculate_ratio(a, b):
    """Calculate the ratio of a to b."""
    return a / b  # Division by zero if b is 0

def process_user_input():
    """Process user input with potential division by zero."""
    print("Enter numbers separated by spaces (or leave empty to trigger bug):")
    user_input = input().strip()
    
    if user_input == "":
        numbers = []
    else:
        numbers = [float(x) for x in user_input.split()]
    
    # This will crash with empty input
    avg = calculate_average(numbers)
    print(f"The average is: {avg}")
    
    return avg

def main():
    """Main function to demonstrate the bug."""
    print("=== Division by Zero Bug Demo ===")
    
    # Direct call that will fail
    print("\n1. Direct call with empty list:")
    try:
        result = calculate_average([])
        print(f"Result: {result}")
    except ZeroDivisionError as e:
        print(f"ERROR: {e}")
    
    # Division by zero in ratio calculation
    print("\n2. Ratio calculation with zero denominator:")
    try:
        ratio = calculate_ratio(10, 0)
        print(f"Ratio: {ratio}")
    except ZeroDivisionError as e:
        print(f"ERROR: {e}")
    
    # Simulated user input
    print("\n3. Simulated user input processing:")
    # We'll simulate the bug by calling with empty list
    try:
        # This simulates what would happen if user enters nothing
        numbers = []
        avg = calculate_average(numbers)
        print(f"Average of empty list: {avg}")
    except ZeroDivisionError as e:
        print(f"ERROR: Cannot calculate average of empty list - {e}")
    
    print("\n=== End of Demo ===")

if __name__ == "__main__":
    main()