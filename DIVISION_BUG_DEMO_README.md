# Division by Zero Bug Finding and Fixing Demo

This project demonstrates how to:
1. Create a Python script with division by zero bugs
2. Find these bugs using static analysis
3. Fix the bugs properly
4. Verify the fixes work

## Files Created

1. **`division_bug_example.py`** - Contains 3 division by zero bugs:
   - `calculate_average()` - divides by `len(numbers)` without checking for empty list
   - `process_data()` - divides by `processed_value` without checking for zero
   - `find_max_ratio()` - divides by `values[i+1]` without checking for zero

2. **`find_division_bugs.py`** - Basic bug finder using Python's AST module to detect division operations where the divisor could be zero.

3. **`enhanced_finder.py`** - Enhanced bug finder that attempts to detect guard conditions (if statements checking variables against zero).

4. **`division_bug_fixed.py`** - Fixed version with all bugs resolved:
   - Added check for empty list in `calculate_average()`
   - Added guard for `processed_value == 0` in `process_data()`
   - Added check for zero denominator in `find_max_ratio()`

5. **`test_demo.py`** - Comprehensive test that runs the entire process.

## How to Run

```bash
# Run the buggy script (will show division by zero errors)
python division_bug_example.py

# Find bugs with basic finder
python find_division_bugs.py division_bug_example.py

# Find bugs with enhanced finder
python enhanced_finder.py division_bug_example.py

# Run the fixed script (no errors)
python division_bug_fixed.py

# Run the complete demo
python test_demo.py
```

## Key Learnings

1. **Division by zero is a common bug** that occurs when:
   - Dividing by a variable that could be zero
   - Dividing by the result of a function that could return zero
   - Dividing by the length of a list that could be empty

2. **Static analysis can help find these bugs** before runtime by:
   - Parsing the AST to find division operations
   - Checking if divisors are constants or variables
   - Looking for guard conditions that protect against zero

3. **Proper fixes involve**:
   - Adding explicit checks before division
   - Handling edge cases gracefully
   - Choosing appropriate default values or error handling strategies

4. **Different handling strategies**:
   - Return a default value (e.g., 0, None, float('inf'))
   - Skip the operation
   - Raise a more informative exception
   - Log a warning and continue

## Limitations of the Bug Finders

The bug finders shown here are simplified for demonstration:
- They don't do full data flow analysis
- They can't track variable values across function boundaries
- They have limited understanding of guard conditions
- Real-world static analysis tools would be more sophisticated

## Real-World Applications

This technique can be extended to:
- Building linters for code quality
- Creating security scanners for vulnerabilities
- Developing IDE plugins for real-time bug detection
- Integrating into CI/CD pipelines for automated code review