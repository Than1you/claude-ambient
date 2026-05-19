"""A misbehaving signal must not break the hook or other signals."""
from __future__ import annotations

import json
from datetime import datetime


def test_one_signal_raising_does_not_break_others(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr("claude_ambient.STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr("claude_ambient.ERROR_LOG", tmp_path / "error.log")
    monkeypatch.setattr("claude_ambient._now", lambda tz: datetime(2026, 5, 18, 14, 0, 0, tzinfo=tz))
    monkeypatch.setenv("CLAUDE_TZ", "America/Chicago")

    import claude_ambient

    class Exploder(claude_ambient.Signal):
        name = "exploder"
        def collect(self, ctx):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "claude_ambient.SIGNAL_REGISTRY",
        [Exploder, claude_ambient.TimeSignal, claude_ambient.RhythmSignal],
    )

    rc = claude_ambient.main()
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "[time]" in ctx
    assert "[rhythm]" in ctx
    assert "boom" not in ctx
    # error log records the failure
    assert (tmp_path / "error.log").exists()
    log = (tmp_path / "error.log").read_text()
    assert "exploder" in log
    assert "boom" in log


def test_error_log_truncates_when_oversized(tmp_path, monkeypatch):
    monkeypatch.setattr("claude_ambient.ERROR_LOG", tmp_path / "error.log")
    (tmp_path / "error.log").write_text("x" * (1024 * 1024 + 100))

    import claude_ambient
    claude_ambient._log_error("dummy", "msg")

    text = (tmp_path / "error.log").read_text()
    assert len(text) < 1024 * 1024
