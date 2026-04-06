#!/usr/bin/env python3
"""A script with a division by zero bug."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    # Fix: check for empty list before division
    if count == 0:
        return 0.0  # Return 0 for empty list, or could raise an exception
    average = total / count
    return average

def process_data(data_sets):
    """Process multiple data sets and calculate averages."""
    results = []
    for data in data_sets:
        avg = calculate_average(data)
        results.append(avg)
    return results

def main():
    """Main function with test cases."""
    print("Testing average calculation...")
    
    # Test case 1: Normal case
    test1 = [1, 2, 3, 4, 5]
    print(f"Average of {test1}: {calculate_average(test1)}")
    
    # Test case 2: Empty list - THIS WILL CAUSE DIVISION BY ZERO
    test2 = []
    print(f"Average of {test2}: {calculate_average(test2)}")
    
    # Test case 3: Another normal case
    test3 = [10, 20, 30]
    print(f"Average of {test3}: {calculate_average(test3)}")
    
    # Test processing multiple data sets
    data_sets = [[1, 2, 3], [], [4, 5, 6]]
    print(f"\nProcessing data sets: {data_sets}")
    print(f"Results: {process_data(data_sets)}")

if __name__ == "__main__":
    main()