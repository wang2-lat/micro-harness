"""
Hybrid Harness: Expensive planner + cheap executor.

The idea: Claude/GPT plans (1 call, ~$0.01), DeepSeek executes (many calls, cheap).
This might break the 50% ceiling on DeepSeek without paying GPT-5.4 prices for every turn.

Hypothesis: The 0/9 failures on DeepSeek were comprehension failures, not execution failures.
If we give DeepSeek concrete steps, it should be able to execute them.
"""
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))
from harness import (
    TOOL_DISPATCH, HarnessConfig, HarnessResult,
    bootstrap_env, build_file_index,
)
from openai_harness import OpenAIHarness


class HybridHarness:
    """
    Phase 1: Expensive model (Claude/GPT) reads code + generates concrete step list.
             No tool calls — just one API call with file contents in prompt.
    Phase 2: Cheap model (DeepSeek) executes each step with tools.
    Phase 3: Cheap model verifies the result.
    """

    def __init__(
        self,
        planner_model: str = "claude-sonnet-4-6",
        planner_key: str = "",
        executor_model: str = "DeepSeek-V3.2",
        executor_key: str = "",
        base_url: str = "https://bobdong.cn/v1",
        verbose: bool = True,
    ):
        self.planner_client = OpenAI(api_key=planner_key, base_url=base_url)
        self.planner_model = planner_model
        self.executor_model = executor_model
        self.executor_key = executor_key
        self.base_url = base_url
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(msg, flush=True)

    def run(self, task: str, cwd: str | None = None) -> HarnessResult:
        start = time.time()
        cwd = cwd or os.getcwd()

        # ─── Phase 1: Plan (1 expensive call, no tools) ───
        self.log(f"[PLAN] Using {self.planner_model} to decompose task...")

        # Read the target file so planner has context
        file_index = build_file_index(cwd)
        env = bootstrap_env(cwd)

        # Find relevant files mentioned in the task
        relevant_code = ""
        for keyword in ["harness.py", "openai_harness", "gemini_harness"]:
            if keyword in task.lower() or keyword in task:
                fpath = Path(cwd) / "src" / keyword
                if not fpath.exists() and not keyword.endswith(".py"):
                    fpath = Path(cwd) / "src" / (keyword + ".py")
                if fpath.exists():
                    content = fpath.read_text()
                    # Only first 200 lines to save tokens
                    lines = content.split('\n')[:200]
                    relevant_code += f"\n--- {fpath.name} (first 200 lines) ---\n"
                    for i, line in enumerate(lines):
                        relevant_code += f"{i+1}: {line}\n"

        plan_prompt = (
            f"You are a senior developer. A junior developer needs to complete this task:\n\n"
            f"TASK: {task}\n\n"
            f"PROJECT FILES:\n{file_index}\n\n"
            f"ENVIRONMENT:\n{env}\n\n"
            f"RELEVANT CODE:\n{relevant_code}\n\n"
            f"Write a numbered list of CONCRETE steps the junior can follow using these tools:\n"
            f"- grep <pattern> <file> (search for text)\n"
            f"- read <file> <start_line> <num_lines> (read specific lines)\n"
            f"- edit <file> <old_text> <new_text> (replace exact text)\n"
            f"- write <file> <content> (create/overwrite file)\n"
            f"- bash <command> (run shell command)\n\n"
            f"Each step MUST be specific enough to execute without thinking.\n"
            f"Include exact file paths, line numbers, and text to match.\n"
            f"Output ONLY the numbered steps."
        )

        try:
            plan_response = self.planner_client.chat.completions.create(
                model=self.planner_model,
                messages=[{"role": "user", "content": plan_prompt}],
                max_tokens=2000,
            )
            plan_text = plan_response.choices[0].message.content or ""
            plan_tokens = (plan_response.usage.prompt_tokens or 0) + (plan_response.usage.completion_tokens or 0)
        except Exception as e:
            self.log(f"[PLAN] ERROR: {e}")
            return HarnessResult(
                success=False, turns=0, total_tokens=0, input_tokens=0,
                output_tokens=0, cache_read_tokens=0, cache_creation_tokens=0,
                final_message="", error=f"planner failed: {e}",
                elapsed_sec=time.time() - start,
            )

        steps = self._parse_steps(plan_text)
        self.log(f"[PLAN] Generated {len(steps)} steps ({plan_tokens} tokens):")
        for i, step in enumerate(steps):
            self.log(f"  {i+1}. {step[:80]}")

        if not steps:
            return HarnessResult(
                success=False, turns=0, total_tokens=plan_tokens, input_tokens=0,
                output_tokens=0, cache_read_tokens=0, cache_creation_tokens=0,
                final_message="", error="planner generated no steps",
                elapsed_sec=time.time() - start,
            )

        # ─── Phase 2: Execute each step (cheap model with tools) ───
        self.log(f"\n[EXEC] Using {self.executor_model} to execute {len(steps)} steps...")
        total_exec_tokens = 0
        total_turns = 0
        all_tool_calls = []

        for i, step in enumerate(steps):
            self.log(f"\n[EXEC] Step {i+1}/{len(steps)}: {step[:60]}")
            executor = OpenAIHarness(
                HarnessConfig(
                    model=self.executor_model, max_turns=6, verbose=self.verbose,
                    use_bootstrap=False, use_file_index=False,
                ),
                api_key=self.executor_key,
                base_url=self.base_url,
            )
            result = executor.run(step, cwd)
            total_exec_tokens += result.total_tokens
            total_turns += result.turns
            all_tool_calls.extend(result.tool_calls)

            if not result.success:
                self.log(f"  [EXEC] Step {i+1} incomplete (continuing anyway)")

        # ─── Phase 3: Verify (cheap model) ───
        self.log(f"\n[VERIFY] Checking result...")
        verifier = OpenAIHarness(
            HarnessConfig(
                model=self.executor_model, max_turns=5, verbose=self.verbose,
                use_bootstrap=False, use_file_index=False,
            ),
            api_key=self.executor_key,
            base_url=self.base_url,
        )
        verify_prompt = f"Verify that this task was completed: {task}\nCheck the relevant files. Report success or failure in 2 sentences."
        vresult = verifier.run(verify_prompt, cwd)
        total_exec_tokens += vresult.total_tokens
        total_turns += vresult.turns

        total_tokens = plan_tokens + total_exec_tokens
        elapsed = time.time() - start

        self.log(f"\n[DONE] Plan: {plan_tokens} tok | Exec: {total_exec_tokens} tok | Total: {total_tokens} tok | {elapsed:.1f}s")

        return HarnessResult(
            success=vresult.success,
            turns=total_turns,
            total_tokens=total_tokens,
            input_tokens=plan_tokens,
            output_tokens=total_exec_tokens,
            cache_read_tokens=0, cache_creation_tokens=0,
            final_message=vresult.final_message,
            tool_calls=all_tool_calls,
            elapsed_sec=elapsed,
        )

    def _parse_steps(self, text: str) -> list[str]:
        lines = text.strip().split('\n')
        steps = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                content = line.lstrip('0123456789.-) ').strip()
                if content and len(content) > 10:
                    steps.append(content)
        return steps if steps else ([text] if len(text) > 20 else [])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 hybrid_harness.py '<task>'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    h = HybridHarness(
        planner_model=os.environ.get("PLANNER_MODEL", "claude-sonnet-4-6"),
        planner_key=os.environ.get("PLANNER_KEY", ""),
        executor_model=os.environ.get("EXECUTOR_MODEL", "DeepSeek-V3.2"),
        executor_key=os.environ.get("EXECUTOR_KEY", ""),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://bobdong.cn/v1"),
    )
    r = h.run(task)
    print(f"\nSuccess: {r.success} | Turns: {r.turns} | Tokens: {r.total_tokens:,} | Time: {r.elapsed_sec:.1f}s")
