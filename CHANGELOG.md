# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — Unreleased

### Added
- Initial release.
- `TimeSignal`: ISO 8601 + full day-of-week + IANA timezone (and optional secondary zones).
- `RhythmSignal`: Δt-since-last-prompt + derived energy/period label (working hours, late night, weekend variants, etc.).
- `SystemSignal` (default off): battery / disk threshold alerts.
- `CalendarSignal` (default off): next event from a local `.ics` file within a configurable window.
- `DeadlinesSignal` (default off): days-remaining from a local `date | label` file, with a -1-day grace.
- Per-signal error isolation with append-only `error.log` (1 MB cap).
- Cross-platform: Python 3.9+, stdlib only for default signals.
