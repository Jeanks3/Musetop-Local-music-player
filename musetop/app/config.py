"""Persistent application preferences stored as JSON.

Only visual preferences are persisted. Playback state and window geometry are
intentionally out of scope for the pre-alpha build.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from musetop.app import paths

logger = logging.getLogger(__name__)

THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"
VALID_THEMES: tuple[str, ...] = (THEME_SYSTEM, THEME_LIGHT, THEME_DARK)

DEFAULT_THEME = THEME_SYSTEM
DEFAULT_ACCENT = "#1f5fd0"

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated user preferences."""

    theme: str = DEFAULT_THEME
    accent_color: str = DEFAULT_ACCENT

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable mapping."""

        return {"theme": self.theme, "accent_color": self.accent_color}

    @classmethod
    def from_mapping(cls, data: Any) -> "AppConfig":
        """Build a config from untrusted JSON data, falling back per field."""

        if not isinstance(data, dict):
            return cls()

        theme = data.get("theme")
        accent = data.get("accent_color")
        normalized_theme = theme if isinstance(theme, str) and theme in VALID_THEMES else DEFAULT_THEME
        normalized_accent = accent if isinstance(accent, str) and _HEX_COLOR.match(accent) else DEFAULT_ACCENT
        return cls(theme=normalized_theme, accent_color=normalized_accent.lower())


def default_config() -> AppConfig:
    """Return the default preferences."""

    return AppConfig()


class ConfigManager:
    """Load and persist :class:`AppConfig` instances as JSON."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path is not None else paths.config_file()

    @property
    def path(self) -> Path:
        """Return the configuration file location."""

        return self._path

    def load(self) -> AppConfig:
        """Read preferences, returning defaults when the file is absent or bad."""

        try:
            raw = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return default_config()
        except OSError as exc:
            logger.warning("Could not read preferences from %s: %s", self._path, exc)
            return default_config()

        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Invalid preferences JSON in %s: %s", self._path, exc)
            return default_config()

        config = AppConfig.from_mapping(payload)
        if config.to_dict() != payload:
            logger.info("Preferences contained invalid fields and were normalized")
        return config

    def save(self, config: AppConfig) -> None:
        """Write preferences atomically as UTF-8 JSON."""

        payload = json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix="settings-",
            suffix=".json.tmp",
            dir=str(self._path.parent),
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self._path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise
        logger.debug("Preferences written to %s", self._path)

    def reset(self) -> AppConfig:
        """Restore and persist the default preferences."""

        config = default_config()
        self.save(config)
        return config

    def with_theme(self, config: AppConfig, theme: str) -> AppConfig:
        """Return ``config`` with a validated theme selection."""

        if theme not in VALID_THEMES:
            raise ValueError(f"Unknown theme: {theme}")
        return replace(config, theme=theme)

    def with_accent(self, config: AppConfig, accent_color: str) -> AppConfig:
        """Return ``config`` with a validated accent color."""

        if not _HEX_COLOR.match(accent_color):
            raise ValueError(f"Invalid accent color: {accent_color}")
        return replace(config, accent_color=accent_color.lower())
