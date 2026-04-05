"""
Benchmark runner: test each harness technique in isolation.

For each task, runs harness with different configurations and measures:
- Success rate
- Token cost (with cache savings)
- Number of turns
- Elapsed time
- Tool call count

Output: JSON table + markdown report.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from pathlib import Path
from dataclasses import asdict

# Import harness
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from harness import MicroHarness, HarnessConfig, HarnessResult


TASKS_FILE = Path(__file__).parent.parent / "tasks" / "tasks.json"


def validate(task: dict, result: HarnessResult) -> bool:
    """Check if the task was actually completed correctly."""
    if not result.success:
        return False

    kind = task["validator"]
    msg = result.final_message

    if kind == "contains_all":
        return all(e in msg for e in task["expected"])
    if kind == "contains_any":
        return any(e in msg for e in task["expected"])
    if kind == "contains_both":
        return all(e in msg for e in task["expected"])
    if kind == "regex":
        return bool(re.search(task["expected"], msg))
    if kind == "file_contains":
        p = Path(task["expected_path"])
        if not p.exists():
            return False
        return task["expected_text"] in p.read_text()
    return False


def run_task(task: dict, config: HarnessConfig) -> dict:
    """Run a single task with given config. Returns result dict."""
    harness = MicroHarness(config)
    result = harness.run(task["prompt"])
    validated = validate(task, result)
    return {
        "task_id": task["id"],
        "success": result.success,
        "validated": validated,
        "turns": result.turns,
        "total_tokens": result.total_tokens,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "cache_read": result.cache_read_tokens,
        "cache_creation": result.cache_creation_tokens,
        "elapsed": round(result.elapsed_sec, 1),
        "tool_calls": len(result.tool_calls),
        "error": result.error,
    }


# Experimental configurations to compare
CONFIGS = {
    "baseline": HarnessConfig(
        use_cache=False, use_bootstrap=False, use_file_index=False,
        critic_mode="off", verbose=False,
    ),
    "with_cache": HarnessConfig(
        use_cache=True, use_bootstrap=False, use_file_index=False,
        critic_mode="off", verbose=False,
    ),
    "with_bootstrap": HarnessConfig(
        use_cache=False, use_bootstrap=True, use_file_index=False,
        critic_mode="off", verbose=False,
    ),
    "with_index": HarnessConfig(
        use_cache=False, use_bootstrap=False, use_file_index=True,
        critic_mode="off", verbose=False,
    ),
    "all_optimizations": HarnessConfig(
        use_cache=True, use_bootstrap=True, use_file_index=True,
        critic_mode="off", verbose=False,
    ),
}


def run_benchmark(difficulty: str = "easy", configs: list[str] | None = None) -> dict:
    """Run all tasks at given difficulty against all configs."""
    with open(TASKS_FILE) as f:
        all_tasks = json.load(f)

    tasks = all_tasks.get(difficulty, [])
    if not tasks:
        print(f"No tasks for difficulty: {difficulty}")
        return {}

    configs_to_run = configs or list(CONFIGS.keys())
    results = {cfg_name: [] for cfg_name in configs_to_run}

    for task in tasks:
        print(f"\n━━━ Task: {task['id']} ━━━")
        for cfg_name in configs_to_run:
            cfg = CONFIGS[cfg_name]
            print(f"  → {cfg_name}...", end=" ", flush=True)
            try:
                r = run_task(task, cfg)
                results[cfg_name].append(r)
                status = "✓" if r["validated"] else "✗"
                print(f"{status} turns={r['turns']} tokens={r['total_tokens']} t={r['elapsed']}s")
            except Exception as e:
                print(f"ERROR: {e}")
                results[cfg_name].append({
                    "task_id": task["id"], "success": False,
                    "validated": False, "error": str(e),
                })

    return results


def summarize(results: dict) -> str:
    """Build markdown summary table."""
    lines = ["\n## Benchmark Results\n"]
    lines.append("| Config | Pass Rate | Avg Turns | Avg Tokens | Avg Cost$ | Avg Time |")
    lines.append("|--------|-----------|-----------|------------|-----------|----------|")

    for cfg_name, task_results in results.items():
        if not task_results:
            continue
        passed = sum(1 for r in task_results if r.get("validated"))
        total = len(task_results)
        pass_rate = f"{passed}/{total} ({passed*100//total}%)"

        valid_runs = [r for r in task_results if r.get("total_tokens")]
        if valid_runs:
            avg_turns = sum(r["turns"] for r in valid_runs) / len(valid_runs)
            avg_tokens = sum(r["total_tokens"] for r in valid_runs) / len(valid_runs)
            avg_time = sum(r["elapsed"] for r in valid_runs) / len(valid_runs)
            # Sonnet pricing: $3/M input, $15/M output, $0.30/M cache reads
            avg_cost = sum(
                (r["input_tokens"] - r.get("cache_read", 0)) * 3 / 1_000_000 +
                r.get("cache_read", 0) * 0.30 / 1_000_000 +
                r.get("cache_creation", 0) * 3.75 / 1_000_000 +
                r["output_tokens"] * 15 / 1_000_000
                for r in valid_runs
            ) / len(valid_runs)
        else:
            avg_turns = avg_tokens = avg_time = avg_cost = 0

        lines.append(
            f"| {cfg_name} | {pass_rate} | {avg_turns:.1f} | "
            f"{avg_tokens:,.0f} | ${avg_cost:.4f} | {avg_time:.1f}s |"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    difficulty = sys.argv[1] if len(sys.argv) > 1 else "easy"

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY environment variable first")
        sys.exit(1)

    print(f"Running benchmark on '{difficulty}' tasks...")
    start = time.time()
    results = run_benchmark(difficulty)
    elapsed = time.time() - start

    print(f"\n\nTotal elapsed: {elapsed:.1f}s")
    print(summarize(results))

    # Save results
    out_path = Path(__file__).parent / f"results_{difficulty}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")
