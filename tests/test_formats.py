from __future__ import annotations

import time
from pathlib import Path

from musetop.core.formats import (
    SUPPORTED_EXTENSIONS,
    is_supported_file,
    scan_paths,
)


def test_all_required_extensions_are_supported() -> None:
    assert {
        ".mp3",
        ".flac",
        ".wav",
        ".ogg",
        ".opus",
        ".m4a",
        ".aac",
    } <= SUPPORTED_EXTENSIONS


def test_supported_extension_is_case_insensitive(tmp_path: Path) -> None:
    path = tmp_path / "song.MP3"
    path.write_bytes(b"")
    assert is_supported_file(path)


def test_unsupported_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")
    assert not is_supported_file(path)
    result = scan_paths([path])
    assert result.files == ()
    assert result.rejected == (path,)


def test_folder_scan_is_non_recursive(tmp_path: Path) -> None:
    direct = tmp_path / "direct.flac"
    direct.write_bytes(b"")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "inside.mp3").write_bytes(b"")

    result = scan_paths([tmp_path])
    assert result.files == (direct,)


def test_mixed_folder_and_explicit_file(tmp_path: Path) -> None:
    folder = tmp_path / "music"
    folder.mkdir()
    first = folder / "b.ogg"
    second = folder / "a.mp3"
    first.write_bytes(b"")
    second.write_bytes(b"")
    (folder / "cover.jpg").write_bytes(b"")
    explicit = tmp_path / "c.flac"
    explicit.write_bytes(b"")

    result = scan_paths([folder, explicit])
    assert set(result.files) == {first, second, explicit}
    assert result.rejected == ()


def test_duplicate_paths_are_removed(tmp_path: Path) -> None:
    path = tmp_path / "one.mp3"
    path.write_bytes(b"")
    result = scan_paths([path, path, tmp_path])
    assert result.files == (path,)


def test_empty_folder_is_reported(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    result = scan_paths([tmp_path])
    assert result.files == ()
    assert result.empty_folders == (tmp_path,)


def test_missing_path_is_reported(tmp_path: Path) -> None:
    missing = tmp_path / "nope.wav"
    result = scan_paths([missing])
    assert result.missing == (missing,)
    assert result.files == ()


def test_scan_500_files_is_under_five_seconds(tmp_path: Path) -> None:
    for index in range(500):
        (tmp_path / f"track_{index:03d}.mp3").write_bytes(b"")
    started = time.perf_counter()
    result = scan_paths([tmp_path])
    elapsed = time.perf_counter() - started
    assert len(result.files) == 500
    assert elapsed < 5.0
