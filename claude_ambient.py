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


class RhythmSignal(Signal):
    """Emit Δt-since-last-prompt + a derived energy/period label."""

    name = "rhythm"

    def collect(self, ctx: SignalContext) -> Optional[str]:
        cfg = ctx.config["signals"]["rhythm"]
        if not cfg.get("enabled", True):
            return None

        delta_str, is_long_gap = self._render_delta(ctx)
        label = self._energy_label(ctx.now)

        parts = [f"Δ since last prompt: {delta_str}"]
        if is_long_gap:
            parts.append("first prompt after gap")
        parts.append(label)
        return "[rhythm] " + " · ".join(parts)

    @staticmethod
    def _render_delta(ctx: SignalContext) -> tuple:
        last = ctx.state.get("last_prompt_at")
        if not last:
            return "first prompt (no prior state)", False
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            return "first prompt (no prior state)", False
        if last_dt.tzinfo is None and ctx.now.tzinfo is not None:
            last_dt = last_dt.replace(tzinfo=ctx.now.tzinfo)
        delta = ctx.now - last_dt
        secs = int(delta.total_seconds())
        if secs < 0:
            # Clock went backwards (DST fall-back or system clock fix); treat as just now.
            return "just now", False
        if secs < 60:
            return "just now", False
        if secs < 3600:
            return f"{secs // 60} min", False
        if secs < 86400:
            h, rem = divmod(secs, 3600)
            m = rem // 60
            return f"{h} hours {m} min", False
        days, rem = divmod(secs, 86400)
        hrs = rem // 3600
        return f"{days} days {hrs} hours", True

    @staticmethod
    def _energy_label(now: datetime) -> str:
        h = now.hour
        is_weekend = now.weekday() >= 5  # 5=Sat, 6=Sun
        if is_weekend:
            if 5 <= h < 12:
                return "weekend morning"
            if 12 <= h < 18:
                return "weekend afternoon"
            if 18 <= h < 22:
                return "weekend evening"
            return "weekend late night"
        if h >= 22 or h < 5:
            return "late night"
        if h < 8:
            return "early morning"
        if h < 18:
            return "working hours"
        return "evening"


import shutil
import subprocess


class SystemSignal(Signal):
    """Emit a fragment only when battery or free-disk crosses a threshold."""

    name = "system"

    def collect(self, ctx: SignalContext) -> Optional[str]:
        cfg = ctx.config["signals"]["system"]
        if not cfg.get("enabled", False):
            return None

        battery_thresh = int(cfg.get("battery_threshold_pct", 20))
        disk_thresh = int(cfg.get("disk_threshold_pct", 10))

        battery = self._read_battery_pct()
        disk = self._read_disk_free_pct()

        notes = []
        if battery is not None and battery <= battery_thresh:
            notes.append(f"battery {battery}% (low)")
        if disk is not None and disk <= disk_thresh:
            notes.append(f"disk {disk}% free (low)")

        if not notes:
            return None
        return "[system] " + " · ".join(notes)

    # --- Battery ----------------------------------------------------------

    def _read_battery_pct(self) -> Optional[int]:
        # 1) psutil (best-effort, optional dep)
        try:
            import psutil  # type: ignore
            bat = psutil.sensors_battery()
            if bat is not None:
                return int(bat.percent)
        except Exception:
            pass
        # 2) Linux /sys
        try:
            for base in Path("/sys/class/power_supply").iterdir():
                cap = base / "capacity"
                if cap.exists():
                    return int(cap.read_text().strip())
        except Exception:
            pass
        # 3) macOS pmset
        try:
            out = subprocess.run(
                ["pmset", "-g", "batt"],
                capture_output=True, text=True, timeout=1,
            )
            for token in out.stdout.split():
                if token.endswith("%;"):
                    return int(token.rstrip("%;"))
        except Exception:
            pass
        return None

    # --- Disk -------------------------------------------------------------

    def _read_disk_free_pct(self) -> Optional[int]:
        target = "C:\\" if os.name == "nt" else "/"
        try:
            usage = shutil.disk_usage(target)
            return int(usage.free * 100 / usage.total)
        except Exception:
            return None


import sys


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _now(tz: ZoneInfo) -> datetime:
    """Indirection so tests can monkeypatch the clock."""
    return datetime.now(tz=tz)


SIGNAL_REGISTRY = [TimeSignal, RhythmSignal, SystemSignal]


def _build_context() -> SignalContext:
    config = load_config()
    state = load_state()
    tz = resolve_timezone(config)
    now = _now(tz)
    return SignalContext(now=now, state=state, config=config)


def _join_fragments(fragments: list, config: dict) -> str:
    sep = " · " if config.get("output", {}).get("compact", False) else "\n"
    text = sep.join(fragments)
    if len(text) > 1024:
        text = text[:1020] + "..."
    return text


def main() -> int:
    try:
        ctx = _build_context()
    except Exception:
        # Even context build failure must not break the user's prompt.
        sys.stdout.write(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        }))
        return 0

    fragments: list = []
    for cls in SIGNAL_REGISTRY:
        try:
            line = cls().collect(ctx)
        except Exception:
            line = None
        if line:
            fragments.append(line)

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": _join_fragments(fragments, ctx.config),
        }
    }
    sys.stdout.write(json.dumps(payload))

    try:
        new_state = dict(ctx.state)
        new_state["last_prompt_at"] = ctx.now.isoformat(timespec="seconds")
        save_state(new_state)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
