"""Bottom playback bar: metadata, progress, transport and volume."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from musetop.app.config import DEFAULT_ACCENT
from musetop.core.tags_reader import TrackInfo
from musetop.ui.icons.svg_icons import render_icon
from musetop.ui.widgets.formatting import format_duration


class PlayerBar(QWidget):
    """Playback controls that only emit user intentions."""

    play_pause_requested = Signal()
    stop_requested = Signal()
    next_requested = Signal()
    previous_requested = Signal()
    seek_requested = Signal(float)
    volume_changed = Signal(int)
    repeat_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("playerBar")
        self._duration = 0.0
        self._seeking = False
        self._icon_color = "#1b1f24"
        self._accent_color = DEFAULT_ACCENT
        self._on_accent = "#ffffff"

        self.title_label = QLabel("Sin reproducción")
        self.title_label.setObjectName("trackTitle")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.subtitle_label = QLabel("Abre archivos o arrastra una carpeta")
        self.subtitle_label.setObjectName("trackSubtitle")
        self.subtitle_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.current_time = QLabel("0:00")
        self.current_time.setObjectName("timeLabel")
        self.total_time = QLabel("0:00")
        self.total_time.setObjectName("timeLabel")

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setObjectName("progressSlider")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)

        self.previous_button = self._make_button("previous", "Anterior")
        self.play_button = self._make_button("play", "Reproducir", primary=True)
        self.stop_button = self._make_button("stop", "Detener")
        self.next_button = self._make_button("next", "Siguiente")
        self.repeat_button = self._make_button("repeat", "Repetir todo", checkable=True)
        self.volume_icon = QLabel()
        self.volume_icon.setObjectName("volumeIcon")
        self.volume_icon.setToolTip("Volumen")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setToolTip("Volumen")

        self._build_layout()
        self._connect_signals()
        self.refresh_icons(self._icon_color, self._accent_color, self._on_accent)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _make_button(self, icon_name: str, tooltip: str, *, checkable: bool = False, primary: bool = False) -> QPushButton:
        button = QPushButton()
        button.setObjectName("primaryButton" if primary else "transportButton")
        button.setToolTip(tooltip)
        button.setCheckable(checkable)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        size = 44 if primary else 34
        button.setFixedSize(size, size)
        icon_size = 24 if primary else 18
        button.setIconSize(QSize(icon_size, icon_size))
        button.setProperty("iconName", icon_name)
        return button

    def _build_layout(self) -> None:
        progress_row = QHBoxLayout()
        progress_row.setContentsMargins(0, 0, 0, 0)
        progress_row.setSpacing(10)
        progress_row.addWidget(self.current_time)
        progress_row.addWidget(self.progress_slider, 1)
        progress_row.addWidget(self.total_time)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.subtitle_label)

        transport_layout = QHBoxLayout()
        transport_layout.setContentsMargins(0, 0, 0, 0)
        transport_layout.setSpacing(8)
        transport_layout.addWidget(self.previous_button)
        transport_layout.addWidget(self.play_button)
        transport_layout.addWidget(self.stop_button)
        transport_layout.addWidget(self.next_button)
        transport_layout.addWidget(self.repeat_button)

        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(6)
        volume_layout.addWidget(self.volume_icon)
        volume_layout.addWidget(self.volume_slider)

        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(12)
        controls_row.addLayout(info_layout, 1)
        controls_row.addStretch(0)
        controls_row.addLayout(transport_layout)
        controls_row.addStretch(0)
        controls_row.addLayout(volume_layout)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 14)
        root.setSpacing(8)
        root.addLayout(progress_row)
        root.addLayout(controls_row)

    def _connect_signals(self) -> None:
        self.play_button.clicked.connect(self.play_pause_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.next_button.clicked.connect(self.next_requested)
        self.previous_button.clicked.connect(self.previous_requested)
        self.volume_slider.valueChanged.connect(self.volume_changed)
        self.repeat_button.toggled.connect(self._on_repeat_toggled)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh_icons(self, icon_color: str, accent_color: str, on_accent: str) -> None:
        """Recolor all icons for the active theme."""

        self._icon_color = icon_color
        self._accent_color = accent_color
        self._on_accent = on_accent
        self.previous_button.setIcon(render_icon("previous", icon_color))
        self.stop_button.setIcon(render_icon("stop", icon_color))
        self.next_button.setIcon(render_icon("next", icon_color))
        self.volume_icon.setPixmap(render_icon("volume", icon_color).pixmap(20, 20))
        self._update_play_icon()
        self._update_repeat_icon()

    def set_track(self, track: TrackInfo | None) -> None:
        """Show metadata for the current track."""

        if track is None:
            self.title_label.setText("Sin reproducción")
            self.subtitle_label.setText("Abre archivos o arrastra una carpeta")
            return
        self.title_label.setText(track.title)
        self.subtitle_label.setText(f"{track.artist} - {track.album}")

    def set_state(self, state: str) -> None:
        """Update the play/pause button from the engine state."""

        self.play_button.setProperty("playbackState", state)
        self._update_play_icon()

    def set_position(self, position: float, duration: float | None = None) -> None:
        """Update the position labels and slider unless the user is seeking."""

        if duration is not None:
            self.set_duration(duration)
        if self._seeking:
            return
        self.current_time.setText(format_duration(position))
        if self._duration > 0:
            value = int(max(0.0, min(1.0, position / self._duration)) * 1000)
            with QSignalBlocker(self.progress_slider):
                self.progress_slider.setValue(value)

    def set_duration(self, duration: float) -> None:
        """Update the total duration label."""

        self._duration = max(0.0, float(duration))
        self.total_time.setText(format_duration(self._duration))
        self.progress_slider.setEnabled(self._duration > 0)
        if self._duration <= 0:
            with QSignalBlocker(self.progress_slider):
                self.progress_slider.setValue(0)

    def set_volume(self, volume: int) -> None:
        """Update the volume slider without re-emitting the signal."""

        with QSignalBlocker(self.volume_slider):
            self.volume_slider.setValue(max(0, min(100, int(volume))))

    def set_repeat_checked(self, checked: bool) -> None:
        """Update the repeat toggle without re-emitting the signal."""

        with QSignalBlocker(self.repeat_button):
            self.repeat_button.setChecked(checked)
        self._update_repeat_icon()

    def reset_progress(self) -> None:
        """Reset position labels after stop."""

        self.current_time.setText("0:00")
        with QSignalBlocker(self.progress_slider):
            self.progress_slider.setValue(0)

    # ------------------------------------------------------------------
    # Internal behavior
    # ------------------------------------------------------------------
    def _update_play_icon(self) -> None:
        playing = self.play_button.property("playbackState") == "playing"
        name = "pause" if playing else "play"
        self.play_button.setIcon(render_icon(name, self._on_accent))
        self.play_button.setToolTip("Pausar" if playing else "Reproducir")

    def _update_repeat_icon(self) -> None:
        color = self._on_accent if self.repeat_button.isChecked() else self._icon_color
        self.repeat_button.setIcon(render_icon("repeat", color))

    def _on_repeat_toggled(self, checked: bool) -> None:
        self._update_repeat_icon()
        self.repeat_toggled.emit(checked)

    def _on_slider_pressed(self) -> None:
        self._seeking = True

    def _on_slider_moved(self, value: int) -> None:
        if self._duration > 0:
            self.current_time.setText(format_duration(value / 1000 * self._duration))

    def _on_slider_released(self) -> None:
        self._seeking = False
        if self._duration <= 0:
            return
        self.seek_requested.emit(self.progress_slider.value() / 1000 * self._duration)
