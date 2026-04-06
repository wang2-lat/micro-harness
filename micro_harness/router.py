"""
Model Router — auto-select the best model for each task type.

Based on our 7-model benchmark data:
- GPT-5.4: fastest agent, best at refactoring
- Claude Sonnet: most token-efficient, best at comprehensive tasks
- DeepSeek: cheapest, good enough for analysis/debug/simple features
- GLM-4.7: best at legal/structured writing

Strategy: classify task with cheap model, route to best model.
"""
from __future__ import annotations
import os
import sys
import re
from pathlib import Path

from openai import OpenAI


TASK_CATEGORIES = {
    "analysis": {
        "keywords": ["compare", "analyze", "report", "difference", "review", "explain"],
        "best_model": "DeepSeek-V3.2",
        "reason": "analysis tasks pass 3/3 on DeepSeek, no need for expensive model",
    },
    "debug": {
        "keywords": ["bug", "fix", "error", "crash", "broken", "debug", "failing"],
        "best_model": "DeepSeek-V3.2",
        "reason": "debug tasks pass 3/3 on DeepSeek",
    },
    "feature": {
        "keywords": ["add", "create", "implement", "build", "new tool", "new function"],
        "best_model": "DeepSeek-V3.2",
        "reason": "feature tasks pass 2/3 on DeepSeek, good enough for most",
    },
    "refactor": {
        "keywords": ["refactor", "configurable", "extract", "rename", "reorganize", "clean up", "type hint", "optimize", "reduce memory", "itertools"],
        "best_model": "claude-sonnet-4-6",
        "reason": "refactor 0/9 on DeepSeek, 1/1 on Claude Sonnet (10 turns, 23K tok)",
    },
    "test": {
        "keywords": ["test", "unittest", "pytest", "assert", "coverage", "spec"],
        "best_model": "GLM-4.7",
        "reason": "GLM passed test-gen while DeepSeek failed; GLM better at structured output",
    },
    "bugfix": {
        "keywords": ["silent", "error handling", "fix the", "patch", "doesn't handle", "exit code", "prefix", "flag error"],
        "best_model": "claude-sonnet-4-6",
        "reason": "bugfix 0/9 on DeepSeek, 1/1 on Claude Sonnet",
    },
    "legal": {
        "keywords": ["legal", "law", "regulation", "case", "court", "compliance", "memo"],
        "best_model": "GLM-4.7",
        "reason": "GLM-4.7 won 4-model legal comparison (5 turns, 18K tok)",
    },
    "finance": {
        "keywords": ["stock", "financial", "revenue", "SEC", "earnings", "equity", "trading"],
        "best_model": "DeepSeek-V3.2",
        "reason": "financial data tasks are structured, DeepSeek handles them fine",
    },
}

# Model pricing (approximate, per 1M tokens)
MODEL_COSTS = {
    "DeepSeek-V3.2": {"input": 0.27, "output": 1.10},
    "GLM-4.7": {"input": 0.50, "output": 2.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "gpt-5.4": {"input": 2.50, "output": 10.00},
}


def classify_task(task: str) -> tuple[str, dict]:
    """Classify a task by keyword matching. Specific categories checked first."""
    task_lower = task.lower()

    # Priority order: check specific categories before generic ones
    priority = ["refactor", "bugfix", "test", "legal", "finance", "debug", "analysis", "feature"]

    for category in priority:
        info = TASK_CATEGORIES[category]
        matches = sum(1 for kw in info["keywords"] if kw in task_lower)
        if matches > 0:
            return category, info

    return "general", {
        "best_model": "DeepSeek-V3.2",
        "reason": "no specific category matched, using cheapest model",
    }


def route(task: str, available_models: list[str] | None = None) -> dict:
    """Route a task to the best model. Returns routing decision."""
    category, info = classify_task(task)
    best = info["best_model"]

    if available_models and best not in available_models:
        # Fallback to cheapest available
        for fallback in ["DeepSeek-V3.2", "GLM-4.7", "claude-sonnet-4-6", "gpt-5.4"]:
            if fallback in available_models:
                best = fallback
                break

    return {
        "task_category": category,
        "model": best,
        "reason": info["reason"],
        "estimated_cost": MODEL_COSTS.get(best, {}),
    }


if __name__ == "__main__":
    tests = [
        "Compare harness.py and openai_harness.py",
        "The tool output truncation is hardcoded. Make it configurable.",
        "Write tests for the critic_check function",
        "Create a Python script with a bug, then find and fix it",
        "The tool_grep function can fail silently. Fix the error handling.",
        "Research AI regulation case law and write a legal memo",
        "Analyze AAPL stock performance and generate a report",
        "Add a new directory listing tool to the harness",
    ]

    print("Task Router Demo\n" + "=" * 60)
    for task in tests:
        r = route(task)
        print(f"\nTask: {task[:55]}...")
        print(f"  → {r['task_category']} → {r['model']}")
        print(f"  Reason: {r['reason'][:60]}")
