"""Integration tests for the libmpv audio engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from musetop.core.audio_engine import AudioEngine, PlaybackMode, PlaybackState
from tests.audio_factory import SUPPORTED_TEST_FORMATS, ffmpeg_available, generate_audio

pytestmark = pytest.mark.integration

if not ffmpeg_available():  # pragma: no cover - environment guard
    pytest.skip("ffmpeg is required for audio integration tests", allow_module_level=True)


@pytest.fixture(scope="module")
def audio_library(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Create one tagged audio file per supported container."""

    directory = tmp_path_factory.mktemp("audio")
    tags = {"title": "Titulo", "artist": "Artista", "album": "Album"}
    files: dict[str, Path] = {}
    for index, extension in enumerate(SUPPORTED_TEST_FORMATS):
        files[extension] = generate_audio(
            directory / f"tone{extension}",
            duration=3.0,
            frequency=330 + index * 40,
            tags=tags,
        )
    return files


@pytest.fixture()
def engine(qtbot: pytest.FixtureRequest) -> AudioEngine:
    instance = AudioEngine(mpv_options={"ao": "null"}, poll_interval_ms=25)
    if not instance.open():
        pytest.skip("libmpv is not available in this environment")
    yield instance
    instance.shutdown()


@pytest.mark.parametrize("extension", SUPPORTED_TEST_FORMATS)
def test_each_supported_format_starts_playback(
    qtbot, engine: AudioEngine, audio_library: dict[str, Path], extension: str
) -> None:
    engine.set_playlist([audio_library[extension]])
    assert engine.play_index(0)
    qtbot.waitUntil(lambda: engine.duration > 0.5, timeout=6000)
    qtbot.waitUntil(lambda: engine.position > 0.02, timeout=6000)
    assert engine.state is PlaybackState.PLAYING
    assert engine.current_index == 0
    assert engine.duration >= 2.0


def test_pause_and_resume(engine: AudioEngine, audio_library: dict[str, Path], qtbot) -> None:
    engine.set_playlist([audio_library[".flac"]])
    engine.play_index(0)
    qtbot.waitUntil(lambda: engine.position > 0.05, timeout=6000)

    engine.pause()
    assert engine.state is PlaybackState.PAUSED
    paused_at = engine.position
    qtbot.wait(250)
    assert engine.position == pytest.approx(paused_at, abs=0.08)

    engine.play()
    assert engine.state is PlaybackState.PLAYING
    qtbot.waitUntil(lambda: engine.position > paused_at + 0.05, timeout=6000)


def test_seek_clamps_and_updates_position(engine: AudioEngine, audio_library: dict[str, Path], qtbot) -> None:
    engine.set_playlist([audio_library[".mp3"]])
    engine.play_index(0)
    qtbot.waitUntil(lambda: engine.duration > 1.0, timeout=6000)
    engine.seek(1.5)
    qtbot.waitUntil(lambda: engine.position >= 1.4, timeout=6000)
    engine.seek(-5)
    qtbot.waitUntil(lambda: engine.position < 0.2, timeout=6000)
    engine.seek(999)
    assert engine.position <= engine.duration + 0.1


def test_volume_is_clamped_and_emitted(qtbot, engine: AudioEngine) -> None:
    with qtbot.waitSignal(engine.volume_changed, timeout=1000) as blocker:
        engine.set_volume(55)
    assert blocker.args == [55]
    assert engine.volume == 55
    engine.set_volume(400)
    assert engine.volume == 100
    engine.set_volume(-10)
    assert engine.volume == 0


def test_next_and_previous(engine: AudioEngine, audio_library: dict[str, Path]) -> None:
    playlist = [audio_library[".mp3"], audio_library[".ogg"], audio_library[".flac"]]
    engine.set_playlist(playlist)
    assert engine.play_index(0)
    assert engine.next()
    assert engine.current_index == 1
    assert engine.previous()
    assert engine.current_index == 0


def test_stop_resets_position(engine: AudioEngine, audio_library: dict[str, Path], qtbot) -> None:
    engine.set_playlist([audio_library[".opus"]])
    engine.play_index(0)
    qtbot.waitUntil(lambda: engine.position > 0.05, timeout=6000)
    engine.stop()
    assert engine.state is PlaybackState.STOPPED
    assert engine.position == 0.0


def test_end_of_track_advances_sequentially(
    qtbot, engine: AudioEngine, tmp_path: Path
) -> None:
    first = generate_audio(tmp_path / "first.flac", duration=0.6)
    second = generate_audio(tmp_path / "second.flac", duration=0.6, frequency=660)
    engine.set_playlist([first, second])
    engine.play_index(0)
    qtbot.waitUntil(lambda: engine.current_index == 1, timeout=12000)
    qtbot.waitUntil(lambda: engine.state is PlaybackState.STOPPED, timeout=12000)


def test_repeat_all_wraps_queue(qtbot, engine: AudioEngine, tmp_path: Path) -> None:
    first = generate_audio(tmp_path / "first.flac", duration=0.5)
    second = generate_audio(tmp_path / "second.flac", duration=0.5, frequency=660)
    engine.set_playlist([first, second])
    engine.set_mode(PlaybackMode.REPEAT_ALL)
    indices: list[int] = []
    engine.track_changed.connect(indices.append)
    engine.play_index(0)
    qtbot.waitUntil(lambda: indices.count(0) >= 2 and 1 in indices, timeout=15000)
    assert engine.mode is PlaybackMode.REPEAT_ALL
    engine.stop()


def test_mode_validation(engine: AudioEngine) -> None:
    engine.set_mode("repeat_all")
    assert engine.mode is PlaybackMode.REPEAT_ALL
    assert engine.toggle_mode() is PlaybackMode.SEQUENTIAL
    with pytest.raises(ValueError):
        engine.set_mode("shuffle")


def test_missing_file_emits_error(qtbot, engine: AudioEngine, tmp_path: Path) -> None:
    missing = tmp_path / "missing.mp3"
    missing.write_bytes(b"not really audio")
    engine.set_playlist([missing])
    missing.unlink()
    with qtbot.waitSignal(engine.error_occurred, timeout=2000) as blocker:
        assert not engine.play_index(0)
    assert "missing.mp3" in blocker.args[0]


def test_play_without_queue_is_safe(engine: AudioEngine) -> None:
    engine.set_playlist([])
    assert engine.play() is False
    assert engine.state is PlaybackState.STOPPED
