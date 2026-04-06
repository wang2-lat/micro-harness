#!/usr/bin/env python3
"""A script with a division by zero bug - FIXED VERSION."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    
    # FIX: Check for zero before division
    if count == 0:
        return 0.0  # Or return None, or raise an exception
    
    average = total / count
    return average

def process_data(data):
    """Process data and calculate statistics."""
    results = []
    
    for item in data:
        # Extract values from item
        values = item.get('values', [])
        
        # Calculate average - FIXED: handle empty list
        avg = calculate_average(values)
        
        # Store result
        results.append({
            'id': item['id'],
            'average': avg,
            'count': len(values)
        })
    
    return results

def main():
    """Main function with test data."""
    # Test data including an empty values list
    test_data = [
        {'id': 1, 'values': [10, 20, 30]},
        {'id': 2, 'values': [5, 15, 25, 35]},
        {'id': 3, 'values': []},  # This will now return 0.0 instead of crashing
        {'id': 4, 'values': [100]},
    ]
    
    print("Processing data...")
    try:
        results = process_data(test_data)
        for result in results:
            print(f"ID: {result['id']}, Average: {result['average']:.2f}, Count: {result['count']}")
    except Exception as e:
        print(f"Error: {e}")
        print("Division by zero bug occurred!")

if __name__ == "__main__":
    main()