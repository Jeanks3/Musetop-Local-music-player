from __future__ import annotations

import json
from pathlib import Path

import pytest

from musetop.app.config import (
    DEFAULT_ACCENT,
    DEFAULT_THEME,
    AppConfig,
    ConfigManager,
    default_config,
)


def test_defaults() -> None:
    config = default_config()
    assert config.theme == DEFAULT_THEME == "system"
    assert config.accent_color == DEFAULT_ACCENT


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "settings.json")
    expected = AppConfig(theme="dark", accent_color="#aa3300")
    manager.save(expected)
    assert manager.load() == expected
    payload = json.loads(manager.path.read_text(encoding="utf-8"))
    assert payload == {"theme": "dark", "accent_color": "#aa3300"}


def test_missing_file_returns_defaults(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "missing.json")
    assert manager.load() == default_config()


def test_invalid_json_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    assert ConfigManager(path).load() == default_config()


def test_invalid_fields_are_normalized(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "neon", "accent_color": "red"}), encoding="utf-8")
    assert ConfigManager(path).load() == default_config()


def test_non_mapping_payload_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(["dark"]), encoding="utf-8")
    assert ConfigManager(path).load() == default_config()


def test_reset_persists_defaults(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "settings.json")
    manager.save(AppConfig(theme="light", accent_color="#123456"))
    assert manager.reset() == default_config()
    assert manager.load() == default_config()


def test_with_theme_and_accent_validate_input() -> None:
    manager = ConfigManager(Path("/tmp/unused-settings.json"))
    config = manager.with_theme(default_config(), "light")
    assert config.theme == "light"
    assert manager.with_accent(config, "#AABBCC").accent_color == "#aabbcc"
    with pytest.raises(ValueError):
        manager.with_theme(config, "neon")
    with pytest.raises(ValueError):
        manager.with_accent(config, "blue")


def test_save_creates_parent_directory(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "nested" / "settings.json")
    manager.save(AppConfig())
    assert manager.path.is_file()
