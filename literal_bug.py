#!/usr/bin/env python3
"""Script with literal division by zero that our tool can find."""

def bad_function():
    """Function with literal division by zero."""
    x = 10
    y = 0
    result = x / y  # This is a literal zero in the division
    return result

def another_bad_one():
    """Another function with division by literal zero."""
    return 100 / 0  # Direct division by literal zero

def main():
    print("This script has literal division by zero bugs!")
    # These would crash if called