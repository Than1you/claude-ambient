"""Tests for default config and user config merge."""
from __future__ import annotations

import json


def test_default_config_has_required_keys():
    from claude_ambient import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["schema_version"] == 1
    assert DEFAULT_CONFIG["timezone"] is None
    assert DEFAULT_CONFIG["signals"]["time"]["enabled"] is True
    assert DEFAULT_CONFIG["signals"]["rhythm"]["enabled"] is True
    assert DEFAULT_CONFIG["signals"]["system"]["enabled"] is False
    assert DEFAULT_CONFIG["signals"]["calendar"]["enabled"] is False
    assert DEFAULT_CONFIG["signals"]["deadlines"]["enabled"] is False


def test_load_config_creates_file_when_missing(tmp_path, monkeypatch):
    from claude_ambient import DEFAULT_CONFIG, load_config

    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.CONFIG_PATH", tmp_path / "config.json")

    cfg = load_config()

    assert (tmp_path / "config.json").exists()
    assert cfg == DEFAULT_CONFIG


def test_load_config_merges_user_overrides(tmp_path, monkeypatch):
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.CONFIG_PATH", tmp_path / "config.json")

    (tmp_path / "config.json").write_text(json.dumps({
        "timezone": "Asia/Shanghai",
        "signals": {"system": {"enabled": True}},
    }))

    from claude_ambient import load_config
    cfg = load_config()

    assert cfg["timezone"] == "Asia/Shanghai"
    assert cfg["signals"]["system"]["enabled"] is True
    # default values still present
    assert cfg["signals"]["time"]["enabled"] is True
    assert cfg["signals"]["system"]["battery_threshold_pct"] == 20


def test_load_config_recovers_from_corrupt_file(tmp_path, monkeypatch):
    monkeypatch.setattr("claude_ambient.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("claude_ambient.CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text("{not valid json")

    from claude_ambient import DEFAULT_CONFIG, load_config
    cfg = load_config()

    assert cfg == DEFAULT_CONFIG
