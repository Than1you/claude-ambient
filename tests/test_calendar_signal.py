"""Tests for CalendarSignal: read next event from a local .ics file."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


CHI = ZoneInfo("America/Chicago")


def _ctx(now, enabled, ics_path=None, window=90):
    from claude_ambient import DEFAULT_CONFIG, SignalContext
    import copy
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["signals"]["calendar"]["enabled"] = enabled
    cfg["signals"]["calendar"]["window_minutes"] = window
    if ics_path is not None:
        cfg["signals"]["calendar"]["_test_ics_path"] = str(ics_path)
    return SignalContext(now=now, state={}, config=cfg)


def _write_ics(path, summary, start_utc):
    body = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "BEGIN:VEVENT\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    path.write_text(body)


def test_calendar_disabled_returns_none(tmp_path):
    from claude_ambient import CalendarSignal

    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    out = CalendarSignal().collect(_ctx(now, enabled=False))
    assert out is None


def test_calendar_missing_file_returns_none(tmp_path):
    from claude_ambient import CalendarSignal

    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    out = CalendarSignal().collect(_ctx(now, enabled=True, ics_path=tmp_path / "does_not_exist.ics"))
    assert out is None


def test_calendar_reports_next_event_within_window(tmp_path):
    from claude_ambient import CalendarSignal

    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    start_utc = (now.astimezone(ZoneInfo("UTC")) + timedelta(minutes=25)).replace(tzinfo=None)
    ics = tmp_path / "calendar.ics"
    _write_ics(ics, "1:1 with advisor", start_utc)

    out = CalendarSignal().collect(_ctx(now, enabled=True, ics_path=ics))
    assert out == "[calendar] next: '1:1 with advisor' in 25 min"


def test_calendar_ignores_event_outside_window(tmp_path):
    from claude_ambient import CalendarSignal

    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    start_utc = (now.astimezone(ZoneInfo("UTC")) + timedelta(minutes=200)).replace(tzinfo=None)
    ics = tmp_path / "calendar.ics"
    _write_ics(ics, "Far away meeting", start_utc)

    out = CalendarSignal().collect(_ctx(now, enabled=True, ics_path=ics, window=90))
    assert out is None
