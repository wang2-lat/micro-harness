#!/usr/bin/env python3
"""Script with a division by zero bug."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0  # Or float('nan') or raise an exception
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average

def process_data(data_list):
    """Process a list of data items."""
    results = []
    for data in data_list:
        # Bug: This will cause division by zero when data is 0
        value = 100 / data if data != 0 else float("inf")
        results.append(value)
    return results

def analyze_dataset(dataset):
    """Analyze a dataset with various calculations."""
    if not dataset:
        return None
    
    # Calculate statistics
    mean = calculate_average(dataset)
    
    # Process the data
    processed = process_data(dataset)
    
    # More calculations that could cause issues
    ratios = []
    for i in range(len(dataset)):
        # Another potential division by zero
        if i > 0:
            ratio = dataset[i] / dataset[i-1] if dataset[i-1] != 0 else float("inf")
        else:
            ratio = 0
        ratios.append(ratio)
    
    return {
        'mean': mean,
        'processed': processed,
        'ratios': ratios
    }

def main():
    """Main function to demonstrate the bug."""
    print("Testing division by zero bug...")
    
    # Test case 1: Normal case
    print("\nTest 1: Normal dataset")
    data1 = [10, 20, 30, 40, 50]
    result1 = analyze_dataset(data1)
    print(f"Result: {result1}")
    
    # Test case 2: Dataset containing zero
    print("\nTest 2: Dataset with zero (will cause division by zero)")
    data2 = [5, 0, 15, 25, 35]
    try:
        result2 = analyze_dataset(data2)
        print(f"Result: {result2}")
    except ZeroDivisionError as e:
        print(f"Error: {e}")
    
    # Test case 3: Empty dataset
    print("\nTest 3: Empty dataset")
    data3 = []
    result3 = analyze_dataset(data3)
    print(f"Result: {result3}")
    
    # Test case 4: Single zero element
    print("\nTest 4: Single zero element")
    data4 = [0]
    try:
        result4 = analyze_dataset(data4)
        print(f"Result: {result4}")
    except ZeroDivisionError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()