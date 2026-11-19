"""Platform-aware filesystem locations used by Musetop.

The project targets Windows 10+ and Linux. macOS is handled as a best-effort
extension so development on that platform does not require special cases.
All paths are derived with :mod:`pathlib` and never perform network access.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

APP_DIR_NAME = "musetop"
WINDOWS_APP_DIR_NAME = "Musetop"


def app_data_dir(
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the per-user configuration directory for the application.

    Windows uses ``%APPDATA%/Musetop``. Linux follows the XDG specification and
    defaults to ``~/.config/musetop``. The optional arguments make the platform
    rules testable without touching the real environment.
    """

    system = (platform or sys.platform).lower()
    environment = os.environ if env is None else env
    home_dir = Path.home() if home is None else Path(home)

    if system.startswith("win"):
        roaming = environment.get("APPDATA")
        base = Path(roaming) if roaming else home_dir / "AppData" / "Roaming"
        return base / WINDOWS_APP_DIR_NAME

    if system == "darwin":
        return home_dir / "Library" / "Application Support" / "Musetop"

    base = environment.get("XDG_CONFIG_HOME")
    config_home = Path(base) if base else home_dir / ".config"
    return config_home / APP_DIR_NAME


def config_file(
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the JSON settings file path."""

    return app_data_dir(platform=platform, env=env, home=home) / "settings.json"


def log_dir(
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the directory that stores rotating log files."""

    return app_data_dir(platform=platform, env=env, home=home) / "logs"


def package_dir() -> Path:
    """Return the directory that contains the ``musetop`` package."""

    return Path(__file__).resolve().parents[1]


def project_dir() -> Path:
    """Return the repository root for source checkouts."""

    return package_dir().parent


def resources_dir() -> Path:
    """Return the directory containing packaged resource files."""

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "resources"
    return package_dir() / "resources"


def vendor_lib_dir() -> Path:
    """Return the directory used for bundled native libraries."""

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "vendor" / "lib"
    return project_dir() / "vendor" / "lib"


def ensure_directory(path: Path) -> Path:
    """Create ``path`` when missing and return it."""

    path.mkdir(parents=True, exist_ok=True)
    return path
