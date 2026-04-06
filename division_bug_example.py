#!/usr/bin/env python3
"""Example script with a division by zero bug."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    average = total / count  # Potential division by zero if numbers is empty
    return average

def process_data(data):
    """Process data and calculate statistics."""
    if not data:
        return None
    
    # Calculate various statistics
    avg = calculate_average(data)
    
    # Calculate variance
    variance_sum = sum((x - avg) ** 2 for x in data)
    variance = variance_sum / len(data)  # Another potential division by zero
    
    return {
        'average': avg,
        'variance': variance,
        'count': len(data)
    }

def main():
    """Main function to demonstrate the bug."""
    # Test cases
    test_cases = [
        [1, 2, 3, 4, 5],
        [10, 20, 30],
        [],  # This will cause division by zero!
        [0, 0, 0],  # This is fine - sum is 0, count is 3
    ]
    
    for i, data in enumerate(test_cases):
        print(f"Test case {i+1}: {data}")
        try:
            result = process_data(data)
            if result:
                print(f"  Average: {result['average']}")
                print(f"  Variance: {result['variance']}")
                print(f"  Count: {result['count']}")
            else:
                print("  No data to process")
        except ZeroDivisionError as e:
            print(f"  ERROR: Division by zero! {e}")
        print()

if __name__ == "__main__":
    main()