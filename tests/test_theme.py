from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from musetop.app.config import ConfigManager, default_config
from musetop.ui.main_window import MainWindow
from musetop.ui.theme.colors import (
    best_text_color,
    blend,
    build_palette,
    contrast_ratio,
    ensure_visible_accent,
    relative_luminance,
)
from musetop.ui.theme.manager import ThemeManager, detect_system_theme, resolve_theme
from tests.fake_engine import FakeEngine

ACCENTS = ("#1f5fd0", "#ffffff", "#000000", "#ffff00", "#808080", "#ff0000", "#00ff00", "#123456", "#abcdef")


def test_color_math() -> None:
    assert relative_luminance("#000000") == pytest.approx(0.0)
    assert relative_luminance("#ffffff") == pytest.approx(1.0)
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, rel=0.01)
    assert contrast_ratio("#123456", "#123456") == pytest.approx(1.0)
    assert best_text_color("#ffffff") == "#000000"
    assert best_text_color("#000000") == "#ffffff"
    assert blend("#000000", "#ffffff", 0.5) == "#808080"
    assert blend("#000000", "#ffffff", -1) == "#000000"
    assert blend("#000000", "#ffffff", 2) == "#ffffff"


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize("accent", ACCENTS)
def test_palette_meets_wcag_aa(mode: str, accent: str) -> None:
    palette = build_palette(mode, accent)
    for background in (palette.background, palette.surface):
        assert contrast_ratio(palette.text, background) >= 4.5
        assert contrast_ratio(palette.text_muted, background) >= 4.5
        assert contrast_ratio(palette.accent, background) >= 3.0
    assert contrast_ratio(palette.on_accent, palette.accent) >= 4.5
    assert contrast_ratio(palette.on_accent, palette.accent_hover) >= 4.5
    assert contrast_ratio(palette.on_accent, palette.accent_pressed) >= 4.5


def test_invisible_accent_is_adjusted_for_contrast() -> None:
    light = build_palette("light", "#ffffff")
    dark = build_palette("dark", "#000000")
    assert light.accent != "#ffffff"
    assert dark.accent != "#000000"
    assert contrast_ratio(light.accent, light.surface) >= 3.0
    assert contrast_ratio(dark.accent, dark.surface) >= 3.0
    assert contrast_ratio(
        ensure_visible_accent("#ffffff", "#ffffff", "#ffffff"), "#ffffff"
    ) >= 3.0


def test_resolve_theme() -> None:
    assert resolve_theme("system", "dark") == "dark"
    assert resolve_theme("system", "light") == "light"
    assert resolve_theme("dark", "light") == "dark"
    assert resolve_theme("light", "dark") == "light"


class FakeHints:
    def __init__(self, scheme: Qt.ColorScheme) -> None:
        self._scheme = scheme

    def colorScheme(self) -> Qt.ColorScheme:  # noqa: N802
        return self._scheme


class FakeApplication:
    def __init__(self, scheme: Qt.ColorScheme, window_color: str = "#ffffff") -> None:
        self._hints = FakeHints(scheme)
        self._palette = QPalette()
        self._palette.setColor(QPalette.ColorRole.Window, QColor(window_color))

    def styleHints(self):  # noqa: N802
        return self._hints

    def palette(self) -> QPalette:
        return self._palette


def test_detect_system_theme_from_qt_scheme() -> None:
    assert detect_system_theme(FakeApplication(Qt.ColorScheme.Dark)) == "dark"
    assert detect_system_theme(FakeApplication(Qt.ColorScheme.Light)) == "light"


def test_detect_system_theme_falls_back_to_window_color() -> None:
    assert detect_system_theme(FakeApplication(Qt.ColorScheme.Unknown, "#101010")) == "dark"
    assert detect_system_theme(FakeApplication(Qt.ColorScheme.Unknown, "#fafafa")) == "light"


def test_manager_persists_theme_and_accent(qtbot, tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    manager = ThemeManager(ConfigManager(path), scheme_provider=lambda: "light")
    assert manager.apply_current().mode == "light"
    assert manager.config.theme == "system"

    with qtbot.waitSignal(manager.palette_changed, timeout=1000):
        manager.set_theme("dark")
    assert manager.palette.mode == "dark"
    assert ConfigManager(path).load().theme == "dark"

    manager.set_accent("#ffcc00")
    assert manager.palette.accent == "#ffcc00"
    assert ConfigManager(path).load().accent_color == "#ffcc00"

    manager.reset()
    assert manager.config == default_config()
    assert ConfigManager(path).load() == default_config()


def test_manager_follows_system_when_selected(qtbot, tmp_path: Path) -> None:
    state = {"theme": "dark"}
    manager = ThemeManager(
        ConfigManager(tmp_path / "settings.json"),
        scheme_provider=lambda: state["theme"],
    )
    manager.apply_current()
    assert manager.palette.mode == "dark"
    state["theme"] = "light"
    manager.refresh_from_system()
    assert manager.palette.mode == "light"
    assert manager.config.theme == "system"


def test_stylesheet_uses_accent_and_selection(qtbot, tmp_path: Path) -> None:
    app = QApplication.instance()
    assert app is not None
    manager = ThemeManager(ConfigManager(tmp_path / "settings.json"), scheme_provider=lambda: "light")
    palette = manager.set_theme("light")
    stylesheet = app.styleSheet()
    assert palette.accent in stylesheet
    assert palette.on_accent in stylesheet
    assert "selection-background-color" in stylesheet
    assert "QPushButton#primaryButton" in stylesheet
    assert app.palette().color(QPalette.ColorRole.Highlight).name() == palette.accent


def test_theme_switch_is_fast_and_does_not_touch_playback(qtbot, tmp_path: Path) -> None:
    engine = FakeEngine()
    window = MainWindow(ConfigManager(tmp_path / "settings.json"), engine)
    qtbot.addWidget(window)
    window.load_paths([])
    for widget in QApplication.topLevelWidgets():
        if widget is not window:
            widget.close()
            widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QApplication.processEvents()
    window.theme_manager.set_theme("light")
    QApplication.processEvents()
    engine.calls.clear()
    started = time.perf_counter()
    window.theme_manager.set_theme("dark")
    QApplication.processEvents()
    elapsed = time.perf_counter() - started
    assert elapsed < 0.5
    assert window.theme_manager.palette.mode == "dark"
    assert "stop" not in engine.calls
    assert "toggle_pause" not in engine.calls
    assert "set_playlist" not in engine.calls
    assert window.theme_manager.config.theme == "dark"


def test_main_window_theme_controls_persist(qtbot, tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "settings.json"
    window = MainWindow(ConfigManager(path), FakeEngine())
    qtbot.addWidget(window)
    index = window.theme_combo.findData("dark")
    window.theme_combo.setCurrentIndex(index)
    assert ConfigManager(path).load().theme == "dark"
    assert window.theme_manager.palette.mode == "dark"

    monkeypatch.setattr(
        "musetop.ui.main_window.QColorDialog.getColor",
        lambda *args, **kwargs: QColor("#ffcc00"),
    )
    window.accent_button.click()
    assert ConfigManager(path).load().accent_color == "#ffcc00"
    assert window.theme_manager.palette.accent == "#ffcc00"

    window._reset_appearance()
    loaded = ConfigManager(path).load()
    assert loaded == default_config()
    assert window.theme_combo.currentData() == "system"
    assert "Apariencia restablecida" in window.statusBar().currentMessage()
