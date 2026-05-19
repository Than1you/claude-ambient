"""Integration of main() with default signals via direct invocation."""
from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo


CHI = ZoneInfo("America/Chicago")


def _isolate(tmp_path, monkeypatch):
    """Point CONFIG_DIR / CONFIG_PATH / STATE_PATH at a temp directory."""
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr("claude_ambient.STATE_PATH", tmp_path / "state.json")


def test_main_emits_hook_json_with_time_and_rhythm(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    monkeypatch.setattr("claude_ambient._now", lambda tz: datetime(2026, 5, 18, 14, 24, 43, tzinfo=tz))
    monkeypatch.setenv("CLAUDE_TZ", "America/Chicago")

    import claude_ambient
    rc = claude_ambient.main()
    captured = capsys.readouterr()

    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "[time] 2026-05-18T14:24:43-05:00 (Monday, CDT, America/Chicago)" in ctx
    assert "[rhythm] Δ since last prompt: first prompt (no prior state) · working hours" in ctx


def test_main_persists_last_prompt(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    monkeypatch.setattr("claude_ambient._now", lambda tz: datetime(2026, 5, 18, 14, 24, 43, tzinfo=tz))
    monkeypatch.setenv("CLAUDE_TZ", "America/Chicago")

    import claude_ambient
    claude_ambient.main()
    capsys.readouterr()

    state = json.loads((tmp_path / "state.json").read_text())
    assert state["last_prompt_at"] == "2026-05-18T14:24:43-05:00"


def test_main_second_call_reports_delta(tmp_path, monkeypatch, capsys):
    _isolate(tmp_path, monkeypatch)
    monkeypatch.setenv("CLAUDE_TZ", "America/Chicago")

    import claude_ambient

    monkeypatch.setattr("claude_ambient._now", lambda tz: datetime(2026, 5, 18, 14, 0, 0, tzinfo=tz))
    claude_ambient.main()
    capsys.readouterr()

    monkeypatch.setattr("claude_ambient._now", lambda tz: datetime(2026, 5, 18, 14, 12, 0, tzinfo=tz))
    claude_ambient.main()
    out = capsys.readouterr().out

    payload = json.loads(out)
    assert "Δ since last prompt: 12 min" in payload["hookSpecificOutput"]["additionalContext"]
