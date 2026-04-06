"""
micro-harness: OpenAI-compatible backend (works with DeepSeek, GLM, Kimi, etc.)
"""
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))
from harness import (
    TOOL_DISPATCH, TOOLS_SCHEMA, critic_check, bootstrap_env, build_file_index,
    HarnessConfig, HarnessResult,
)

# Convert our tool schemas to OpenAI format
OPENAI_TOOLS = [
    {"type": "function", "function": {
        "name": t["name"],
        "description": t["description"],
        "parameters": t["input_schema"],
    }}
    for t in TOOLS_SCHEMA
]


class OpenAIHarness:
    """Agent harness using any OpenAI-compatible API."""

    def __init__(self, config: HarnessConfig | None = None,
                 api_key: str | None = None, base_url: str | None = None):
        self.config = config or HarnessConfig()
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.tokens_used = 0
        self.consecutive_errors = 0

    def log(self, msg: str):
        if self.config.verbose:
            print(msg, flush=True)

    def run(self, task: str, cwd: str | None = None) -> HarnessResult:
        start = time.time()
        c = self.config

        # System prompt
        file_index = build_file_index(cwd or os.getcwd()) if c.use_file_index else None
        system_parts = [
            "You are a coding agent. You have tools. Be efficient.",
            "",
            "CRITICAL RULES:",
            "1. Use grep to find things. NEVER read an entire file to search for something.",
            "2. Use read with start_line+limit (max 30 lines). NEVER read more than 30 lines at once.",
            "3. Before editing, ALWAYS read the exact lines you want to change. Copy old_string exactly from the read output.",
            "4. After writing code, ALWAYS run it immediately to check for errors.",
            "5. If you need to write a new Python file that imports from this project, start with: import sys; sys.path.insert(0, 'src')",
            "6. Work fast. Don't read files you don't need. Don't explain your thinking — just act.",
            "7. When done, say what you did in 2-3 sentences.",
        ]
        if file_index:
            system_parts.append(f"\n=== Project Files ===\n{file_index}")
        system_parts.append(f"\nCWD: {os.getcwd()}\nDate: {time.strftime('%Y-%m-%d %H:%M')}")
        system_msg = "\n".join(system_parts)

        # Bootstrap
        first_msg = task
        if c.use_bootstrap:
            first_msg = bootstrap_env(cwd) + "\n\nTask: " + task

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": first_msg},
        ]
        tool_calls_log = []
        input_tok = output_tok = 0

        for turn in range(c.max_turns):
            if self.tokens_used > c.max_tokens_total:
                return self._result(False, turn, input_tok, output_tok, "",
                                   "token budget exceeded", tool_calls_log, start)
            if self.consecutive_errors >= c.max_consecutive_errors:
                return self._result(False, turn, input_tok, output_tok, "",
                                   f"{c.max_consecutive_errors} consecutive errors",
                                   tool_calls_log, start)

            try:
                response = self.client.chat.completions.create(
                    model=c.model,
                    messages=messages,
                    tools=OPENAI_TOOLS,
                    max_tokens=4096,
                )
            except Exception as e:
                self.consecutive_errors += 1
                self.log(f"[turn {turn}] API error: {e}")
                time.sleep(2)
                continue

            self.consecutive_errors = 0
            choice = response.choices[0]
            msg = choice.message

            # Track tokens
            if response.usage:
                input_tok += response.usage.prompt_tokens or 0
                output_tok += response.usage.completion_tokens or 0
                self.tokens_used = input_tok + output_tok

            # No tool calls — done
            if not msg.tool_calls:
                text = msg.content or ""
                self.log(f"[turn {turn}] DONE: {text[:200]}")
                return self._result(True, turn + 1, input_tok, output_tok,
                                   text, None, tool_calls_log, start)

            # Add assistant message
            messages.append(msg.model_dump())

            # Execute tools
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                tool_calls_log.append(f"{fn_name}({json.dumps(fn_args)[:100]})")
                self.log(f"[turn {turn}] → {fn_name}({str(fn_args)[:80]})")

                # Critic
                if fn_name == "bash" and c.critic_mode != "off":
                    allowed, reason = critic_check(fn_args.get("command", ""), c.critic_mode)
                    if not allowed:
                        self.log(f"  ⛔ BLOCKED: {reason}")
                        messages.append({
                            "role": "tool", "tool_call_id": tc.id,
                            "content": f"BLOCKED: {reason}",
                        })
                        continue

                # Execute
                try:
                    fn = TOOL_DISPATCH[fn_name]
                    result = fn(**fn_args)
                    result_str = str(result)[:self.config.max_tool_output]
                    self.log(f"  ← {result_str[:150]}")
                    messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": result_str,
                    })
                except Exception as e:
                    self.log(f"  ← ERROR: {e}")
                    messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": f"ERROR: {e}",
                    })

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 openai_harness.py '<task>'")
        print("Env: OPENAI_API_KEY, OPENAI_BASE_URL, MODEL (default: gpt-4o)")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    model = os.environ.get("MODEL", "gpt-4o")
    h = OpenAIHarness(HarnessConfig(model=model, verbose=True))
    r = h.run(task)

    print("\n" + "=" * 60)
    print(f"Model: {model}")
    print(f"Success: {r.success}")
    print(f"Turns: {r.turns}")
    print(f"Tokens: {r.total_tokens:,} (in={r.input_tokens:,} out={r.output_tokens:,})")
    print(f"Elapsed: {r.elapsed_sec:.1f}s")
    print(f"Tool calls: {len(r.tool_calls)}")
    if r.error:
        print(f"Error: {r.error}")
    print(f"\nFinal: {r.final_message[:300]}")
