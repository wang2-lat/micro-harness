"""
micro-harness: The smallest agent harness you can learn from.

Single file, ~400 lines. Each section is labeled with the technique it demonstrates.
Reads like a textbook. Runs like a production harness.
"""
from __future__ import annotations
import os
import sys
import subprocess
import time
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable

import anthropic


# ═══════════════════════════════════════════════════════════════
# TECHNIQUE 2: Tool System — 5 structured tools, no shell parsing
# ═══════════════════════════════════════════════════════════════

TOOLS_SCHEMA = [
    {
        "name": "read",
        "description": "Read a file. Returns content with line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path"},
                "start_line": {"type": "integer", "default": 1},
                "limit": {"type": "integer", "default": 500},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write",
        "description": "Write content to a file (creates or overwrites).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit",
        "description": "Replace exact text in a file. old_string must match exactly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "bash",
        "description": "Execute a shell command. Returns stdout+stderr+exit_code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["command"],
        },
    },
    {
        "name": "grep",
        "description": "Search for pattern in files using ripgrep.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
                "glob": {"type": "string", "description": "File glob like *.py"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "tree",
        "description": "Show directory structure like the unix 'tree' command but implemented in pure Python (no subprocess).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": ".", "description": "Directory path to show tree for"},
                "max_depth": {"type": "integer", "default": 3, "description": "Maximum depth to traverse"},
            },
            "required": [],
        },
    },
]


def tool_read(path: str, start_line: int = 1, limit: int = 500) -> str:
    """Read a file with line numbers.
    Returns content with line numbers or error message if file not found."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: File not found: {path}"
    try:
        lines = p.read_text().splitlines()
    except Exception as e:
        return f"ERROR: {e}"
    end = min(start_line - 1 + limit, len(lines))
    numbered = [f"{i+1:5}→{lines[i]}" for i in range(start_line - 1, end)]
    return "\n".join(numbered) if numbered else "(empty file)"


def tool_write(path: str, content: str) -> str:
    """Write content to a file, creating directories if needed.
    Returns success message with byte count or error message."""
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} bytes to {path}"


def tool_edit(path: str, old_string: str, new_string: str) -> str:
    """Replace exact text in a file. old_string must match exactly.
    Returns success message or error if file not found or string not unique."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: File not found: {path}"
    content = p.read_text()
    count = content.count(old_string)
    if count == 0:
        return "ERROR: old_string not found in file"
    if count > 1:
        return f"ERROR: old_string appears {count} times; needs to be unique"
    p.write_text(content.replace(old_string, new_string, 1))
    return "Edit applied"


def tool_bash(command: str, timeout: int = 30) -> str:
    """Execute a shell command with timeout.
    Returns exit code, stdout (last 4000 chars), and stderr (last 1000 chars)."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=os.getcwd(),
        )
        out = result.stdout[-4000:] if result.stdout else ""
        err = result.stderr[-1000:] if result.stderr else ""
        return f"exit={result.returncode}\n{out}{'--stderr--' + chr(10) + err if err else ''}"
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"


def tool_grep(pattern: str, path: str = ".", glob: str | None = None) -> str:
    """Search for pattern in files using ripgrep.
    Returns matching lines with line numbers or error if rg not installed."""
    cmd = ["rg", "-n", pattern, path]
    if glob:
        cmd.extend(["-g", glob])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Check exit code
        if result.returncode == 0:
            # Success with matches
            out = result.stdout[:4000] if result.stdout else ""
            # Check if output is empty or contains only whitespace
            return out if out and not out.isspace() else "(no matches)"
        elif result.returncode == 1:
            # No matches found
            return "(no matches)"
        else:
            # Error from ripgrep (exit code 2 or other)
            if result.stderr and result.stderr.strip():
                error_msg = result.stderr.strip()
            else:
                error_msg = f"ripgrep failed with exit code {result.returncode}"
            return f"ERROR: {error_msg}"
    except FileNotFoundError:
        return "ERROR: ripgrep (rg) not installed"
    except subprocess.TimeoutExpired:
        return "ERROR: grep timeout"
    except Exception as e:
        return f"ERROR: {e}"


def tool_tree(path: str = ".", max_depth: int = 3) -> str:
    """Show directory structure like the unix 'tree' command in pure Python.
    Returns string representation of directory tree up to max_depth."""
    from pathlib import Path
    
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: Path not found: {path}"
    if not p.is_dir():
        return f"ERROR: Not a directory: {path}"
    
    result_lines = []
    
    def build_tree(current_path: Path, prefix: str = "", depth: int = 0, is_last: bool = True):
        if depth > max_depth:
            return
            
        # Add current directory/file to output
        if depth == 0:
            # For root, show the path or just the directory name
            display_name = str(current_path) if path == "." else current_path.name
            result_lines.append(f"{display_name}/")
        else:
            connector = "└── " if is_last else "├── "
            result_lines.append(f"{prefix}{connector}{current_path.name}")
        
        if current_path.is_dir():
            # Get sorted list of entries, directories first
            try:
                entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                result_lines.append(f"{prefix}    [Permission denied]")
                return
                
            # Update prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            # Process each child
            for i, child in enumerate(entries):
                is_last_child = (i == len(entries) - 1)
                if child.is_dir():
                    build_tree(child, child_prefix, depth + 1, is_last_child)
                else:
                    if depth + 1 <= max_depth:
                        connector = "└── " if is_last_child else "├── "
                        result_lines.append(f"{child_prefix}{connector}{child.name}")
    
    build_tree(p)
    return "\n".join(result_lines)


TOOL_DISPATCH: dict[str, Callable] = {
    "read": tool_read,
    "write": tool_write,
    "edit": tool_edit,
    "bash": tool_bash,
    "grep": tool_grep,
    "tree": tool_tree,
}


# ═══════════════════════════════════════════════════════════════
# TECHNIQUE 7: Critic Permissions — ask cheap model before bash
# ═══════════════════════════════════════════════════════════════

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bdd\s+if=.*of=/dev/",
    r"mkfs\.",
    r":\(\)\{.*:\|:\s*\&\s*\};:",  # fork bomb
    r">\s*/dev/sd[a-z]",
    r"chmod\s+-R\s+777\s+/",
    r"curl.*\|\s*sh",
    r"wget.*\|\s*bash",
]


def critic_check(command: str, critic_mode: str = "allowlist") -> tuple[bool, str]:
    """Returns (allowed, reason)."""
    # Always block obvious disasters
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return False, f"BLOCKED: matches dangerous pattern {pattern!r}"

    if critic_mode == "allowlist":
        # Conservative: only explicit whitelist
        safe_prefixes = ("ls", "cat", "head", "tail", "echo", "pwd", "wc", "grep",
                         "find", "which", "date", "env", "python", "node", "git status",
                         "git log", "git diff", "npm list", "pip list", "rg")
        if any(command.strip().startswith(p) for p in safe_prefixes):
            return True, "allowlist match"
        return False, "not in allowlist"

    if critic_mode == "off":
        return True, "critic disabled"

    return True, "default allow"


# ═══════════════════════════════════════════════════════════════
# TECHNIQUE 4: Environment Bootstrap — save 2-5 exploration turns
# ═══════════════════════════════════════════════════════════════

def bootstrap_env(cwd: str | None = None) -> str:
    """Inject environment snapshot at turn 0. Meta-Harness's winning trick."""
    cwd = cwd or os.getcwd()
    lines = [f"=== Environment Bootstrap @ {cwd} ==="]

    # Directory listing (top level only)
    try:
        entries = sorted(os.listdir(cwd))[:30]
        lines.append(f"Files: {', '.join(entries) if entries else '(empty)'}")
    except Exception:
        pass

    # Runtime versions
    for cmd in ["python3 --version", "node --version"]:
        try:
            r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                lines.append(f"{cmd}: {r.stdout.strip() or r.stderr.strip()}")
        except Exception:
            pass

    # Git state
    try:
        r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True,
                           timeout=3, cwd=cwd)
        if r.returncode == 0:
            status = r.stdout.strip() or "(clean)"
            lines.append(f"git: {status[:200]}")
    except Exception:
        pass

    # Project manifest
    for mf in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod"]:
        p = Path(cwd) / mf
        if p.exists():
            lines.append(f"manifest: {mf} present")
            break

    lines.append("=== end bootstrap ===")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# TECHNIQUE 5: Three-Layer Memory — lazy skill loading
# ═══════════════════════════════════════════════════════════════

def build_file_index(root: str, max_files: int = 100) -> str:
    """Layer 1: lightweight file index (always in prompt)."""
    ignore = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
    files = []
    for p in Path(root).rglob("*"):
        if any(part in ignore for part in p.parts):
            continue
        if p.is_file() and not p.name.startswith("."):
            files.append(str(p.relative_to(root)))
        if len(files) >= max_files:
            break
    return "\n".join(sorted(files))


# ═══════════════════════════════════════════════════════════════
# TECHNIQUE 3: Cache Boundary — stable prefix vs dynamic suffix
# ═══════════════════════════════════════════════════════════════

def build_system_prompt(
    base_instructions: str,
    file_index: str | None = None,
    use_cache: bool = True,
) -> list[dict]:
    """
    Split system prompt into cached stable prefix + uncached dynamic suffix.
    Returns list of content blocks for the Messages API.
    """
    stable_parts = [
        "You are micro-harness, a minimal coding agent.",
        "",
        base_instructions,
    ]
    if file_index:
        stable_parts.extend(["", "=== Project Files (Layer 1 Index) ===", file_index])

    stable = "\n".join(stable_parts)

    # Dynamic suffix: current state that changes per session
    dynamic = (
        f"=== Session Context ===\n"
        f"CWD: {os.getcwd()}\n"
        f"Date: {time.strftime('%Y-%m-%d %H:%M')}\n"
    )

    if use_cache:
        # Mark stable part for caching
        return [
            {"type": "text", "text": stable, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": dynamic},
        ]
    else:
        return [{"type": "text", "text": stable + "\n" + dynamic}]


# ═══════════════════════════════════════════════════════════════
# TECHNIQUE 1 + 6: Agent Loop with Circuit Breakers
# ═══════════════════════════════════════════════════════════════

@dataclass
class HarnessConfig:
    model: str = "claude-sonnet-4-5"
    max_turns: int = 30
    max_tokens_total: int = 500_000
    max_consecutive_errors: int = 3
    max_tool_output: int = 8000
    use_cache: bool = True
    use_bootstrap: bool = True
    use_file_index: bool = True
    critic_mode: str = "off"  # off | allowlist
    verbose: bool = True
    max_tool_output: int = 8000


@dataclass
class HarnessResult:
    success: bool
    turns: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    final_message: str
    error: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    elapsed_sec: float = 0.0


class MicroHarness:
    def __init__(self, config: HarnessConfig | None = None):
        self.config = config or HarnessConfig()
        self.client = anthropic.Anthropic()
        self.messages: list[dict] = []
        self.tokens_used = 0
        self.consecutive_errors = 0

    def log(self, msg: str):
        if self.config.verbose:
            print(msg, flush=True)

    def run(self, task: str, cwd: str | None = None) -> HarnessResult:
        start = time.time()
        c = self.config

        # Build system prompt (TECHNIQUE 3 + 5)
        file_index = build_file_index(cwd or os.getcwd()) if c.use_file_index else None
        system = build_system_prompt(
            base_instructions=(
                "Use tools to complete the user's task. "
                "When finished, output a final message summarizing what you did."
            ),
            file_index=file_index,
            use_cache=c.use_cache,
        )

        # Bootstrap (TECHNIQUE 4)
        first_user = task
        if c.use_bootstrap:
            first_user = bootstrap_env(cwd) + "\n\nTask: " + task

        self.messages = [{"role": "user", "content": first_user}]
        tool_calls_log: list[str] = []

        # Agent loop (TECHNIQUE 1) with circuit breakers (TECHNIQUE 6)
        input_tok = output_tok = cache_read = cache_create = 0

        for turn in range(c.max_turns):
            # Fuse: token budget
            if self.tokens_used > c.max_tokens_total:
                return HarnessResult(
                    success=False, turns=turn, total_tokens=self.tokens_used,
                    input_tokens=input_tok, output_tokens=output_tok,
                    cache_read_tokens=cache_read, cache_creation_tokens=cache_create,
                    final_message="", error="token budget exceeded",
                    tool_calls=tool_calls_log, elapsed_sec=time.time() - start,
                )

            # Fuse: consecutive errors
            if self.consecutive_errors >= c.max_consecutive_errors:
                return HarnessResult(
                    success=False, turns=turn, total_tokens=self.tokens_used,
                    input_tokens=input_tok, output_tokens=output_tok,
                    cache_read_tokens=cache_read, cache_creation_tokens=cache_create,
                    final_message="", error=f"{c.max_consecutive_errors} consecutive errors",
                    tool_calls=tool_calls_log, elapsed_sec=time.time() - start,
                )

            try:
                response = self.client.messages.create(
                    model=c.model,
                    max_tokens=4096,
                    system=system,
                    tools=TOOLS_SCHEMA,
                    messages=self.messages,
                )
            except Exception as e:
                self.consecutive_errors += 1
                self.log(f"[turn {turn}] API error: {e}")
                time.sleep(2)
                continue

            # Track tokens
            usage = response.usage
            input_tok += usage.input_tokens
            output_tok += usage.output_tokens
            cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
            cache_create += getattr(usage, "cache_creation_input_tokens", 0) or 0
            self.tokens_used = input_tok + output_tok

            self.consecutive_errors = 0

            # Extract assistant message
            assistant_content = response.content
            self.messages.append({"role": "assistant", "content": assistant_content})

            # Check stop reason
            if response.stop_reason == "end_turn":
                text = ""
                for block in assistant_content:
                    if block.type == "text":
                        text += block.text
                self.log(f"[turn {turn}] DONE: {text[:200]}")
                return HarnessResult(
                    success=True, turns=turn + 1, total_tokens=self.tokens_used,
                    input_tokens=input_tok, output_tokens=output_tok,
                    cache_read_tokens=cache_read, cache_creation_tokens=cache_create,
                    final_message=text, tool_calls=tool_calls_log,
                    elapsed_sec=time.time() - start,
                )

            # Execute tools
            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue
                tool_name = block.name
                tool_input = block.input
                tool_calls_log.append(f"{tool_name}({json.dumps(tool_input)[:100]})")

                self.log(f"[turn {turn}] → {tool_name}({str(tool_input)[:80]})")

                # Critic check for bash
                if tool_name == "bash" and c.critic_mode != "off":
                    allowed, reason = critic_check(tool_input.get("command", ""), c.critic_mode)
                    if not allowed:
                        result = f"BLOCKED BY CRITIC: {reason}"
                        self.log(f"  ⛔ {result}")
                        tool_results.append({
                            "type": "tool_result", "tool_use_id": block.id,
                            "content": result, "is_error": True,
                        })
                        continue

                # Execute
                try:
                    fn = TOOL_DISPATCH[tool_name]
                    result = fn(**tool_input)
                    result_str = str(result)[:self.config.max_tool_output]
                    self.log(f"  ← {result_str[:150]}")
                    # Check if result starts with "ERROR:" to set is_error flag
                    is_error = result_str.startswith("ERROR:")
                    tool_results.append({
                        "type": "tool_result", "tool_use_id": block.id,
                        "content": result_str,
                        "is_error": is_error,
                    })
                except Exception as e:
                    self.log(f"  ← ERROR: {e}")
                    tool_results.append({
                        "type": "tool_result", "tool_use_id": block.id,
                        "content": f"ERROR: {e}", "is_error": True,
                    })

            self.messages.append({"role": "user", "content": tool_results})

        # Max turns hit
        return HarnessResult(
            success=False, turns=c.max_turns, total_tokens=self.tokens_used,
            input_tokens=input_tok, output_tokens=output_tok,
            cache_read_tokens=cache_read, cache_creation_tokens=cache_create,
            final_message="", error=f"max_turns ({c.max_turns}) reached",
            tool_calls=tool_calls_log, elapsed_sec=time.time() - start,
        )


# ═══════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python harness.py '<task>'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    harness = MicroHarness()
    result = harness.run(task)

    print("\n" + "=" * 60)
    print(f"Success: {result.success}")
    print(f"Turns: {result.turns}")
    print(f"Tokens: {result.total_tokens:,} (in={result.input_tokens:,} out={result.output_tokens:,})")
    print(f"Cache: read={result.cache_read_tokens:,} created={result.cache_creation_tokens:,}")
    print(f"Elapsed: {result.elapsed_sec:.1f}s")
    print(f"Tool calls: {len(result.tool_calls)}")
    if result.error:
        print(f"Error: {result.error}")
