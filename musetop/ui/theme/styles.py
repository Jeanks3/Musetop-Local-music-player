"""Qt stylesheet generated from theme tokens."""

from __future__ import annotations

from musetop.ui.theme.colors import ThemePalette


def build_stylesheet(palette: ThemePalette) -> str:
    """Return the application QSS for ``palette``."""

    return f"""
QMainWindow, QWidget#centralWidget {{
    background-color: {palette.background};
    color: {palette.text};
}}
QToolBar#mainToolBar {{
    background-color: {palette.surface};
    border: none;
    border-bottom: 1px solid {palette.border};
    padding: 6px 10px;
    spacing: 6px;
}}
QLabel#toolbarLabel {{
    color: {palette.text_muted};
    padding: 0 4px;
}}
QToolBar#mainToolBar QToolButton {{
    background-color: transparent;
    color: {palette.text};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 9px;
}}
QToolBar#mainToolBar QToolButton:hover {{
    background-color: {palette.hover};
    border-color: {palette.border};
}}
QToolBar#mainToolBar QToolButton:pressed {{
    background-color: {palette.pressed};
}}
QToolBar#mainToolBar QToolButton:disabled {{
    color: {palette.disabled_text};
}}
QStatusBar {{
    background-color: {palette.surface};
    color: {palette.text_muted};
    border-top: 1px solid {palette.border};
}}
QStatusBar QLabel {{
    color: {palette.text_muted};
}}
QTableView#playlistView {{
    background-color: {palette.surface};
    alternate-background-color: {palette.surface_alt};
    color: {palette.text};
    border: 1px solid {palette.border};
    border-radius: 8px;
    gridline-color: {palette.border};
    selection-background-color: {palette.accent};
    selection-color: {palette.on_accent};
    outline: 0;
}}
QTableView#playlistView::item {{
    padding: 5px 8px;
    border: none;
}}
QTableView#playlistView::item:hover {{
    background-color: {palette.hover};
}}
QTableView#playlistView::item:selected {{
    background-color: {palette.accent};
    color: {palette.on_accent};
}}
QHeaderView::section {{
    background-color: {palette.surface_alt};
    color: {palette.text_muted};
    border: none;
    border-bottom: 1px solid {palette.border};
    padding: 7px 8px;
    font-weight: 600;
}}
QWidget#playerBar {{
    background-color: {palette.surface};
    border: 1px solid {palette.border};
    border-radius: 10px;
}}
QLabel#trackTitle {{
    color: {palette.text};
    font-size: 15px;
    font-weight: 600;
}}
QLabel#trackSubtitle, QLabel#timeLabel {{
    color: {palette.text_muted};
}}
QPushButton#transportButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 0;
}}
QPushButton#transportButton:hover {{
    background-color: {palette.hover};
    border-color: {palette.border};
}}
QPushButton#transportButton:pressed {{
    background-color: {palette.pressed};
}}
QPushButton#transportButton:checked {{
    background-color: {palette.accent};
    border-color: {palette.accent};
}}
QPushButton#transportButton:focus {{
    border-color: {palette.accent};
}}
QPushButton#primaryButton {{
    background-color: {palette.accent};
    border: 2px solid {palette.accent};
    border-radius: 22px;
    padding: 0;
}}
QPushButton#primaryButton:hover {{
    background-color: {palette.accent_hover};
    border-color: {palette.accent_hover};
}}
QPushButton#primaryButton:pressed {{
    background-color: {palette.accent_pressed};
    border-color: {palette.accent_pressed};
}}
QPushButton#primaryButton:focus {{
    border-color: {palette.on_accent};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background-color: {palette.border};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background-color: {palette.accent};
    border-radius: 2px;
}}
QSlider::add-page:horizontal {{
    background-color: {palette.border};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background-color: {palette.accent};
}}
QSlider::handle:horizontal:hover {{
    background-color: {palette.accent_hover};
}}
QSlider#volumeSlider::handle:horizontal {{
    width: 11px;
    height: 11px;
    margin: -4px 0;
    border-radius: 5px;
}}
QComboBox {{
    background-color: {palette.surface};
    color: {palette.text};
    border: 1px solid {palette.border};
    border-radius: 6px;
    padding: 5px 9px;
    min-width: 138px;
}}
QComboBox:hover, QComboBox:focus {{
    border-color: {palette.accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {palette.surface};
    color: {palette.text};
    border: 1px solid {palette.border};
    selection-background-color: {palette.accent};
    selection-color: {palette.on_accent};
    outline: 0;
}}
QPushButton#accentButton {{
    background-color: {palette.surface};
    color: {palette.text};
    border: 1px solid {palette.border};
    border-radius: 6px;
    padding: 5px 10px;
}}
QPushButton#accentButton:hover {{
    background-color: {palette.hover};
    border-color: {palette.accent};
}}
QToolTip {{
    background-color: {palette.surface};
    color: {palette.text};
    border: 1px solid {palette.border};
    padding: 5px;
}}
QDialog, QMessageBox {{
    background-color: {palette.background};
    color: {palette.text};
}}
QScrollBar:vertical {{
    background: {palette.surface};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {palette.border};
    min-height: 24px;
    border-radius: 6px;
}}
QScrollBar::handle:vertical:hover {{
    background: {palette.accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {palette.surface};
    height: 12px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {palette.border};
    min-width: 24px;
    border-radius: 6px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {palette.accent};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""
