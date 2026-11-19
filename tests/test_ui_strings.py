"""Live user-interface string guard: no emoji may be shown to users."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from musetop.app.config import ConfigManager
from musetop.ui.main_window import MainWindow
from tests.fake_engine import FakeEngine
from tests.test_architecture import EMOJI_PATTERN


def _visible_strings(window: MainWindow) -> list[str]:
    texts = [window.windowTitle(), window.statusBar().currentMessage()]
    for action in window.findChildren(type(window.open_files_action)):
        texts.extend([action.text(), action.toolTip(), action.statusTip()])
    for widget in window.findChildren(QWidget):
        texts.extend(
            [
                widget.windowTitle(),
                widget.toolTip(),
                widget.statusTip(),
                widget.accessibleName(),
            ]
        )
        text_method = getattr(widget, "text", None)
        if callable(text_method):
            texts.append(str(text_method()))
        placeholder = getattr(widget, "placeholderText", None)
        if callable(placeholder):
            texts.append(str(placeholder()))
    return [text for text in texts if text]


def test_live_ui_has_no_emoji(qtbot, tmp_path) -> None:
    window = MainWindow(ConfigManager(tmp_path / "settings.json"), FakeEngine())
    qtbot.addWidget(window)
    window.show()
    offenders = [text for text in _visible_strings(window) if EMOJI_PATTERN.search(text)]
    assert not offenders, f"Emoji found in live UI strings: {offenders}"
