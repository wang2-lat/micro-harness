# Harness Comparison Report: harness.py vs openai_harness.py

## Overview

This report compares the two main harness implementations in the micro-harness project:
- `src/harness.py` - The original Claude/Anthropic implementation
- `src/openai_harness.py` - OpenAI-compatible implementation for DeepSeek, GLM, Kimi, etc.

## Key Differences

### 1. **API Client & Dependencies**
- **harness.py**: Uses `anthropic` library, imports `anthropic` directly
- **openai_harness.py**: Uses `openai` library, imports `OpenAI` client

### 2. **Default Model**
- **harness.py**: `"claude-sonnet-4-5"` (Anthropic Claude)
- **openai_harness.py**: `"gpt-4o"` (OpenAI) but configurable via environment variable `MODEL`

### 3. **Tool Schema Format**
- **harness.py**: Uses Anthropic's native tool schema format
- **openai_harness.py**: Converts to OpenAI function calling format with `{"type": "function", "function": {...}}` structure

### 4. **System Prompt Structure**
- **harness.py**: Uses `build_system_prompt()` function with cache boundary technique (TECHNIQUE 3)
  - Splits into cached stable prefix + uncached dynamic suffix
  - Uses `cache_control` parameter for ephemeral caching
  - Base instructions: "You are micro-harness, a minimal coding agent."
  
- **openai_harness.py**: Simplified system prompt with CRITICAL RULES
  - No cache boundary technique
  - More detailed, prescriptive rules for agent behavior
  - Includes 7 specific CRITICAL RULES for efficient operation

### 5. **Token Tracking & Caching**
- **harness.py**: Tracks cache tokens (`cache_read_tokens`, `cache_creation_tokens`)
- **openai_harness.py**: No cache tracking (returns 0 for cache-related fields)

### 6. **Message Structure**
- **harness.py**: Uses Anthropic Messages API format with `system` parameter
- **openai_harness.py**: Uses OpenAI chat format with `system` role in messages array

### 7. **Tool Execution & Response Handling**
- **harness.py**: Uses `tool_use` blocks with `tool_result` responses
- **openai_harness.py**: Uses `tool_calls` array with `tool` role responses

### 8. **Error Handling for Tool Arguments**
- **harness.py**: Assumes proper JSON from Anthropic API
- **openai_harness.py**: Has explicit `json.loads()` with fallback for malformed JSON

### 9. **CLI Interface**
- **harness.py**: Simple usage: `python harness.py '<task>'`
- **openai_harness.py**: More detailed usage with environment variable documentation
  - Supports `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL` env vars

### 10. **Code Organization**
- **harness.py**: Self-contained with all tool implementations
- **openai_harness.py**: Imports tools and utilities from `harness.py`
  - Reuses `TOOL_DISPATCH`, `TOOLS_SCHEMA`, `critic_check`, `bootstrap_env`, etc.

## Shared Components

Both harnesses share:
- **Tool implementations**: `tool_read`, `tool_write`, `tool_edit`, `tool_bash`, `tool_grep`, `tool_tree`
- **Configuration**: `HarnessConfig` dataclass
- **Result structure**: `HarnessResult` dataclass  
- **Safety features**: `critic_check()` function with dangerous pattern detection
- **Environment bootstrap**: `bootstrap_env()` function
- **File indexing**: `build_file_index()` function

## Design Philosophy Differences

### harness.py (Anthropic)
- **Focus**: Demonstrates 8 specific techniques as a learning tool
- **Structure**: Organized by "TECHNIQUE" comments with clear pedagogical intent
- **Features**: Implements cache boundary, three-layer memory, circuit breakers
- **Goal**: "The smallest agent harness you can learn from"

### openai_harness.py (OpenAI-compatible)
- **Focus**: Practical compatibility with multiple LLM providers
- **Structure**: Simplified, pragmatic implementation
- **Features**: Drops some advanced techniques (caching) for broader compatibility
- **Goal**: "Works with DeepSeek, GLM, Kimi, etc."

## Performance Implications

1. **Caching**: harness.py has potential token savings via cache boundary technique
2. **Flexibility**: openai_harness.py supports more LLM providers
3. **Rules Enforcement**: openai_harness.py has more prescriptive agent rules
4. **Error Handling**: openai_harness.py has additional JSON parsing safeguards

## Usage Recommendations

### Use harness.py when:
- Working with Anthropic Claude models
- Wanting to learn the 8 micro-harness techniques
- Need cache optimization for repeated tasks
- Prefer the pedagogical code structure

### Use openai_harness.py when:
- Working with OpenAI-compatible APIs (DeepSeek, GLM, Kimi, etc.)
- Need compatibility across multiple LLM providers
- Want more prescriptive agent behavior rules
- Don't need cache optimization features

## Similar Third Implementation: gemini_harness.py

There's also a `gemini_harness.py` that follows a similar pattern to `openai_harness.py`:
- Imports tools from `harness.py`
- Converts tool schemas to Gemini format
- Uses Google's Gemini API
- Default model: `"gemini-2.5-flash"`

## Conclusion

The `openai_harness.py` is a pragmatic adaptation of the original `harness.py` designed for broader LLM provider compatibility. It sacrifices some advanced techniques (like cache boundaries) for simplicity and wider API support, while adding more prescriptive agent rules. Both share the core tool implementations and safety features, making them consistent in behavior despite different underlying APIs.