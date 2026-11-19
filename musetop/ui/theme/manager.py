"""Theme selection, system following, Qt application and JSON persistence."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from musetop.app.config import (
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
    AppConfig,
    ConfigManager,
)
from musetop.ui.theme.colors import (
    ThemePalette,
    build_palette,
    relative_luminance,
)
from musetop.ui.theme.styles import build_stylesheet

logger = logging.getLogger(__name__)


def detect_system_theme(app: QApplication | None = None) -> str:
    """Return ``light`` or ``dark`` from the platform color scheme."""

    application = app if app is not None else QApplication.instance()
    if application is None:
        return THEME_LIGHT
    scheme = application.styleHints().colorScheme()
    if scheme == Qt.ColorScheme.Dark:
        return THEME_DARK
    if scheme == Qt.ColorScheme.Light:
        return THEME_LIGHT
    window_color = application.palette().color(QPalette.ColorRole.Window).name()
    return THEME_DARK if relative_luminance(window_color) < 0.5 else THEME_LIGHT


def resolve_theme(theme: str, system_theme: str) -> str:
    """Resolve ``system`` to a concrete light or dark mode."""

    if theme == THEME_SYSTEM:
        return THEME_DARK if system_theme == THEME_DARK else THEME_LIGHT
    return THEME_DARK if theme == THEME_DARK else THEME_LIGHT


def _apply_palette(application: QApplication, palette: ThemePalette) -> None:
    qt_palette = QPalette()
    color = QColor
    qt_palette.setColor(QPalette.ColorRole.Window, color(palette.background))
    qt_palette.setColor(QPalette.ColorRole.WindowText, color(palette.text))
    qt_palette.setColor(QPalette.ColorRole.Base, color(palette.surface))
    qt_palette.setColor(QPalette.ColorRole.AlternateBase, color(palette.surface_alt))
    qt_palette.setColor(QPalette.ColorRole.Text, color(palette.text))
    qt_palette.setColor(QPalette.ColorRole.Button, color(palette.surface))
    qt_palette.setColor(QPalette.ColorRole.ButtonText, color(palette.text))
    qt_palette.setColor(QPalette.ColorRole.BrightText, color(palette.on_accent))
    qt_palette.setColor(QPalette.ColorRole.Highlight, color(palette.accent))
    qt_palette.setColor(QPalette.ColorRole.HighlightedText, color(palette.on_accent))
    qt_palette.setColor(QPalette.ColorRole.ToolTipBase, color(palette.surface))
    qt_palette.setColor(QPalette.ColorRole.ToolTipText, color(palette.text))
    qt_palette.setColor(QPalette.ColorRole.PlaceholderText, color(palette.text_muted))
    qt_palette.setColor(QPalette.ColorRole.Link, color(palette.accent))
    qt_palette.setColor(QPalette.ColorRole.Mid, color(palette.border))
    qt_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, color(palette.disabled_text))
    qt_palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        color(palette.disabled_text),
    )
    qt_palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        color(palette.disabled_text),
    )
    application.setPalette(qt_palette)


class ThemeManager(QObject):
    """Own the active palette and persist visual preferences."""

    palette_changed = Signal(object)

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        app: QApplication | None = None,
        scheme_provider: Callable[[], str] | None = None,
    ) -> None:
        super().__init__()
        self._config_manager = config_manager or ConfigManager()
        self._config = self._config_manager.load()
        self._app = app if app is not None else QApplication.instance()
        self._scheme_provider = scheme_provider
        self._palette = build_palette(THEME_LIGHT, self._config.accent_color)
        if self._app is not None and scheme_provider is None:
            self._app.styleHints().colorSchemeChanged.connect(self._on_system_scheme_changed)

    @property
    def config(self) -> AppConfig:
        """Current preferences."""

        return self._config

    @property
    def palette(self) -> ThemePalette:
        """Current resolved palette."""

        return self._palette

    def apply_current(self) -> ThemePalette:
        """Apply the stored preferences to the Qt application."""

        return self._apply()

    def set_theme(self, theme: str) -> ThemePalette:
        """Select a theme, apply it and persist the preference."""

        self._config = self._config_manager.with_theme(self._config, theme)
        palette = self._apply()
        self._persist()
        return palette

    def set_accent(self, accent_color: str) -> ThemePalette:
        """Select an accent color, apply it and persist the preference."""

        self._config = self._config_manager.with_accent(self._config, accent_color)
        palette = self._apply()
        self._persist()
        return palette

    def reset(self) -> ThemePalette:
        """Restore the default theme and accent color."""

        self._config = self._config_manager.reset()
        palette = self._apply()
        return palette

    def refresh_from_system(self) -> ThemePalette:
        """Re-resolve the system theme without writing preferences."""

        if self._config.theme == THEME_SYSTEM:
            return self._apply()
        return self._palette

    def _system_theme(self) -> str:
        if self._scheme_provider is not None:
            return self._scheme_provider()
        return detect_system_theme(self._app)

    def _apply(self) -> ThemePalette:
        resolved = resolve_theme(self._config.theme, self._system_theme())
        self._palette = build_palette(resolved, self._config.accent_color)
        if self._app is not None:
            _apply_palette(self._app, self._palette)
            self._app.setStyleSheet(build_stylesheet(self._palette))
        self.palette_changed.emit(self._palette)
        logger.debug("Applied %s theme with accent %s", self._palette.mode, self._palette.accent)
        return self._palette

    def _persist(self) -> None:
        try:
            self._config_manager.save(self._config)
        except OSError as exc:
            logger.error("Could not persist visual preferences: %s", exc)

    def _on_system_scheme_changed(self, _scheme: object) -> None:
        self.refresh_from_system()


__all__ = [
    "ThemeManager",
    "detect_system_theme",
    "resolve_theme",
]
