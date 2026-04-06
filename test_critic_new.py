#!/usr/bin/env python3
"""New tests for the critic_check function from src/harness.py"""

import sys
import os
sys.path.insert(0, 'src')

from harness import critic_check

def test_case_sensitivity_allowlist():
    """Test that safe commands are case-sensitive in allowlist mode."""
    # 'ls' is in safe_prefixes, but 'LS' should not be.
    allowed, reason = critic_check("LS -la", "allowlist")
    assert not allowed, "Uppercase safe command should be blocked in allowlist mode"
    assert "not in allowlist" in reason, f"Unexpected reason: {reason}"

    allowed, reason = critic_check("Python script.py", "allowlist")
    assert not allowed, "Uppercase Python command should be blocked in allowlist mode"
    assert "not in allowlist" in reason, f"Unexpected reason: {reason}"

def test_dangerous_patterns_with_invalid_critic_mode():
    """Test that dangerous patterns are blocked even with an invalid critic mode."""
    dangerous_command = "rm -rf /"
    allowed, reason = critic_check(dangerous_command, "some_invalid_mode")
    assert not allowed, "Dangerous command should be blocked even with invalid critic mode"
    assert "BLOCKED" in reason, f"Reason should mention BLOCKED: {reason}"

def test_empty_command_dangerous_patterns():
    """Test that an empty command string does not trigger dangerous patterns."""
    allowed, reason = critic_check("", "allowlist")
    assert not allowed, "Empty command should not be allowed in allowlist mode"
    assert "not in allowlist" in reason, f"Unexpected reason for empty command: {reason}"

    allowed, reason = critic_check("", "off")
    assert allowed, "Empty command should be allowed in off mode"
    assert "critic disabled" in reason, f"Unexpected reason for empty command in off mode: {reason}"

def run_all_new_tests():
    """Run all new test functions and report results."""
    test_functions = [
        test_case_sensitivity_allowlist,
        test_dangerous_patterns_with_invalid_critic_mode,
        test_empty_command_dangerous_patterns,
    ]
    
    passed = 0
    failed = 0
    
    print("\n--- Running New Critic Tests ---")
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: Unexpected error: {e}")
            failed += 1
    
    print(f"\nTotal New Tests: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_all_new_tests()
    sys.exit(0 if success else 1)
