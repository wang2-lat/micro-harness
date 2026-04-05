"""Run benchmark with Gemini backend, comparing technique configs."""
import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from gemini_harness import GeminiHarness
from harness import HarnessConfig, HarnessResult

TASKS = [
    {"id": "list-files", "prompt": "List the Python files in src/ and report how many there are."},
    {"id": "read-arch", "prompt": "Read ARCHITECTURE.md and tell me how many techniques it describes."},
    {"id": "check-version", "prompt": "What Python version is installed on this system? Give the exact version string."},
    {"id": "create-run", "prompt": "Create /tmp/mh-bench.py that prints 'benchmark ok'. Run it. Report the output."},
    {"id": "count-lines", "prompt": "How many lines of code are in src/harness.py? Count and give the number."},
    {"id": "find-funcs", "prompt": "Search src/harness.py for all functions starting with 'tool_'. List their names."},
]

CONFIGS = {
    "baseline": HarnessConfig(
        model="gemini-2.5-flash", use_cache=False, use_bootstrap=False,
        use_file_index=False, critic_mode="off", verbose=False,
    ),
    "+bootstrap": HarnessConfig(
        model="gemini-2.5-flash", use_cache=False, use_bootstrap=True,
        use_file_index=False, critic_mode="off", verbose=False,
    ),
    "+index": HarnessConfig(
        model="gemini-2.5-flash", use_cache=False, use_bootstrap=False,
        use_file_index=True, critic_mode="off", verbose=False,
    ),
    "+all": HarnessConfig(
        model="gemini-2.5-flash", use_cache=False, use_bootstrap=True,
        use_file_index=True, critic_mode="off", verbose=False,
    ),
}

def run_all():
    results = {}
    for cfg_name, cfg in CONFIGS.items():
        results[cfg_name] = []
        print(f"\n{'='*50}")
        print(f"Config: {cfg_name}")
        print(f"{'='*50}")
        for task in TASKS:
            print(f"  {task['id']}...", end=" ", flush=True)
            try:
                h = GeminiHarness(cfg)
                r = h.run(task["prompt"])
                results[cfg_name].append({
                    "task": task["id"],
                    "success": r.success,
                    "turns": r.turns,
                    "tokens": r.total_tokens,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "elapsed": round(r.elapsed_sec, 1),
                    "tools": len(r.tool_calls),
                })
                status = "✓" if r.success else "✗"
                print(f"{status} turns={r.turns} tok={r.total_tokens} t={r.elapsed_sec:.1f}s")
            except Exception as e:
                print(f"ERROR: {e}")
                results[cfg_name].append({"task": task["id"], "success": False, "error": str(e)})
            time.sleep(0.5)  # Rate limit courtesy

    # Summary
    print(f"\n\n{'='*70}")
    print(f"{'Config':<15} {'Pass':>5} {'Avg Turns':>10} {'Avg Tokens':>12} {'Avg Time':>10}")
    print(f"{'='*70}")
    for cfg_name, task_results in results.items():
        valid = [r for r in task_results if r.get("tokens")]
        passed = sum(1 for r in task_results if r.get("success"))
        if valid:
            avg_turns = sum(r["turns"] for r in valid) / len(valid)
            avg_tokens = sum(r["tokens"] for r in valid) / len(valid)
            avg_time = sum(r["elapsed"] for r in valid) / len(valid)
        else:
            avg_turns = avg_tokens = avg_time = 0
        print(f"{cfg_name:<15} {passed}/{len(task_results):>3} {avg_turns:>10.1f} {avg_tokens:>12,.0f} {avg_time:>9.1f}s")

    # Save
    out = Path(__file__).parent / "gemini_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("Set GEMINI_API_KEY first"); sys.exit(1)
    run_all()
