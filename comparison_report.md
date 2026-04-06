# Comparison Report: harness.py vs openai_harness.py

## Overview

This report compares the two main agent harness implementations in the micro-harness project:
- `src/harness.py` - The original Claude/Anthropic API implementation
- `src/openai_harness.py` - OpenAI-compatible API implementation

Both files implement the same core "micro-harness" architecture with 8 key techniques, but differ in their API integrations and implementation details.

## Key Similarities

### Shared Architecture
Both harnesses implement the same 8 techniques:
1. **Agent Loop with Circuit Breakers** - Main execution loop with safety limits
2. **Tool System** - 6 structured tools (read, write, edit, bash, grep, tree)
3. **Cache Boundary** - Stable prefix vs dynamic suffix in system prompt
4. **Environment Bootstrap** - Initial environment snapshot
5. **Three-Layer Memory** - File index system
6. **Circuit Breakers** - Token budget, consecutive errors, max turns
7. **Critic Permissions** - Safety checks for bash commands
8. **Lazy Skill Loading** - File index as lightweight memory

### Shared Components
Both harnesses import and use the same core components from `harness.py`:
- Tool implementations (`TOOL_DISPATCH`, `tool_read`, `tool_write`, etc.)
- Critic system (`critic_check`)
- Environment bootstrap (`bootstrap_env`)
- File index (`build_file_index`)
- Configuration (`HarnessConfig`) and result (`HarnessResult`) classes

## Key Differences

### 1. API Integration

**harness.py (Anthropic API):**
- Uses `anthropic.Anthropic()` client
- Claude-specific models (`claude-sonnet-4-5`)
- Anthropic Messages API with tool calling
- Supports cache control (`cache_control` parameter)

**openai_harness.py (OpenAI-compatible API):**
- Uses `openai.OpenAI()` client
- Works with any OpenAI-compatible API (OpenAI, DeepSeek, GLM, Kimi, etc.)
- OpenAI Chat Completions API with function calling
- No cache support (OpenAI API doesn't have cache control)

### 2. Tool Schema Format

**harness.py:**
- Uses Anthropic's tool schema format
- Direct `TOOLS_SCHEMA` list with `input_schema`

**openai_harness.py:**
- Converts to OpenAI function calling format
- Wraps tools in `{"type": "function", "function": {...}}` structure
- Uses `OPENAI_TOOLS` variable (converted from `TOOLS_SCHEMA`)

### 3. System Prompt Structure

**harness.py:**
- Uses `build_system_prompt()` function with cache boundary technique
- Splits into stable prefix (cached) and dynamic suffix
- Returns list of content blocks for Anthropic API

**openai_harness.py:**
- Builds system prompt inline as a single string
- Includes detailed workflow instructions (PLAN, ACT, VERIFY rules)
- No cache boundary implementation
- Appends file index and CWD/Date directly

### 4. Message Format

**harness.py (Anthropic):**
- Messages as list of dicts with `role` and `content`
- Tool results use `{"type": "tool_result", "tool_use_id": ..., "content": ..., "is_error": ...}`
- Supports `is_error` flag for error handling
- Tool arguments come directly as `block.input` (already parsed)

**openai_harness.py (OpenAI):**
- Messages as list of dicts with `role` and `content`
- Tool results use `{"role": "tool", "tool_call_id": ..., "content": ...}`
- No explicit `is_error` flag (errors in content)
- Tool arguments need JSON parsing: `json.loads(tc.function.arguments)`

### 5. Token Tracking

**harness.py:**
- Tracks cache tokens (`cache_read_tokens`, `cache_creation_tokens`)
- Uses `response.usage` with Anthropic-specific fields
- Supports cache token accounting

**openai_harness.py:**
- Only tracks basic tokens (`prompt_tokens`, `completion_tokens`)
- No cache token tracking
- Uses `response.usage` from OpenAI API

### 6. Error Handling

**harness.py:**
- Marks tool results with `is_error=True` for error messages
- Checks for `"ERROR:"` prefix in result strings
- More sophisticated error detection

**openai_harness.py:**
- All tool results go in `content` field
- Relies on string content to indicate errors
- Simpler error handling

### 7. CLI Interface

**harness.py CLI:**
- Simple: `python harness.py '<task>'`
- Uses default Claude model (`claude-sonnet-4-5`)
- No environment variable configuration

**openai_harness.py CLI:**
- More configurable: `python3 openai_harness.py '<task>'`
- Supports `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL` env vars
- Default model: `gpt-4o` (configurable via env var, but class defaults to Claude)
- **Note**: The `OpenAIHarness` class constructor uses `HarnessConfig()` which defaults to `"claude-sonnet-4-5"`, so model must be explicitly set

### 8. Code Structure

**harness.py:**
- 577 lines total
- Self-contained with all tool implementations
- More complex due to cache boundary implementation
- Includes `tool_tree()` implementation

**openai_harness.py:**
- 200 lines total
- Imports most functionality from `harness.py`
- Simpler, focused on API adaptation
- Uses helper `_result()` method for consistency

## Performance Implications

### Advantages of harness.py (Anthropic):
1. **Cache Optimization** - Can save significant tokens with repeated system prompts
2. **Better Error Handling** - Explicit error flags for tool results
3. **Sophisticated Prompt Structure** - Cache boundary technique reduces costs

### Advantages of openai_harness.py:
1. **API Flexibility** - Works with any OpenAI-compatible provider
2. **Simpler Implementation** - Less complex codebase
3. **Wider Model Support** - Can use GPT-4, DeepSeek, GLM, etc.
4. **Detailed Instructions** - More explicit workflow rules in system prompt

## Use Cases

### Use harness.py when:
- You have access to Claude/Anthropic API
- You need cache optimization for repeated tasks
- You want sophisticated error handling
- You're working on cost-sensitive applications

### Use openai_harness.py when:
- You need compatibility with multiple LLM providers
- You're using OpenAI, DeepSeek, GLM, or other compatible APIs
- You want simpler code to maintain
- You need detailed instruction following

## Gemini Harness Comparison

There's also `gemini_harness.py` which follows a similar pattern:
- Adapts the same core architecture to Google's Gemini API
- Uses Gemini-specific tool schema format
- Similar to `openai_harness.py` in being an API adapter
- Shows the modularity of the micro-harness design

## Conclusion

Both `harness.py` and `openai_harness.py` successfully implement the core micro-harness architecture while adapting to different LLM APIs. The key differences are:

1. **API Integration** - Anthropic vs OpenAI-compatible
2. **Cache Support** - Present in Anthropic, absent in OpenAI version
3. **Tool Schema Format** - API-specific adaptations
4. **System Prompt Structure** - Cache boundary vs single prompt
5. **Error Handling** - Sophisticated vs simple approaches

The `openai_harness.py` demonstrates how the micro-harness architecture can be adapted to different LLM backends while maintaining the same core techniques and tool system. This modularity is a key strength of the design.

## Recommendations

1. **For new projects**: Consider `openai_harness.py` for its API flexibility and simpler code
2. **For cost optimization**: Use `harness.py` with Claude cache features if available
3. **For multi-provider support**: The architecture easily supports adding more backends (as shown with `gemini_harness.py`)
4. **For customization**: Both are extensible, but `openai_harness.py` has simpler code to modify

The existence of both implementations shows the versatility of the micro-harness approach and its ability to work across different LLM ecosystems while maintaining consistent agent behavior and tool usage patterns.