"""
micro-harness: Gemini backend
Same 8 techniques, using Google's Gemini API with function calling.
"""
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from harness import (
    TOOL_DISPATCH, tool_read, tool_write, tool_edit, tool_bash, tool_grep,
    critic_check, bootstrap_env, build_file_index,
    HarnessConfig, HarnessResult,
)


# ─── Convert our tool schemas to Gemini function declarations ───

GEMINI_TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="read",
        description="Read a file. Returns content with line numbers.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "path": types.Schema(type="STRING"),
                "start_line": types.Schema(type="INTEGER"),
                "limit": types.Schema(type="INTEGER"),
            },
            required=["path"],
        ),
    ),
    types.FunctionDeclaration(
        name="write",
        description="Write content to a file (creates or overwrites).",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "path": types.Schema(type="STRING"),
                "content": types.Schema(type="STRING"),
            },
            required=["path", "content"],
        ),
    ),
    types.FunctionDeclaration(
        name="edit",
        description="Replace exact text in a file. old_string must match exactly.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "path": types.Schema(type="STRING"),
                "old_string": types.Schema(type="STRING"),
                "new_string": types.Schema(type="STRING"),
            },
            required=["path", "old_string", "new_string"],
        ),
    ),
    types.FunctionDeclaration(
        name="bash",
        description="Execute a shell command. Returns stdout+stderr+exit_code.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "command": types.Schema(type="STRING"),
                "timeout": types.Schema(type="INTEGER"),
            },
            required=["command"],
        ),
    ),
    types.FunctionDeclaration(
        name="grep",
        description="Search for pattern in files using ripgrep.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "pattern": types.Schema(type="STRING"),
                "path": types.Schema(type="STRING"),
                "glob": types.Schema(type="STRING"),
            },
            required=["pattern"],
        ),
    ),
    types.FunctionDeclaration(
        name="tree",
        description="Show directory structure like the unix 'tree' command but implemented in pure Python (no subprocess).",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "path": types.Schema(type="STRING"),
                "max_depth": types.Schema(type="INTEGER"),
            },
            required=[],
        ),
    ),
])


class GeminiHarness:
    """Agent harness using Gemini as the LLM backend."""

    def __init__(self, config: HarnessConfig | None = None):
        self.config = config or HarnessConfig(model="gemini-2.5-flash")
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        self.tokens_used = 0
        self.consecutive_errors = 0

    def log(self, msg: str):
        if self.config.verbose:
            print(msg, flush=True)

    def run(self, task: str, cwd: str | None = None) -> HarnessResult:
        start = time.time()
        c = self.config

        # TECHNIQUE 5: File index
        file_index = build_file_index(cwd or os.getcwd()) if c.use_file_index else None

        # TECHNIQUE 3: System prompt (Gemini uses system_instruction)
        system_parts = [
            "You are micro-harness, a minimal coding agent.",
            "Use tools to complete the user's task.",
            "When finished, output a final message summarizing what you did.",
        ]
        if file_index:
            system_parts.append(f"\n=== Project Files ===\n{file_index}")
        system_parts.append(f"\nCWD: {os.getcwd()}\nDate: {time.strftime('%Y-%m-%d %H:%M')}")

        system_instruction = "\n".join(system_parts)

        # TECHNIQUE 4: Bootstrap
        first_msg = task
        if c.use_bootstrap:
            first_msg = bootstrap_env(cwd) + "\n\nTask: " + task

        # Build chat history
        contents = [types.Content(role="user", parts=[types.Part(text=first_msg)])]
        tool_calls_log = []
        input_tok = output_tok = 0

        for turn in range(c.max_turns):
            # TECHNIQUE 6: Circuit breakers
            if self.tokens_used > c.max_tokens_total:
                return self._result(False, turn, input_tok, output_tok, "",
                                   "token budget exceeded", tool_calls_log, start)

            if self.consecutive_errors >= c.max_consecutive_errors:
                return self._result(False, turn, input_tok, output_tok, "",
                                   f"{c.max_consecutive_errors} consecutive errors",
                                   tool_calls_log, start)

            try:
                response = self.client.models.generate_content(
                    model=c.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=[GEMINI_TOOLS],
                        max_output_tokens=4096,
                    ),
                )
            except Exception as e:
                err_str = str(e)
                self.consecutive_errors += 1
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate" in err_str.lower():
                    wait = min(30, 5 * self.consecutive_errors)
                    self.log(f"[turn {turn}] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    self.log(f"[turn {turn}] API error: {e}")
                    time.sleep(3)
                continue

            self.consecutive_errors = 0

            # Track tokens
            if response.usage_metadata:
                input_tok += response.usage_metadata.prompt_token_count or 0
                output_tok += response.usage_metadata.candidates_token_count or 0
                self.tokens_used = input_tok + output_tok

            # Check for function calls
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content or not candidate.content.parts:
                return self._result(True, turn + 1, input_tok, output_tok,
                                   response.text or "", None, tool_calls_log, start)

            parts = candidate.content.parts
            fn_calls = [p for p in parts if p.function_call]

            if not fn_calls:
                # No tool calls — model is done
                text = "".join(p.text for p in parts if p.text)
                self.log(f"[turn {turn}] DONE: {text[:200]}")
                return self._result(True, turn + 1, input_tok, output_tok,
                                   text, None, tool_calls_log, start)

            # Add model response to history
            contents.append(types.Content(role="model", parts=parts))

            # Execute tools and build response
            fn_response_parts = []
            for part in fn_calls:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                tool_calls_log.append(f"{tool_name}({json.dumps(tool_args)[:100]})")

                self.log(f"[turn {turn}] → {tool_name}({str(tool_args)[:80]})")

                # TECHNIQUE 7: Critic
                if tool_name == "bash" and c.critic_mode != "off":
                    allowed, reason = critic_check(tool_args.get("command", ""), c.critic_mode)
                    if not allowed:
                        self.log(f"  ⛔ BLOCKED: {reason}")
                        fn_response_parts.append(types.Part.from_function_response(
                            name=tool_name, response={"error": f"BLOCKED: {reason}"}
                        ))
                        continue

                # Execute
                try:
                    fn = TOOL_DISPATCH[tool_name]
                    result = fn(**tool_args)
                    result_str = str(result)[:self.config.max_tool_output]
                    self.log(f"  ← {result_str[:150]}")
                    fn_response_parts.append(types.Part.from_function_response(
                        name=tool_name, response={"result": result_str}
                    ))
                except Exception as e:
                    self.log(f"  ← ERROR: {e}")
                    fn_response_parts.append(types.Part.from_function_response(
                        name=tool_name, response={"error": str(e)}
                    ))

            contents.append(types.Content(role="user", parts=fn_response_parts))

        return self._result(False, c.max_turns, input_tok, output_tok, "",
                           f"max_turns ({c.max_turns}) reached", tool_calls_log, start)

    def _result(self, success, turns, inp, out, msg, err, tools, start):
        return HarnessResult(
            success=success, turns=turns,
            total_tokens=inp + out, input_tokens=inp, output_tokens=out,
            cache_read_tokens=0, cache_creation_tokens=0,
            final_message=msg, error=err, tool_calls=tools,
            elapsed_sec=time.time() - start,
        )


# ─── CLI ───

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: GEMINI_API_KEY=xxx python3 gemini_harness.py '<task>'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    harness = GeminiHarness(HarnessConfig(model="gemini-2.5-flash", verbose=True))
    result = harness.run(task)

    print("\n" + "=" * 60)
    print(f"Success: {result.success}")
    print(f"Turns: {result.turns}")
    print(f"Tokens: {result.total_tokens:,} (in={result.input_tokens:,} out={result.output_tokens:,})")
    print(f"Elapsed: {result.elapsed_sec:.1f}s")
    print(f"Tool calls: {len(result.tool_calls)}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"\nFinal: {result.final_message[:300]}")
