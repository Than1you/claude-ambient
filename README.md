<h1 align="center">claude-ambient</h1>

<p align="center"><strong>Time-aware ambient context for Claude Code.</strong></p>

<p align="center">
  <em>Claude doesn't know what time it is. Or what day. Or how long since you last asked.<br/>Until now.</em>
</p>

<p align="center">
  <a href="https://github.com/Than1you/claude-ambient/actions/workflows/ci.yml">
    <img src="https://github.com/Than1you/claude-ambient/actions/workflows/ci.yml/badge.svg" alt="CI"/>
  </a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"/>
  <img src="https://img.shields.io/badge/install-2%20steps-brightgreen" alt="2-step install"/>
  <img src="https://img.shields.io/badge/runtime-stdlib--only-orange" alt="stdlib only"/>
  <img src="https://img.shields.io/badge/single--file-573%20LOC-lightgrey" alt="single file"/>
</p>

```text
┌─ what Claude actually receives, every prompt ────────────────────────────────┐
│  [time]   2026-05-19T08:42:00-05:00  (Tuesday, CDT, America/Chicago)         │
│  [rhythm] Δ since last prompt: 3 days 4 hours · first prompt after gap       │
│                                                · working hours               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤔 The problem

Claude Code's system prompt has a date. **One date.** Stamped at session start. After that, time stops:

- 3 minutes have passed? Claude doesn't know.
- 3 days have passed? Claude *also* doesn't know.
- Did DST flip last night? Friday at 11pm vs Saturday at 1am? Crickets.

So when you say "tonight" / "earlier today" / "this weekend", Claude is guessing. When you come back from a 3-day trip, Claude treats it like a quick follow-up. When it's 2am, Claude doesn't know to be more careful.

This is a 50-line problem with a 1-line installer.

## ⚡ Install (2 steps, ~60 seconds)

```bash
# 1. Drop the single file into your Claude config
curl -sSL https://raw.githubusercontent.com/Than1you/claude-ambient/main/claude_ambient.py \
  -o ~/.claude/claude_ambient.py
```

Then add this entry under `"hooks"` in `~/.claude/settings.json`:

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/claude_ambient.py"
      }]
    }]
  }
}
```

That's it. Claude Code hot-reloads the config — your next prompt is already time-aware. **No `pip`, no installer script, no build, no daemon.**

> **Windows:** swap `~/.claude/...` for `%USERPROFILE%\.claude\...` and `python3` → `python`. Also run `pip install tzdata` once — Windows Python's `zoneinfo` doesn't ship the IANA timezone database, but Linux and macOS do.

## 🎁 What gets injected

Two lines on every prompt, ~100 chars:

```
[time]   2026-05-19T01:46:58-05:00 (Tuesday, CDT, America/Chicago)
[rhythm] Δ since last prompt: 4 min · late night
```

After you've been away:

```
[time]   2026-05-21T09:00:00-05:00 (Thursday, CDT, America/Chicago)
[rhythm] Δ since last prompt: 2 days 7 hours · first prompt after gap · working hours
```

Multiple timezones (opt-in, for cross-timezone teams):

```
[time]   2026-05-19T14:24:43-05:00 (Tuesday, CDT, America/Chicago) (also: 19:24 UTC, 03:24+1 Asia/Shanghai)
```

## 🧱 Signals — five modules, configurable

| Signal | Default | What it does |
|---|:---:|---|
| 🕐 `time`      | **on**  | ISO 8601 + day-of-week + IANA timezone (with optional secondary zones) |
| 💓 `rhythm`    | **on**  | Δt since last prompt + derived energy label (`working hours`, `late night`, `weekend morning`, …) |
| 🔋 `system`    | off | Battery / disk alerts — silent unless a threshold is crossed |
| 📅 `calendar`  | off | Next event from a local `.ics` file, within a configurable window |
| ⏳ `deadlines` | off | Days-remaining from a tiny `YYYY-MM-DD \| label` text file |

Toggle each one in `~/.claude/claude-ambient/config.json` (auto-created on first run). Want a custom signal? It's one class with one `collect()` method — ~30 lines in a single file.

## 🎚️ Configuration (auto-generated on first run)

```json
{
  "timezone": null,
  "secondary_timezones": [],
  "signals": {
    "time":      { "enabled": true, "format": "iso_human" },
    "rhythm":    { "enabled": true },
    "system":    { "enabled": false, "battery_threshold_pct": 20, "disk_threshold_pct": 10 },
    "calendar":  { "enabled": false, "window_minutes": 90 },
    "deadlines": { "enabled": false }
  }
}
```

Timezone resolution: `config.timezone` → `$CLAUDE_TZ` → `$TZ` → system default → UTC. Set `"timezone": "America/Chicago"` to pin your local zone even when running on a UTC server.

## 🥊 vs. similar tools

| Feature                              | smarter-claude-clock | claude-code-toolkit | session-timer-hook | **claude-ambient** |
| ------------------------------------ | :------------------: | :-----------------: | :----------------: | :----------------: |
| Per-prompt fresh time                |          ✓           |    ✗ (start only)   |         ✓          |     **✓**          |
| **Δt since last prompt**             |          ✗           |          ✗          |  ✓ (post-turn)     |     **✓**          |
| Energy / period labels               |          ✗           |   ✓ (flag only)     |         ✗          |     **✓**          |
| Configurable timezone + overrides    |          ✗           |          ✗          |         ✗          |     **✓**          |
| Multi-timezone display               |          ✗           |          ✗          |         ✗          |     **✓**          |
| Single cross-platform file           |          ✗           |  ✗ (bash + ps1)     |         ✗          |     **✓**          |
| Structured `hookSpecificOutput` JSON |          ✗           |          ✗          |         ✗          |     **✓**          |
| Modular signal framework             |          ✗           |          ✗          |         ✗          |     **✓**          |

## 📊 By the numbers

- **573 lines** of Python — one file, the source *is* the deliverable
- **55 tests**, all passing on Linux × macOS × Windows × Python 3.9 / 3.11 / 3.13
- **~90 ms** cold-start latency (Python startup dominates)
- **<200 chars** typical context payload, hard-capped at 1 KB
- **Zero** external dependencies for the default signals

## 🛣️ Roadmap (v0.2+)

- [ ] Demo GIF (Claude knowing it's Tuesday)
- [ ] Configurable rhythm bands (night-owl mode)
- [ ] `pip install claude-ambient` for one-line install
- [ ] Google Calendar / Outlook OAuth for the calendar signal
- [ ] Rolling 7-day gap average — "you usually come back in 8h, this is unusual"
- [ ] Plugin-of-plugin extension API (drop a `.py` into `~/.claude/claude-ambient/signals/`)

Got an idea? Open an issue or PR.

## 🗑️ Uninstall

Delete the hook entry from `~/.claude/settings.json` and:

```bash
rm ~/.claude/claude_ambient.py
rm -rf ~/.claude/claude-ambient
```

## 📜 License

[MIT](LICENSE) — do whatever, just keep the notice.

---

<p align="center">
  <sub>If this saved you from explaining "no it's Wednesday" one more time,<br/>
  consider <a href="https://github.com/Than1you/claude-ambient">⭐ starring the repo</a>.</sub>
</p>
