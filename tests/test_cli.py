"""Offline tests for the `mh` console script (no API key, no network)."""
import json
import shutil
import subprocess
import sys

import pytest

from micro_harness import __version__, cli


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "route" in out and "run" in out


def test_no_command_prints_help(capsys):
    assert cli.main([]) == 0
    assert "usage: mh" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert __version__ in capsys.readouterr().out


def test_route_is_offline_and_returns_json(capsys):
    assert cli.main(["route", "Write tests for the critic_check function"]) == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["task_category"] == "test"
    assert decision["model"] == "GLM-4.7"


def test_route_respects_available_models(capsys):
    cli.main(["route", "Refactor this module", "--available", "DeepSeek-V3.2"])
    assert json.loads(capsys.readouterr().out)["model"] == "DeepSeek-V3.2"


def test_run_without_key_fails_cleanly(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert cli.main(["run", "anything"]) == 2
    assert "ANTHROPIC" in capsys.readouterr().err.upper()


@pytest.mark.skipif(shutil.which("mh") is None, reason="package not installed")
def test_installed_console_script():
    r = subprocess.run(["mh", "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "usage: mh" in r.stdout


def test_python_dash_m():
    r = subprocess.run([sys.executable, "-m", "micro_harness.cli", "--help"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
