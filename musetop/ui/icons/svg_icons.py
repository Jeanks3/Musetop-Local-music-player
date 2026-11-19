"""Monochrome SVG icon loader. Icons inherit the active theme color."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICON_DIR = Path(__file__).resolve().parent
_CACHE: dict[tuple[str, str, int], QIcon] = {}

ICON_NAMES = (
    "app",
    "file_plus",
    "folder",
    "next",
    "pause",
    "play",
    "previous",
    "repeat",
    "reset",
    "stop",
    "trash",
    "volume",
)


def icon_path(name: str) -> Path:
    """Return the SVG path for ``name``."""

    return ICON_DIR / f"{name}.svg"


def render_icon(name: str, color: str, size: int = 24) -> QIcon:
    """Render an SVG with ``currentColor`` replaced by ``color``."""

    cache_key = (name, color.lower(), size)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    path = icon_path(name)
    if not path.is_file():
        return QIcon()

    svg = path.read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    icon = QIcon(pixmap)
    _CACHE[cache_key] = icon
    return icon


def clear_icon_cache() -> None:
    """Clear the render cache; used by tests and theme switches."""

    _CACHE.clear()
