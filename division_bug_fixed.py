#!/usr/bin/env python3
"""Fixed version of the script with division by zero bugs resolved."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:  # Handle empty list
        return 0  # Or raise an exception, or return None
    
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average

def process_data(data_list):
    """Process a list of data items."""
    results = []
    for data in data_list:
        # Simulate some processing
        processed_value = data * 2
        
        # FIX: Check for zero before division
        if processed_value == 0:
            # Handle the zero case - could use a default value or skip
            normalized = float('inf')  # Or 0, or None, depending on requirements
        else:
            normalized = 100 / processed_value
        
        results.append(normalized)
    return results

def find_max_ratio(values):
    """Find the maximum ratio between consecutive values."""
    if len(values) < 2:
        return 0
    
    max_ratio = 0
    for i in range(len(values) - 1):
        # FIX: Check for zero denominator
        if values[i+1] == 0:
            # Handle division by zero - could skip or use a special value
            # For this example, we'll skip zero denominators
            continue
        
        ratio = values[i] / values[i+1]
        if ratio > max_ratio:
            max_ratio = ratio
    
    return max_ratio

def main():
    """Main function demonstrating the fixes."""
    print("Testing calculate_average function (FIXED):")
    
    # Test case 1: Normal case
    numbers1 = [10, 20, 30, 40, 50]
    avg1 = calculate_average(numbers1)
    print(f"Average of {numbers1}: {avg1}")
    
    # Test case 2: Empty list - now handled
    numbers2 = []
    avg2 = calculate_average(numbers2)
    print(f"Average of empty list: {avg2}")
    
    print("\nTesting process_data function (FIXED):")
    
    # Test case 3: Normal case
    data1 = [1, 2, 3, 4, 5]
    results1 = process_data(data1)
    print(f"Processed {data1}: {results1}")
    
    # Test case 4: Contains zero - now handled
    data2 = [0, 1, 2, 3]
    results2 = process_data(data2)
    print(f"Processed {data2}: {results2}")
    
    print("\nTesting find_max_ratio function (FIXED):")
    
    # Test case 5: Normal case
    values1 = [10, 5, 20, 4, 30]
    ratio1 = find_max_ratio(values1)
    print(f"Max ratio in {values1}: {ratio1}")
    
    # Test case 6: Contains zero - now handled
    values2 = [10, 0, 5, 2]
    ratio2 = find_max_ratio(values2)
    print(f"Max ratio in {values2}: {ratio2}")
    
    # Test case 7: All zeros edge case
    values3 = [0, 0, 0, 0]
    ratio3 = find_max_ratio(values3)
    print(f"Max ratio in {values3}: {ratio3}")

if __name__ == "__main__":
    main()