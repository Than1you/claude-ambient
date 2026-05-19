"""Run claude_ambient.py as a subprocess and validate the hook JSON contract."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_subprocess_emits_valid_hook_json(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)  # Windows equivalent of HOME
    env["CLAUDE_TZ"] = "America/Chicago"

    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "claude_ambient.py")],
        capture_output=True, text=True, timeout=10, env=env,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)

    assert "hookSpecificOutput" in payload
    inner = payload["hookSpecificOutput"]
    assert inner["hookEventName"] == "UserPromptSubmit"
    assert isinstance(inner["additionalContext"], str)
    # default signals are time + rhythm
    assert "[time]" in inner["additionalContext"]
    assert "[rhythm]" in inner["additionalContext"]


def test_subprocess_persists_state_between_runs(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)
    env["CLAUDE_TZ"] = "America/Chicago"

    subprocess.run(
        [sys.executable, str(REPO_ROOT / "claude_ambient.py")],
        capture_output=True, text=True, timeout=10, env=env, check=True,
    )

    state_path = tmp_path / ".claude" / "claude-ambient" / "state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert "last_prompt_at" in state
