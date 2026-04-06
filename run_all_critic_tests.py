#!/usr/bin/env python3
"""Run all critic_check tests and verify they all pass."""

import sys
import os
import subprocess

def run_test_file(test_file):
    """Run a test file and return (success, output)."""
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Test timed out: {test_file}"
    except Exception as e:
        return False, f"Error running {test_file}: {e}"

def main():
    """Run all test files."""
    test_files = [
        "test_critic.py",
        "test_critic_new.py",
        "test_critic_comprehensive.py",
        "test_critic_edge_cases.py",
        "test_critic_regex_edge_cases.py",
    ]
    
    # Check which files exist
    existing_files = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_files.append(test_file)
        else:
            print(f"Warning: {test_file} not found")
    
    print(f"Running {len(existing_files)} test files...\n")
    
    all_passed = True
    for test_file in existing_files:
        print(f"=== Running {test_file} ===")
        success, output = run_test_file(test_file)
        
        if success:
            print(f"✓ {test_file} passed")
            # Show summary if available
            if "Total:" in output:
                for line in output.split('\n'):
                    if "Total:" in line:
                        print(f"  {line}")
        else:
            print(f"✗ {test_file} failed")
            print(f"Output:\n{output}")
            all_passed = False
        
        print()
    
    # Also run the test from benchmarks directory
    benchmark_test = "benchmarks/test_offline.py"
    if os.path.exists(benchmark_test):
        print(f"=== Running {benchmark_test} ===")
        
        # Change to benchmarks directory to run the test
        original_cwd = os.getcwd()
        os.chdir("benchmarks")
        
        success, output = run_test_file("test_offline.py")
        
        if success:
            print(f"✓ {benchmark_test} passed")
            # Show summary if available
            if "Total:" in output:
                for line in output.split('\n'):
                    if "Total:" in line:
                        print(f"  {line}")
        else:
            print(f"✗ {benchmark_test} failed")
            print(f"Output:\n{output}")
            all_passed = False
        
        os.chdir(original_cwd)
        print()
    
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())