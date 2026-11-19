from __future__ import annotations

from pathlib import Path

import pytest

from musetop.core.tags_reader import (
    UNKNOWN_ALBUM,
    UNKNOWN_ARTIST,
    TrackInfo,
    read_track,
)
from tests.audio_factory import (
    SUPPORTED_TEST_FORMATS,
    ffmpeg_available,
    generate_audio,
    write_wav_id3,
)

pytestmark = pytest.mark.integration

if not ffmpeg_available():  # pragma: no cover - environment guard
    pytest.skip("ffmpeg is required for tag integration tests", allow_module_level=True)


@pytest.fixture(scope="module")
def tagged_files(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    directory = tmp_path_factory.mktemp("tagged")
    tags = {"title": "Titulo de prueba", "artist": "Artista de prueba", "album": "Album de prueba"}
    files: dict[str, Path] = {}
    for extension in SUPPORTED_TEST_FORMATS:
        path = generate_audio(directory / f"track{extension}", duration=1.0, tags=tags)
        if extension == ".wav":
            write_wav_id3(path, tags["title"], tags["artist"], tags["album"])
        files[extension] = path
    return files


@pytest.mark.parametrize("extension", SUPPORTED_TEST_FORMATS)
def test_reads_tags_for_supported_formats(tagged_files: dict[str, Path], extension: str) -> None:
    track = read_track(tagged_files[extension])
    assert track.title == "Titulo de prueba"
    assert track.artist == "Artista de prueba"
    assert track.album == "Album de prueba"
    assert track.duration == pytest.approx(1.0, abs=0.15)


def test_mp4_uses_standard_metadata(tmp_path: Path) -> None:
    path = generate_audio(
        tmp_path / "tagged.m4a",
        duration=1.0,
        tags={"title": "M4A", "artist": "Artista M4A", "album": "Album M4A"},
    )
    track = read_track(path)
    assert (track.title, track.artist, track.album) == ("M4A", "Artista M4A", "Album M4A")


def test_raw_aac_falls_back_to_stem_but_keeps_duration(tmp_path: Path) -> None:
    path = generate_audio(tmp_path / "sin_etiquetas.aac", duration=1.0)
    track = read_track(path)
    assert track.title == "sin_etiquetas"
    assert track.artist == UNKNOWN_ARTIST
    assert track.album == UNKNOWN_ALBUM
    assert track.duration == pytest.approx(1.0, abs=0.2)


def test_missing_file_returns_placeholders(tmp_path: Path) -> None:
    missing = tmp_path / "missing.mp3"
    track = read_track(missing)
    assert track == TrackInfo(missing, "missing", UNKNOWN_ARTIST, UNKNOWN_ALBUM, 0.0)


def test_invalid_audio_returns_placeholders(tmp_path: Path) -> None:
    broken = tmp_path / "broken.flac"
    broken.write_bytes(b"not audio")
    track = read_track(broken)
    assert track.title == "broken"
    assert track.duration == 0.0


def test_from_path_classmethod(tagged_files: dict[str, Path]) -> None:
    track = TrackInfo.from_path(tagged_files[".mp3"])
    assert track.title == "Titulo de prueba"
