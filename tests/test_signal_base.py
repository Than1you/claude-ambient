"""Tests for Signal ABC and SignalContext dataclass."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest


def test_signal_context_holds_now_state_config():
    from claude_ambient import SignalContext

    now = datetime(2026, 5, 18, 14, 24, 43, tzinfo=timezone.utc)
    ctx = SignalContext(now=now, state={"k": 1}, config={"c": 2})

    assert ctx.now == now
    assert ctx.state == {"k": 1}
    assert ctx.config == {"c": 2}


def test_signal_abc_requires_collect():
    from claude_ambient import Signal

    with pytest.raises(TypeError):
        Signal()  # type: ignore[abstract]


def test_signal_subclass_can_be_instantiated_when_collect_implemented():
    from claude_ambient import Signal, SignalContext

    class Dummy(Signal):
        name = "dummy"

        def collect(self, ctx: SignalContext):
            return "[dummy] ok"

    d = Dummy()
    ctx = SignalContext(
        now=datetime(2026, 5, 18, tzinfo=timezone.utc),
        state={},
        config={},
    )
    assert d.collect(ctx) == "[dummy] ok"
