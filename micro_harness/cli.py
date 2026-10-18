"""Command-line entry point for the ``mh`` console script.

    mh --help
    mh route "Write tests for the critic_check function"   # offline, no API key
    mh run "Create hello.txt with 'hi'"                    # Anthropic backend

``route`` only uses the keyword router (micro_harness.router), so it never
calls a model. ``run`` drives micro_harness.core.MicroHarness, which uses the
Anthropic SDK (``pip install 'micro-harness[anthropic]'`` and set
ANTHROPIC_API_KEY).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__


def _cmd_route(args: argparse.Namespace) -> int:
    from .router import route

    available = [m.strip() for m in args.available.split(",")] if args.available else None
    print(json.dumps(route(args.task, available), indent=2, ensure_ascii=False))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        from .core import HarnessConfig, MicroHarness
    except ImportError as exc:  # anthropic is an optional dependency
        print(f"mh run needs the Anthropic SDK ({exc}).\n"
              "Install it with: pip install 'micro-harness[anthropic]'", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("mh run needs ANTHROPIC_API_KEY to be set.", file=sys.stderr)
        return 2

    if args.cwd:
        os.chdir(args.cwd)   # tools act on the process working directory
    config = HarnessConfig(
        model=args.model,
        max_turns=args.max_turns,
        critic_mode=args.critic,
        verbose=not args.quiet,
    )
    result = MicroHarness(config).run(args.task, cwd=os.getcwd())

    print("\n" + "=" * 60)
    print(f"Success: {result.success}")
    print(f"Turns: {result.turns}")
    print(f"Tokens: {result.total_tokens:,} (in={result.input_tokens:,} out={result.output_tokens:,})")
    print(f"Elapsed: {result.elapsed_sec:.1f}s")
    print(f"Tool calls: {len(result.tool_calls)}")
    if result.error:
        print(f"Error: {result.error}")
    return 0 if result.success else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mh",
        description="micro-harness: a minimal agent harness with honest benchmarks.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_route = sub.add_parser("route", help="pick a model for a task (offline keyword router)")
    p_route.add_argument("task", help="task description")
    p_route.add_argument("--available", metavar="M1,M2",
                         help="comma-separated models you can use; falls back among these")
    p_route.set_defaults(func=_cmd_route)

    p_run = sub.add_parser("run", help="run a task with the Anthropic-backed harness")
    p_run.add_argument("task", help="task description")
    p_run.add_argument("--model", default="claude-sonnet-4-5",
                       help="Anthropic model id (default: %(default)s)")
    p_run.add_argument("--max-turns", type=int, default=30, help="default: %(default)s")
    p_run.add_argument("--critic", choices=["off", "allowlist"], default="off",
                       help="shell-command critic mode (default: %(default)s)")
    p_run.add_argument("--cwd", help="directory to work in (default: current directory)")
    p_run.add_argument("--quiet", action="store_true", help="don't print each turn")
    p_run.set_defaults(func=_cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
