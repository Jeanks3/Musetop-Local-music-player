"""Audio playback engine backed by libmpv.

The engine owns the playback queue, transport state, seek position, volume and
repeat mode. It emits Qt signals and has no knowledge of widgets, themes or the
rest of the user interface.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QTimer, Qt, Signal

from musetop.core import mpv_loader

logger = logging.getLogger(__name__)


class PlaybackState(StrEnum):
    """Transport states exposed to the user interface."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class PlaybackMode(StrEnum):
    """Supported end-of-track behaviors."""

    SEQUENTIAL = "sequential"
    REPEAT_ALL = "repeat_all"


DEFAULT_MPV_OPTIONS: dict[str, Any] = {
    "idle": True,
    "video": False,
    "audio_display": False,
    "terminal": False,
    "config": False,
    "ytdl": False,
    "osc": False,
    "input_default_bindings": False,
    "input_vo_keyboard": False,
    "osd_level": 0,
}


class AudioEngine(QObject):
    """Qt-observable facade over libmpv playback."""

    state_changed = Signal(str)
    position_changed = Signal(float)
    duration_changed = Signal(float)
    track_changed = Signal(int)
    playlist_changed = Signal()
    volume_changed = Signal(int)
    error_occurred = Signal(str)
    playback_finished = Signal()

    _end_file_reached = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        mpv_options: Mapping[str, Any] | None = None,
        poll_interval_ms: int = 200,
    ) -> None:
        super().__init__(parent)
        self._player: Any | None = None
        self._event_wrapper: Any | None = None
        self._playlist: list[Path] = []
        self._index = -1
        self._state = PlaybackState.STOPPED
        self._mode = PlaybackMode.SEQUENTIAL
        self._position = 0.0
        self._duration = 0.0
        self._volume = 80
        self._options: dict[str, Any] = dict(DEFAULT_MPV_OPTIONS)
        if mpv_options:
            self._options.update(mpv_options)

        self._timer = QTimer(self)
        self._timer.setInterval(max(25, poll_interval_ms))
        self._timer.timeout.connect(self._poll)

        self._end_file_reached.connect(
            self._advance_after_end,
            Qt.ConnectionType.QueuedConnection,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def open(self) -> bool:
        """Create the libmpv backend. Returns False when libmpv is unavailable."""

        if self._player is not None:
            return True

        try:
            mpv_module = mpv_loader.load_mpv_module()
        except OSError as exc:
            logger.error("libmpv could not be loaded: %s", exc)
            self.error_occurred.emit(str(exc))
            return False

        try:
            player = mpv_module.MPV(**self._options)
            player.volume = self._volume
            self._event_wrapper = player.event_callback("end-file")(self._on_end_file)
        except Exception as exc:  # pragma: no cover - depends on native runtime
            logger.exception("libmpv initialization failed")
            self.error_occurred.emit(f"No se pudo iniciar el motor de audio: {exc}")
            return False

        self._player = player
        logger.info("Audio engine ready with %s", player.mpv_version)
        return True

    def shutdown(self) -> None:
        """Stop timers and release the libmpv handle."""

        self._timer.stop()
        if self._player is None:
            return
        player = self._player
        self._player = None
        try:
            if self._event_wrapper is not None:
                player.unregister_event_callback(self._event_wrapper)
            player.terminate()
        except Exception:  # pragma: no cover - native teardown
            logger.exception("libmpv teardown failed")
        finally:
            self._event_wrapper = None
            self._state = PlaybackState.STOPPED

    @property
    def is_open(self) -> bool:
        """Whether the native engine has been created."""

        return self._player is not None

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------
    @property
    def playlist(self) -> tuple[Path, ...]:
        """Return an immutable snapshot of the queue."""

        return tuple(self._playlist)

    @property
    def current_index(self) -> int:
        """Return the current queue index or -1 when empty."""

        return self._index

    @property
    def current_path(self) -> Path | None:
        """Return the current path or None."""

        if 0 <= self._index < len(self._playlist):
            return self._playlist[self._index]
        return None

    def play_index(self, index: int) -> bool:
        """Start playback at ``index``. Returns True when playback was requested."""

        if not 0 <= index < len(self._playlist):
            logger.warning("Playback index out of range: %s", index)
            return False
        path = self._playlist[index]
        if not path.is_file():
            message = f"No se encontró el archivo: {path.name}"
            logger.error("Missing media file: %s", path)
            self.error_occurred.emit(message)
            return False
        if not self.open():
            return False

        self._index = index
        self._position = 0.0
        self._duration = 0.0
        self.track_changed.emit(index)
        self.position_changed.emit(0.0)
        self.duration_changed.emit(0.0)
        try:
            self._player.play(str(path))
            self._player.pause = False
        except Exception as exc:  # pragma: no cover - native backend
            logger.exception("libmpv could not play %s", path)
            self.error_occurred.emit(f"No se pudo reproducir {path.name}: {exc}")
            self._set_state(PlaybackState.STOPPED)
            return False

        self._set_state(PlaybackState.PLAYING)
        self._timer.start()
        logger.info("Playing %s", path.name)
        return True

    def set_playlist(
        self,
        paths: Iterable[str | Path],
        *,
        start_index: int | None = None,
        preserve_current: bool = True,
    ) -> None:
        """Replace the queue, optionally preserving the currently playing file."""

        current = self.current_path if preserve_current else None
        self._playlist = [Path(item) for item in paths]
        self._playlist = [item for item in self._playlist if item.is_file()]
        self.playlist_changed.emit()

        if start_index is not None and 0 <= start_index < len(self._playlist):
            self.play_index(start_index)
            return

        if current is not None and current in self._playlist:
            new_index = self._playlist.index(current)
            if new_index != self._index:
                self._index = new_index
                self.track_changed.emit(new_index)
            return

        if self._index != -1 or self._state is not PlaybackState.STOPPED:
            self.stop()
        self._index = -1
        self._set_state(PlaybackState.STOPPED)
        self.track_changed.emit(-1)

    def append_paths(self, paths: Iterable[str | Path]) -> int:
        """Append new unique paths and return how many were added."""

        existing = set(self._playlist)
        added = 0
        for item in paths:
            path = Path(item)
            if path in existing or not path.is_file():
                continue
            self._playlist.append(path)
            existing.add(path)
            added += 1
        if added:
            self.playlist_changed.emit()
        return added

    def remove_path(self, path: str | Path) -> None:
        """Remove one path while preserving the current track when possible."""

        remaining = [item for item in self._playlist if item != Path(path)]
        self.set_playlist(remaining)

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------
    @property
    def state(self) -> PlaybackState:
        """Current transport state."""

        return self._state

    @property
    def mode(self) -> PlaybackMode:
        """Current end-of-track mode."""

        return self._mode

    @property
    def position(self) -> float:
        """Last polled playback position in seconds."""

        return self._position

    @property
    def duration(self) -> float:
        """Last known track duration in seconds."""

        return self._duration

    @property
    def volume(self) -> int:
        """Current volume in the 0-100 range."""

        return self._volume

    def play(self) -> bool:
        """Start or resume playback."""

        if self._state is PlaybackState.PAUSED and self._player is not None:
            self._player.pause = False
            self._set_state(PlaybackState.PLAYING)
            self._timer.start()
            return True
        if self._state is PlaybackState.PLAYING:
            return True
        if self._player is None and not self.open():
            return False
        if self._index >= 0:
            return self.play_index(self._index)
        if self._playlist:
            return self.play_index(0)
        return False

    def pause(self) -> None:
        """Pause playback when currently playing."""

        if self._state is not PlaybackState.PLAYING or self._player is None:
            return
        self._player.pause = True
        self._set_state(PlaybackState.PAUSED)

    def toggle_pause(self) -> None:
        """Toggle between playing and paused."""

        if self._state is PlaybackState.PLAYING:
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        """Stop playback and reset the position."""

        if self._player is not None:
            try:
                self._player.stop()
            except Exception:  # pragma: no cover - native backend
                logger.exception("libmpv stop failed")
        self._timer.stop()
        self._position = 0.0
        self.position_changed.emit(0.0)
        self._set_state(PlaybackState.STOPPED)

    def next(self) -> bool:
        """Advance to the next track according to the playback mode."""

        if not self._playlist:
            return False
        if self._index + 1 < len(self._playlist):
            return self.play_index(self._index + 1)
        if self._mode is PlaybackMode.REPEAT_ALL:
            return self.play_index(0)
        self.stop()
        self.playback_finished.emit()
        return False

    def previous(self) -> bool:
        """Go to the previous track, wrapping in repeat-all mode."""

        if not self._playlist:
            return False
        if self._index > 0:
            return self.play_index(self._index - 1)
        if self._mode is PlaybackMode.REPEAT_ALL:
            return self.play_index(len(self._playlist) - 1)
        return self.play_index(0)

    def seek(self, seconds: float) -> None:
        """Seek to an absolute position, clamped to the known duration."""

        if self._player is None or self._state is PlaybackState.STOPPED:
            return
        target = max(0.0, float(seconds))
        if self._duration > 0:
            target = min(target, self._duration)
        try:
            self._player.seek(target, reference="absolute")
        except Exception:  # pragma: no cover - native backend
            logger.exception("libmpv seek failed")
            return
        self._position = target
        self.position_changed.emit(target)

    def set_volume(self, volume: int | float) -> None:
        """Set the volume, clamped to 0-100."""

        normalized = max(0, min(100, int(round(float(volume)))))
        self._volume = normalized
        if self._player is not None:
            try:
                self._player.volume = normalized
            except Exception:  # pragma: no cover - native backend
                logger.exception("libmpv volume update failed")
        self.volume_changed.emit(normalized)

    def set_mode(self, mode: PlaybackMode | str) -> None:
        """Set the end-of-track mode."""

        try:
            self._mode = PlaybackMode(mode)
        except ValueError as exc:
            raise ValueError(f"Modo de reproducción desconocido: {mode}") from exc

    def toggle_mode(self) -> PlaybackMode:
        """Switch between sequential and repeat-all."""

        self._mode = (
            PlaybackMode.REPEAT_ALL
            if self._mode is PlaybackMode.SEQUENTIAL
            else PlaybackMode.SEQUENTIAL
        )
        return self._mode

    # ------------------------------------------------------------------
    # Native callbacks
    # ------------------------------------------------------------------
    def _on_end_file(self, event: Any) -> None:
        """Forward natural EOF events to the Qt thread."""

        data = getattr(event, "data", None)
        if data is None:
            return
        if int(getattr(data, "reason", -1)) == 0:
            self._end_file_reached.emit()

    def _advance_after_end(self) -> None:
        if self._state is PlaybackState.STOPPED:
            return
        logger.debug("Track ended at index %s", self._index)
        self.next()

    def _poll(self) -> None:
        if self._player is None:
            return
        try:
            position = self._player.time_pos
            duration = self._player.duration
        except Exception:  # pragma: no cover - property unavailable while loading
            return

        if position is not None and abs(float(position) - self._position) >= 0.02:
            self._position = max(0.0, float(position))
            self.position_changed.emit(self._position)
        if duration is not None and abs(float(duration) - self._duration) >= 0.05:
            self._duration = max(0.0, float(duration))
            self.duration_changed.emit(self._duration)

    def _set_state(self, state: PlaybackState) -> None:
        if state is self._state:
            return
        self._state = state
        self.state_changed.emit(state.value)
        logger.debug("Playback state changed to %s", state.value)
