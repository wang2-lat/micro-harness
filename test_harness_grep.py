#!/usr/bin/env python3
"""Test harness with grep error."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.harness import MicroHarness, HarnessConfig

# Create a minimal test
config = HarnessConfig(
    max_turns=5,
    verbose=True,
    use_bootstrap=False,
    use_file_index=False,
    critic_mode="off"
)

harness = MicroHarness(config)

# Mock the API call to avoid needing actual API key
import anthropic
from unittest.mock import Mock, patch

# Create a mock response that calls the grep tool
mock_response = Mock()
mock_response.stop_reason = "tool_use"
mock_response.usage = Mock(input_tokens=100, output_tokens=50)
mock_response.content = [
    Mock(
        type="tool_use",
        name="grep",
        id="test-id",
        input={"pattern": "test", "path": ".", "glob": "*.py"}
    )
]

# Test the tool execution directly
print("Testing tool_grep directly...")
from src.harness import tool_grep
result = tool_grep("test", ".", "*.py")
print(f"Result: {result!r}")
print(f"Starts with ERROR:: {result.startswith('ERROR:')}")

# Now test through the harness loop
print("\nTesting through harness (mocked)...")

with patch.object(anthropic.Anthropic, 'messages') as mock_messages:
    mock_messages.create.return_value = mock_response
    
    # Run the harness
    result = harness.run("Test grep tool")
    print(f"Harness result success: {result.success}")
    print(f"Harness error: {result.error}")
    print(f"Tool calls: {result.tool_calls}")