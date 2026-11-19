from __future__ import annotations

from pathlib import Path

from musetop.app import paths


def test_linux_defaults_to_xdg_config_home() -> None:
    home = Path("/home/demo")
    assert paths.app_data_dir("linux", {"XDG_CONFIG_HOME": "/tmp/config"}, home) == Path("/tmp/config/musetop")


def test_linux_falls_back_to_dot_config() -> None:
    home = Path("/home/demo")
    assert paths.app_data_dir("linux", {}, home) == home / ".config" / "musetop"


def test_windows_uses_appdata(monkeypatch) -> None:
    home = Path("C:/Users/demo")
    env = {"APPDATA": "C:/Users/demo/AppData/Roaming"}
    assert paths.app_data_dir("win32", env, home) == Path("C:/Users/demo/AppData/Roaming/Musetop")


def test_windows_without_appdata_uses_roaming_default() -> None:
    home = Path("C:/Users/demo")
    assert paths.app_data_dir("win32", {}, home) == home / "AppData" / "Roaming" / "Musetop"


def test_config_and_log_paths(tmp_path: Path) -> None:
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    config = paths.config_file("linux", env, tmp_path)
    logs = paths.log_dir("linux", env, tmp_path)
    assert config == tmp_path / "musetop" / "settings.json"
    assert logs == tmp_path / "musetop" / "logs"


def test_ensure_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "folder"
    assert paths.ensure_directory(target) == target
    assert target.is_dir()


def test_project_has_resource_directories() -> None:
    assert paths.package_dir().name == "musetop"
    assert paths.resources_dir().name == "resources"
    assert paths.vendor_lib_dir().name == "lib"
