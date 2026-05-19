"""Tests for state load/save helpers."""
from __future__ import annotations

import json


def test_load_state_returns_empty_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.STATE_PATH", tmp_path / "state.json")

    from claude_ambient import load_state
    state = load_state()

    assert state == {"schema_version": 1}


def test_load_state_recovers_from_corrupt(tmp_path, monkeypatch):
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.STATE_PATH", tmp_path / "state.json")
    (tmp_path / "state.json").write_text("garbage{")

    from claude_ambient import load_state
    state = load_state()

    assert state == {"schema_version": 1}


def test_save_state_writes_atomically(tmp_path, monkeypatch):
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.STATE_PATH", tmp_path / "state.json")

    from claude_ambient import save_state

    save_state({"schema_version": 1, "last_prompt_at": "2026-05-18T14:24:43-05:00"})

    body = json.loads((tmp_path / "state.json").read_text())
    assert body["last_prompt_at"] == "2026-05-18T14:24:43-05:00"
    # tmp file should not be left behind
    assert not (tmp_path / "state.json.tmp").exists()
