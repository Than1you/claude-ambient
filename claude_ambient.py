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


import copy
import json
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict = {
    "schema_version": 1,
    "timezone": None,
    "secondary_timezones": [],
    "signals": {
        "time":      {"enabled": True,  "format": "iso_human"},
        "rhythm":    {"enabled": True},
        "system":    {"enabled": False, "battery_threshold_pct": 20, "disk_threshold_pct": 10},
        "calendar":  {"enabled": False, "window_minutes": 90},
        "deadlines": {"enabled": False},
    },
    "output": {
        "header": False,
        "compact": False,
    },
}

CONFIG_DIR: Path = Path.home() / ".claude" / "claude-ambient"
CONFIG_PATH: Path = CONFIG_DIR / "config.json"


def _deep_merge(default: dict, user: dict) -> dict:
    """Return a new dict with user values overlaid onto default, recursively."""
    out: dict = {}
    for key, dval in default.items():
        if key not in user:
            out[key] = copy.deepcopy(dval)
        elif isinstance(dval, dict) and isinstance(user[key], dict):
            out[key] = _deep_merge(dval, user[key])
        else:
            out[key] = user[key]
    # surface unknown user keys at the end (they are ignored downstream but
    # preserved so we don't silently drop user data on rewrite)
    for key, uval in user.items():
        if key not in default:
            out[key] = uval
    return out


def load_config() -> dict:
    """Return the merged config dict, creating the default file if absent."""
    if not CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
        return copy.deepcopy(DEFAULT_CONFIG)
    try:
        user = json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(DEFAULT_CONFIG)
    if not isinstance(user, dict):
        return copy.deepcopy(DEFAULT_CONFIG)
    return _deep_merge(DEFAULT_CONFIG, user)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

STATE_PATH: Path = CONFIG_DIR / "state.json"


def load_state() -> dict:
    """Return persisted state, or a fresh empty state on missing/corrupt file."""
    fresh = {"schema_version": 1}
    if not STATE_PATH.exists():
        return fresh
    try:
        data = json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return fresh
    if not isinstance(data, dict):
        return fresh
    return data


def save_state(state: dict) -> None:
    """Persist state atomically: write to .tmp, then os.replace into place."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(state))
    os.replace(tmp, STATE_PATH)


from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# ---------------------------------------------------------------------------
# Timezone resolution
# ---------------------------------------------------------------------------

def _system_timezone() -> Optional[str]:
    """Best-effort detection of the host's IANA timezone name."""
    # /etc/timezone (Debian-family)
    try:
        text = Path("/etc/timezone").read_text().strip()
        if text:
            return text
    except OSError:
        pass
    # /etc/localtime symlink (most modern Linux / macOS)
    try:
        link = os.readlink("/etc/localtime")
        marker = "/zoneinfo/"
        if marker in link:
            return link.split(marker, 1)[1]
    except OSError:
        pass
    # Python 3.9+: ZoneInfo("localtime") tries platform-native lookup
    try:
        ZoneInfo("localtime")
        return "localtime"
    except ZoneInfoNotFoundError:
        return None


def resolve_timezone(config: dict) -> ZoneInfo:
    """Apply the override chain and return a ZoneInfo, falling back to UTC."""
    candidates = [
        config.get("timezone"),
        os.environ.get("CLAUDE_TZ"),
        os.environ.get("TZ"),
        _system_timezone(),
    ]
    for name in candidates:
        if not name:
            continue
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            continue
    return ZoneInfo("UTC")


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

class TimeSignal(Signal):
    """Emit the current local time (ISO 8601 + day-of-week + IANA name)."""

    name = "time"

    def collect(self, ctx: SignalContext) -> Optional[str]:
        cfg = ctx.config["signals"]["time"]
        if not cfg.get("enabled", True):
            return None

        iso = ctx.now.isoformat(timespec="seconds")
        if cfg.get("format") == "iso":
            return f"[time] {iso}"

        day = ctx.now.strftime("%A")
        tz_abbrev = ctx.now.strftime("%Z") or "?"
        tz_name = getattr(ctx.now.tzinfo, "key", str(ctx.now.tzinfo))

        head = f"[time] {iso} ({day}, {tz_abbrev}, {tz_name})"

        secondary = ctx.config.get("secondary_timezones", [])
        if secondary:
            extras = self._render_secondary(ctx.now, secondary)
            if extras:
                head += f" (also: {extras})"
        return head

    @staticmethod
    def _render_secondary(now: datetime, zones: list) -> str:
        primary_date = now.date()
        parts = []
        for zname in zones:
            try:
                z = ZoneInfo(zname)
            except ZoneInfoNotFoundError:
                continue
            in_zone = now.astimezone(z)
            delta_days = (in_zone.date() - primary_date).days
            if delta_days > 0:
                suffix = f"+{delta_days}"
            elif delta_days < 0:
                suffix = str(delta_days)
            else:
                suffix = ""
            parts.append(f"{in_zone.strftime('%H:%M')}{suffix} {zname}")
        return ", ".join(parts)


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
