"""Tests for the timezone override chain."""
from __future__ import annotations

from zoneinfo import ZoneInfo


def test_resolve_prefers_config_over_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_TZ", "Asia/Shanghai")
    monkeypatch.setenv("TZ", "UTC")

    from claude_ambient import resolve_timezone
    tz = resolve_timezone({"timezone": "America/Chicago"})

    assert isinstance(tz, ZoneInfo)
    assert tz.key == "America/Chicago"


def test_resolve_falls_through_to_claude_tz(monkeypatch):
    monkeypatch.delenv("TZ", raising=False)
    monkeypatch.setenv("CLAUDE_TZ", "Asia/Shanghai")

    from claude_ambient import resolve_timezone
    tz = resolve_timezone({"timezone": None})

    assert tz.key == "Asia/Shanghai"


def test_resolve_falls_through_to_tz(monkeypatch):
    monkeypatch.delenv("CLAUDE_TZ", raising=False)
    monkeypatch.setenv("TZ", "Europe/London")

    from claude_ambient import resolve_timezone
    tz = resolve_timezone({"timezone": None})

    assert tz.key == "Europe/London"


def test_resolve_ignores_invalid_timezone(monkeypatch):
    monkeypatch.setenv("CLAUDE_TZ", "Mars/Olympus_Mons")
    monkeypatch.setenv("TZ", "Europe/London")

    from claude_ambient import resolve_timezone
    tz = resolve_timezone({"timezone": "Also/Invalid"})

    assert tz.key == "Europe/London"


def test_resolve_falls_back_to_utc(monkeypatch):
    monkeypatch.delenv("CLAUDE_TZ", raising=False)
    monkeypatch.delenv("TZ", raising=False)
    monkeypatch.setattr("claude_ambient._system_timezone", lambda: None)

    from claude_ambient import resolve_timezone
    tz = resolve_timezone({"timezone": None})

    assert tz.key == "UTC"
