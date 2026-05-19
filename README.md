# claude-ambient

> A single-file Claude Code hook that injects fresh time, day-of-week, and Δt-since-last-prompt into every user prompt — so Claude knows when you're back from lunch, when it's the weekend, and when DST flipped.

## Why

Claude Code's session start date is injected once and goes stale. There's no time-of-day, day-of-week, or "how long since your last message" signal. `claude-ambient` adds them via the `UserPromptSubmit` hook.

## Install (2 steps)

```bash
# 1. Download the single file
curl -sSL https://raw.githubusercontent.com/<your-user>/claude-ambient/main/claude_ambient.py \
  -o ~/.claude/claude_ambient.py

# 2. Add this hook entry to ~/.claude/settings.json (under "hooks")
```

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

That's it. No `pip`, no installer script, no build step.

**Windows:** substitute `%USERPROFILE%\.claude\claude_ambient.py` and use `python` instead of `python3`.

## What gets injected

```
[time] 2026-05-18T14:24:43-05:00 (Monday, CDT, America/Chicago)
[rhythm] Δ since last prompt: 12 min · working hours
```

After a long absence:

```
[time] 2026-05-21T09:00:00-05:00 (Thursday, CDT, America/Chicago)
[rhythm] Δ since last prompt: 3 days 4 hours · first prompt after gap · working hours
```

## Signals (5 modules, configurable)

| Signal      | Default | What it does                                               |
| ----------- | ------- | ---------------------------------------------------------- |
| `time`      | **ON**  | ISO 8601 + day-of-week + IANA timezone                     |
| `rhythm`    | **ON**  | Δt since last prompt + energy/period label                 |
| `system`    | off     | battery / disk alerts (only when threshold crossed)        |
| `calendar`  | off     | next event from a local `.ics` file (within window)        |
| `deadlines` | off     | days-remaining from a local `date \| label` text file      |

## Configuration

`~/.claude/claude-ambient/config.json` is created on first run with sensible defaults. Selected keys:

```json
{
  "timezone": null,
  "secondary_timezones": ["UTC", "Asia/Shanghai"],
  "signals": {
    "time":      { "enabled": true, "format": "iso_human" },
    "rhythm":    { "enabled": true },
    "system":    { "enabled": false, "battery_threshold_pct": 20, "disk_threshold_pct": 10 },
    "calendar":  { "enabled": false, "window_minutes": 90 },
    "deadlines": { "enabled": false }
  },
  "output": { "compact": false }
}
```

Timezone resolution order: `config.timezone` → `$CLAUDE_TZ` → `$TZ` → system default → UTC.

## Compared with similar tools

| Feature                              | smarter-claude-clock | claude-code-toolkit | session-timer-hook | **claude-ambient** |
| ------------------------------------ | :------------------: | :-----------------: | :----------------: | :----------------: |
| Per-prompt fresh time                |          ✓           |    ✗ (start only)   |         ✓          |         ✓          |
| Δt since last prompt                 |          ✗           |          ✗          |  ✓ (post-turn)     |         ✓          |
| Energy / period labels               |          ✗           |   ✓ (flag only)     |         ✗          |         ✓          |
| Configurable timezone + overrides    |          ✗           |          ✗          |         ✗          |         ✓          |
| Multi-timezone display               |          ✗           |          ✗          |         ✗          |         ✓          |
| Single cross-platform file           |          ✗           |  ✗ (bash + ps1)     |         ✗          |         ✓          |
| Structured `hookSpecificOutput` JSON |          ✗           |          ✗          |         ✗          |         ✓          |
| Modular signal framework             |          ✗           |          ✗          |         ✗          |         ✓          |

## Requirements

- Python ≥ 3.9 (for `zoneinfo`)
- That's it — no external dependencies for the default signals
- Optional: `psutil` improves battery detection on `system` signal

## Uninstall

Delete the hook entry from `~/.claude/settings.json` and remove `~/.claude/claude_ambient.py` plus `~/.claude/claude-ambient/`.

## License

MIT — see `LICENSE`.
