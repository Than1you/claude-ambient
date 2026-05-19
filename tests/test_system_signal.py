"""Tests for SystemSignal: triggers only when battery / disk thresholds cross."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def _ctx(enabled=True, battery=None, disk_free_pct=None):
    from claude_ambient import DEFAULT_CONFIG, SignalContext
    import copy
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["signals"]["system"]["enabled"] = enabled
    state = {"_battery_pct": battery, "_disk_free_pct": disk_free_pct}
    return SignalContext(
        now=datetime(2026, 5, 18, 14, 0, 0, tzinfo=ZoneInfo("UTC")),
        state=state,
        config=cfg,
    )


def test_disabled_returns_none(monkeypatch):
    from claude_ambient import SystemSignal
    monkeypatch.setattr("claude_ambient.SystemSignal._read_battery_pct", lambda self: 5)
    monkeypatch.setattr("claude_ambient.SystemSignal._read_disk_free_pct", lambda self: 1)

    out = SystemSignal().collect(_ctx(enabled=False))
    assert out is None


def test_returns_none_when_nothing_notable(monkeypatch):
    from claude_ambient import SystemSignal
    monkeypatch.setattr("claude_ambient.SystemSignal._read_battery_pct", lambda self: 90)
    monkeypatch.setattr("claude_ambient.SystemSignal._read_disk_free_pct", lambda self: 50)

    out = SystemSignal().collect(_ctx(enabled=True))
    assert out is None


def test_triggers_on_low_battery(monkeypatch):
    from claude_ambient import SystemSignal
    monkeypatch.setattr("claude_ambient.SystemSignal._read_battery_pct", lambda self: 12)
    monkeypatch.setattr("claude_ambient.SystemSignal._read_disk_free_pct", lambda self: 80)

    out = SystemSignal().collect(_ctx(enabled=True))
    assert out is not None
    assert "battery 12% (low)" in out
    assert "disk" not in out


def test_triggers_on_low_disk(monkeypatch):
    from claude_ambient import SystemSignal
    monkeypatch.setattr("claude_ambient.SystemSignal._read_battery_pct", lambda self: 80)
    monkeypatch.setattr("claude_ambient.SystemSignal._read_disk_free_pct", lambda self: 4)

    out = SystemSignal().collect(_ctx(enabled=True))
    assert out is not None
    assert "disk 4% free (low)" in out
    assert "battery" not in out


def test_triggers_on_both(monkeypatch):
    from claude_ambient import SystemSignal
    monkeypatch.setattr("claude_ambient.SystemSignal._read_battery_pct", lambda self: 5)
    monkeypatch.setattr("claude_ambient.SystemSignal._read_disk_free_pct", lambda self: 2)

    out = SystemSignal().collect(_ctx(enabled=True))
    assert "battery 5% (low)" in out
    assert "disk 2% free (low)" in out
