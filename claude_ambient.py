#!/usr/bin/env python3
"""claude-ambient — single-file Claude Code UserPromptSubmit hook.

Injects fresh time + Δt-since-last-prompt + derived rhythm signals into
every user prompt via the Claude Code hooks JSON contract.

License: MIT
"""
from __future__ import annotations

__version__ = "0.1.0"


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Signal interface
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalContext:
    """Read-only view passed to every Signal.collect() call."""
    now: datetime          # tz-aware, in the resolved local timezone
    state: dict            # last-prompt persisted state (read-only view)
    config: dict           # full resolved config dict (read-only view)


class Signal(ABC):
    """Abstract base for any ambient signal emitter."""

    name: str = ""

    @abstractmethod
    def collect(self, ctx: SignalContext) -> Optional[str]:
        """Return a single-line fragment to inject, or None to skip."""


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
