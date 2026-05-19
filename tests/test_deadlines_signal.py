"""Tests for DeadlinesSignal: future, past-1-day grace, past-2-day drop."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


CHI = ZoneInfo("America/Chicago")


def _ctx(now, enabled, deadlines_path=None):
    from claude_ambient import DEFAULT_CONFIG, SignalContext
    import copy
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["signals"]["deadlines"]["enabled"] = enabled
    if deadlines_path is not None:
        cfg["signals"]["deadlines"]["_test_file"] = str(deadlines_path)
    return SignalContext(now=now, state={}, config=cfg)


def test_disabled(tmp_path):
    from claude_ambient import DeadlinesSignal
    out = DeadlinesSignal().collect(_ctx(datetime(2026, 5, 18, tzinfo=CHI), enabled=False))
    assert out is None


def test_missing_file(tmp_path):
    from claude_ambient import DeadlinesSignal
    out = DeadlinesSignal().collect(_ctx(
        datetime(2026, 5, 18, tzinfo=CHI), enabled=True,
        deadlines_path=tmp_path / "nope.txt",
    ))
    assert out is None


def test_future_deadlines_sorted(tmp_path):
    from claude_ambient import DeadlinesSignal
    p = tmp_path / "deadlines.txt"
    p.write_text(
        "# format: date | label\n"
        "2026-06-15 | OPDD paper draft\n"
        "2026-05-21 | MATH baseline run\n"
    )
    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    out = DeadlinesSignal().collect(_ctx(now, enabled=True, deadlines_path=p))
    assert out == "[deadlines] MATH baseline run: 3 days · OPDD paper draft: 28 days"


def test_past_within_grace_kept(tmp_path):
    from claude_ambient import DeadlinesSignal
    p = tmp_path / "deadlines.txt"
    p.write_text("2026-05-17 | yesterday\n")
    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    out = DeadlinesSignal().collect(_ctx(now, enabled=True, deadlines_path=p))
    assert out == "[deadlines] yesterday: -1 day"


def test_past_beyond_grace_dropped(tmp_path):
    from claude_ambient import DeadlinesSignal
    p = tmp_path / "deadlines.txt"
    p.write_text("2026-05-16 | two days ago\n")
    now = datetime(2026, 5, 18, 14, 0, 0, tzinfo=CHI)
    out = DeadlinesSignal().collect(_ctx(now, enabled=True, deadlines_path=p))
    assert out is None
