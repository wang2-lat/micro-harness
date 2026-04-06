#!/usr/bin/env python3
"""A script with a division by zero bug (original version)."""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    # Bug: division by zero when list is empty
    average = total / count
    return average

def main():
    """Main function."""
    print("This has a division by zero bug!")
    # This would crash: calculate_average([])