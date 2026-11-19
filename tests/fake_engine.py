"""Test double for the audio engine; no native playback is started."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from musetop.core.audio_engine import PlaybackMode, PlaybackState


class FakeEngine(QObject):
    state_changed = Signal(str)
    position_changed = Signal(float)
    duration_changed = Signal(float)
    track_changed = Signal(int)
    playlist_changed = Signal()
    volume_changed = Signal(int)
    error_occurred = Signal(str)
    playback_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.state: PlaybackState | str = PlaybackState.STOPPED
        self.mode: PlaybackMode | str = PlaybackMode.SEQUENTIAL
        self.volume = 80
        self.position = 0.0
        self.duration = 0.0
        self.current_index = -1
        self.paths: list[Path] = []
        self.last_play_index: int | None = None
        self.last_seek: float | None = None
        self.calls: list[str] = []

    def set_playlist(self, paths, *, start_index=None, preserve_current=True) -> None:
        self.paths = [Path(path) for path in paths]
        self.calls.append("set_playlist")
        self.playlist_changed.emit()
        if start_index is not None:
            self.play_index(start_index)

    def play_index(self, index: int) -> bool:
        if not 0 <= index < len(self.paths):
            return False
        self.current_index = index
        self.last_play_index = index
        self.state = PlaybackState.PLAYING
        self.calls.append(f"play_index:{index}")
        self.track_changed.emit(index)
        self.state_changed.emit(PlaybackState.PLAYING.value)
        return True

    def play(self) -> bool:
        return self.play_index(max(0, self.current_index))

    def pause(self) -> None:
        self.state = PlaybackState.PAUSED
        self.state_changed.emit(PlaybackState.PAUSED.value)

    def toggle_pause(self) -> None:
        self.calls.append("toggle_pause")
        if self.state is PlaybackState.PLAYING:
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        self.state = PlaybackState.STOPPED
        self.position = 0.0
        self.calls.append("stop")
        self.state_changed.emit(PlaybackState.STOPPED.value)

    def next(self) -> bool:
        self.calls.append("next")
        return self.play_index(self.current_index + 1)

    def previous(self) -> bool:
        self.calls.append("previous")
        return self.play_index(max(0, self.current_index - 1))

    def seek(self, seconds: float) -> None:
        self.last_seek = seconds
        self.position = seconds
        self.calls.append("seek")

    def set_volume(self, volume: int) -> None:
        self.volume = volume
        self.calls.append("set_volume")
        self.volume_changed.emit(volume)

    def set_mode(self, mode) -> None:
        self.mode = PlaybackMode(mode)
        self.calls.append("set_mode")

    def toggle_mode(self):
        self.mode = (
            PlaybackMode.REPEAT_ALL
            if self.mode is PlaybackMode.SEQUENTIAL
            else PlaybackMode.SEQUENTIAL
        )
        return self.mode

    def shutdown(self) -> None:
        self.calls.append("shutdown")
