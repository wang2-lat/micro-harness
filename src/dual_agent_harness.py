"""
Dual-Agent Harness: Planner + Executor

Technique 9: Sub-agent orchestration.
A "planner" agent decomposes abstract tasks into concrete steps.
An "executor" agent runs each step with tools.

This addresses the #1 failure mode: models can't decompose
"make it configurable" into concrete edit operations.
"""
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))
from harness import (
    TOOL_DISPATCH, TOOLS_SCHEMA, HarnessConfig, HarnessResult,
    bootstrap_env, build_file_index, critic_check,
)
from openai_harness import OpenAIHarness, OPENAI_TOOLS


class DualAgentHarness:
    """
    Two-phase agent:
    Phase 1 (Planner): Reads code, understands task, outputs numbered step list.
    Phase 2 (Executor): Executes each step with tools.
    """

    def __init__(self, config: HarnessConfig | None = None,
                 api_key: str | None = None, base_url: str | None = None):
        self.config = config or HarnessConfig()
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.log_fn = print if self.config.verbose else lambda *a, **k: None

    def run(self, task: str, cwd: str | None = None) -> HarnessResult:
        start = time.time()
        c = self.config

        # Phase 1: Plan
        self.log_fn("[PLANNER] Analyzing task...", flush=True)
        plan = self._plan(task, cwd)
        if not plan:
            return HarnessResult(
                success=False, turns=0, total_tokens=0, input_tokens=0,
                output_tokens=0, cache_read_tokens=0, cache_creation_tokens=0,
                final_message="", error="planner failed to generate plan",
                elapsed_sec=time.time() - start,
            )

        self.log_fn(f"[PLANNER] Plan ({len(plan)} steps):", flush=True)
        for i, step in enumerate(plan):
            self.log_fn(f"  {i+1}. {step}", flush=True)

        # Phase 2: Execute each step
        self.log_fn("\n[EXECUTOR] Starting execution...", flush=True)
        total_turns = 0
        total_input = total_output = 0
        all_tool_calls = []

        for i, step in enumerate(plan):
            self.log_fn(f"\n[EXECUTOR] Step {i+1}/{len(plan)}: {step[:60]}...", flush=True)
            executor = OpenAIHarness(
                HarnessConfig(
                    model=c.model, max_turns=8, verbose=c.verbose,
                    use_bootstrap=False, use_file_index=False,
                ),
                api_key=os.environ.get("OPENAI_API_KEY"),
                base_url=os.environ.get("OPENAI_BASE_URL"),
            )
            result = executor.run(step, cwd)
            total_turns += result.turns
            total_input += result.input_tokens
            total_output += result.output_tokens
            all_tool_calls.extend(result.tool_calls)

            if not result.success:
                self.log_fn(f"  [EXECUTOR] Step {i+1} incomplete: {result.error}", flush=True)
                # Continue anyway — partial progress is better than stopping

        # Final verification
        self.log_fn("\n[VERIFIER] Checking result...", flush=True)
        verifier = OpenAIHarness(
            HarnessConfig(
                model=c.model, max_turns=5, verbose=c.verbose,
                use_bootstrap=False, use_file_index=False,
            ),
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL"),
        )
        verify_result = verifier.run(
            f"Verify that the following task was completed correctly: {task}\n"
            f"Check the relevant files and report if the changes look correct.",
            cwd,
        )
        total_turns += verify_result.turns
        total_input += verify_result.input_tokens
        total_output += verify_result.output_tokens

        return HarnessResult(
            success=verify_result.success,
            turns=total_turns,
            total_tokens=total_input + total_output,
            input_tokens=total_input,
            output_tokens=total_output,
            cache_read_tokens=0, cache_creation_tokens=0,
            final_message=verify_result.final_message,
            tool_calls=all_tool_calls,
            elapsed_sec=time.time() - start,
        )

    def _plan(self, task: str, cwd: str | None = None) -> list[str] | None:
        """Phase 1: Planner agent reads code and generates step list."""
        file_index = build_file_index(cwd or os.getcwd())
        bootstrap = bootstrap_env(cwd)

        planner_prompt = (
            "You are a senior developer planning a coding task. "
            "Given the task and project context below, output a numbered list of CONCRETE steps. "
            "Each step must be a specific action that a junior developer could execute with tools "
            "(read, write, edit, bash, grep). "
            "Be specific: include file names, function names, line references. "
            "Output ONLY the numbered list, nothing else.\n\n"
            f"Project files:\n{file_index}\n\n"
            f"Environment:\n{bootstrap}\n\n"
            f"Task: {task}"
        )

        # Planner gets tools to read code for planning
        messages = [
            {"role": "system", "content": "You are a task planner. Read the code to understand the codebase, then output a numbered step list. Use grep and read tools to understand the code before planning."},
            {"role": "user", "content": planner_prompt},
        ]

        plan_turns = 0
        max_plan_turns = 8

        for turn in range(max_plan_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=OPENAI_TOOLS,
                    max_tokens=2048,
                )
            except Exception as e:
                self.log_fn(f"[PLANNER] API error: {e}", flush=True)
                time.sleep(5)
                continue

            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                # Model outputted text — should be the plan
                text = msg.content or ""
                return self._parse_plan(text)

            # Model wants to read code first — let it
            messages.append(msg.model_dump())
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                self.log_fn(f"[PLANNER] → {fn_name}({str(fn_args)[:60]})", flush=True)

                if fn_name in TOOL_DISPATCH:
                    result = str(TOOL_DISPATCH[fn_name](**fn_args))[:4000]
                else:
                    result = f"Unknown tool: {fn_name}"

                messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": result,
                })

            plan_turns += 1

        return None

    def _parse_plan(self, text: str) -> list[str]:
        """Extract numbered steps from planner output."""
        lines = text.strip().split('\n')
        steps = []
        for line in lines:
            line = line.strip()
            # Match "1. ...", "1) ...", "- ..."
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering prefix
                content = line.lstrip('0123456789.-) ').strip()
                if content:
                    steps.append(content)
        return steps if steps else [text]  # fallback: treat whole text as one step


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dual_agent_harness.py '<task>'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    model = os.environ.get("MODEL", "DeepSeek-V3.2")
    h = DualAgentHarness(HarnessConfig(model=model, verbose=True, max_turns=20))
    r = h.run(task)

    print(f"\n{'='*60}")
    print(f"Success: {r.success}")
    print(f"Total turns: {r.turns}")
    print(f"Tokens: {r.total_tokens:,}")
    print(f"Elapsed: {r.elapsed_sec:.1f}s")
    print(f"Tool calls: {len(r.tool_calls)}")
    if r.error:
        print(f"Error: {r.error}")
    print(f"\nFinal: {r.final_message[:300]}")
