"""Tests for RhythmSignal: Δt buckets + energy labels."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _ctx(now, last_iso=None):
    from claude_ambient import DEFAULT_CONFIG, SignalContext
    import copy
    state = {"schema_version": 1}
    if last_iso is not None:
        state["last_prompt_at"] = last_iso
    return SignalContext(now=now, state=state, config=copy.deepcopy(DEFAULT_CONFIG))


CHI = ZoneInfo("America/Chicago")


def test_first_prompt_ever():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    out = RhythmSignal().collect(_ctx(now))

    assert "first prompt (no prior state)" in out
    assert "working hours" in out


def test_delta_just_now():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 14, 0, 30, tzinfo=CHI)
    last = (now - timedelta(seconds=20)).isoformat(timespec="seconds")
    out = RhythmSignal().collect(_ctx(now, last))

    assert "Δ since last prompt: just now" in out


def test_delta_minutes():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 14, 12, 0, tzinfo=CHI)
    last = (now - timedelta(minutes=12)).isoformat(timespec="seconds")
    out = RhythmSignal().collect(_ctx(now, last))

    assert "Δ since last prompt: 12 min" in out


def test_delta_hours_minutes():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 17, 30, 0, tzinfo=CHI)
    last = (now - timedelta(hours=3, minutes=15)).isoformat(timespec="seconds")
    out = RhythmSignal().collect(_ctx(now, last))

    assert "Δ since last prompt: 3 hours 15 min" in out


def test_delta_days_marks_long_gap():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 9, 0, 0, tzinfo=CHI)
    last = (now - timedelta(days=3, hours=4)).isoformat(timespec="seconds")
    out = RhythmSignal().collect(_ctx(now, last))

    assert "Δ since last prompt: 3 days 4 hours" in out
    assert "first prompt after gap" in out


def test_energy_label_late_night():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 2, 30, 0, tzinfo=CHI)  # Monday 02:30
    out = RhythmSignal().collect(_ctx(now))
    assert "late night" in out


def test_energy_label_early_morning():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 6, 30, 0, tzinfo=CHI)  # Monday 06:30
    out = RhythmSignal().collect(_ctx(now))
    assert "early morning" in out


def test_energy_label_working_hours():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 10, 0, 0, tzinfo=CHI)  # Monday 10:00
    out = RhythmSignal().collect(_ctx(now))
    assert "working hours" in out


def test_energy_label_evening():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 18, 20, 0, 0, tzinfo=CHI)  # Monday 20:00
    out = RhythmSignal().collect(_ctx(now))
    assert "evening" in out


def test_weekend_morning():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 16, 9, 0, 0, tzinfo=CHI)  # Saturday
    out = RhythmSignal().collect(_ctx(now))
    assert "weekend morning" in out


def test_weekend_afternoon():
    from claude_ambient import RhythmSignal

    now = datetime(2026, 5, 17, 14, 0, 0, tzinfo=CHI)  # Sunday
    out = RhythmSignal().collect(_ctx(now))
    assert "weekend afternoon" in out


def test_rhythm_disabled_returns_none():
    from claude_ambient import DEFAULT_CONFIG, RhythmSignal, SignalContext
    import copy

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["signals"]["rhythm"]["enabled"] = False
    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    ctx = SignalContext(now=now, state={}, config=cfg)

    assert RhythmSignal().collect(ctx) is None
