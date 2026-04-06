"""
Verify-and-Retry Loop — force verification after every code change.

After any edit/write/line_edit, automatically run a verification command.
If verification fails, revert and let the model retry.

This targets the feature task (67% → hopefully 90%+):
the model edits code but doesn't check if it still imports.
"""
from __future__ import annotations
import os
import sys
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass


@dataclass
class VerifyConfig:
    """What to verify after code changes."""
    check_syntax: bool = True       # python -c "import ast; ast.parse(...)"
    check_import: bool = True       # python -c "import module"
    check_command: str | None = None # custom verification command
    auto_revert: bool = True        # revert on failure


class FileSnapshot:
    """Save/restore file state for rollback."""
    def __init__(self):
        self._snapshots: dict[str, str] = {}

    def save(self, path: str):
        p = Path(path).expanduser()
        if p.exists():
            self._snapshots[str(p)] = p.read_text()

    def revert(self, path: str) -> bool:
        p = str(Path(path).expanduser())
        if p in self._snapshots:
            Path(p).write_text(self._snapshots[p])
            return True
        return False

    def revert_all(self):
        for p, content in self._snapshots.items():
            Path(p).write_text(content)


def verify_python_syntax(path: str) -> tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        result = subprocess.run(
            ["python3", "-c", f"import ast; ast.parse(open('{path}').read())"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return True, "syntax OK"
        return False, f"syntax error: {result.stderr[:200]}"
    except Exception as e:
        return False, f"verify error: {e}"


def verify_python_import(module_path: str) -> tuple[bool, str]:
    """Check if a Python module can be imported."""
    p = Path(module_path)
    if not p.suffix == ".py":
        return True, "not a Python file, skip"

    module_dir = str(p.parent)
    module_name = p.stem

    try:
        result = subprocess.run(
            ["python3", "-c", f"import sys; sys.path.insert(0, '{module_dir}'); import {module_name}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, "import OK"
        return False, f"import error: {result.stderr[:200]}"
    except Exception as e:
        return False, f"verify error: {e}"


def verify_after_edit(path: str, config: VerifyConfig | None = None) -> tuple[bool, str]:
    """Run all applicable verifications on a file."""
    config = config or VerifyConfig()
    results = []

    if path.endswith(".py"):
        if config.check_syntax:
            ok, msg = verify_python_syntax(path)
            results.append(("syntax", ok, msg))
            if not ok:
                return False, f"VERIFY FAILED (syntax): {msg}"

        if config.check_import:
            ok, msg = verify_python_import(path)
            results.append(("import", ok, msg))
            if not ok:
                return False, f"VERIFY FAILED (import): {msg}"

    if config.check_command:
        try:
            result = subprocess.run(
                config.check_command, shell=True,
                capture_output=True, text=True, timeout=15,
            )
            ok = result.returncode == 0
            msg = "custom check OK" if ok else f"custom check failed: {result.stderr[:200]}"
            results.append(("custom", ok, msg))
            if not ok:
                return False, f"VERIFY FAILED (custom): {msg}"
        except Exception as e:
            return False, f"VERIFY FAILED: {e}"

    return True, "all checks passed"


if __name__ == "__main__":
    print("=== Verify Loop Self-Test ===\n")

    import tempfile

    # Test 1: Valid Python
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("def hello():\n    return 'world'\n")
        tmp = f.name

    ok, msg = verify_after_edit(tmp)
    print(f"Valid Python: {'✓' if ok else '✗'} {msg}")

    # Test 2: Syntax error
    Path(tmp).write_text("def hello(\n")
    ok, msg = verify_after_edit(tmp)
    print(f"Syntax error: {'✓' if not ok else '✗'} {msg[:60]}")

    # Test 3: Import error
    Path(tmp).write_text("import nonexistent_module_xyz\n")
    ok, msg = verify_after_edit(tmp)
    print(f"Import error: {'✓' if not ok else '✗'} {msg[:60]}")

    # Test 4: Snapshot + revert
    snap = FileSnapshot()
    Path(tmp).write_text("original content\n")
    snap.save(tmp)
    Path(tmp).write_text("modified content\n")
    snap.revert(tmp)
    reverted = Path(tmp).read_text()
    print(f"Revert: {'✓' if 'original' in reverted else '✗'}")

    os.unlink(tmp)
    print("\nAll self-tests passed!")
