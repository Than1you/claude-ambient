"""Tests for TimeSignal output formatting and secondary timezones."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def _ctx(now, config_overrides=None):
    from claude_ambient import DEFAULT_CONFIG, SignalContext
    import copy
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for path, value in (config_overrides or {}).items():
        node = cfg
        keys = path.split(".")
        for k in keys[:-1]:
            node = node[k]
        node[keys[-1]] = value
    return SignalContext(now=now, state={}, config=cfg)


def test_time_signal_default_format_chicago():
    from claude_ambient import TimeSignal

    now = datetime(2026, 5, 18, 14, 24, 43, tzinfo=ZoneInfo("America/Chicago"))
    out = TimeSignal().collect(_ctx(now))

    assert out == "[time] 2026-05-18T14:24:43-05:00 (Monday, CDT, America/Chicago)"


def test_time_signal_full_day_name_for_sunday():
    from claude_ambient import TimeSignal

    now = datetime(2026, 5, 17, 9, 0, 0, tzinfo=ZoneInfo("America/Chicago"))
    out = TimeSignal().collect(_ctx(now))

    assert "(Sunday, " in out


def test_time_signal_iso_only_format():
    from claude_ambient import TimeSignal

    now = datetime(2026, 5, 18, 14, 24, 43, tzinfo=ZoneInfo("America/Chicago"))
    out = TimeSignal().collect(_ctx(now, {"signals.time.format": "iso"}))

    assert out == "[time] 2026-05-18T14:24:43-05:00"


def test_time_signal_secondary_zones_with_day_crossing():
    from claude_ambient import TimeSignal

    now = datetime(2026, 5, 18, 14, 24, 43, tzinfo=ZoneInfo("America/Chicago"))
    out = TimeSignal().collect(_ctx(now, {"secondary_timezones": ["UTC", "Asia/Shanghai"]}))

    # In Shanghai it is the next calendar day (+1)
    assert "(also: 19:24 UTC, 03:24+1 Asia/Shanghai)" in out


def test_time_signal_disabled_returns_none():
    from claude_ambient import TimeSignal

    now = datetime(2026, 5, 18, 14, 24, 43, tzinfo=ZoneInfo("America/Chicago"))
    out = TimeSignal().collect(_ctx(now, {"signals.time.enabled": False}))

    assert out is None


def test_time_signal_dst_winter_shows_cst():
    from claude_ambient import TimeSignal

    now = datetime(2026, 1, 15, 14, 24, 43, tzinfo=ZoneInfo("America/Chicago"))
    out = TimeSignal().collect(_ctx(now))

    assert "(Thursday, CST, America/Chicago)" in out
    assert "-06:00" in out
