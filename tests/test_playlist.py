from __future__ import annotations

from pathlib import Path

from musetop.core.playlist import Playlist
from musetop.core.tags_reader import TrackInfo


def make_track(name: str) -> TrackInfo:
    return TrackInfo(Path(f"/music/{name}.mp3"), name, "Artist", "Album", 1.0)


def test_add_tracks_and_deduplicate() -> None:
    playlist = Playlist()
    assert playlist.add_tracks([make_track("a"), make_track("b")]) == 2
    assert playlist.add_tracks([make_track("b"), make_track("c")]) == 1
    assert [track.title for track in playlist] == ["a", "b", "c"]
    assert len(playlist) == 3
    assert playlist.index_of("/music/b.mp3") == 1
    assert playlist.index_of("/music/missing.mp3") == -1


def test_remove_rows_ignores_invalid_indices() -> None:
    playlist = Playlist([make_track("a"), make_track("b"), make_track("c")])
    removed = playlist.remove_rows([2, 99, -1, 0])
    assert [track.title for track in removed] == ["a", "c"]
    assert [track.title for track in playlist] == ["b"]


def test_move_rows_before_destination() -> None:
    playlist = Playlist([make_track("a"), make_track("b"), make_track("c"), make_track("d")])
    assert playlist.move_rows([0], 3) is True
    assert [track.title for track in playlist] == ["b", "c", "a", "d"]


def test_move_rows_multiple() -> None:
    playlist = Playlist([make_track("a"), make_track("b"), make_track("c"), make_track("d")])
    assert playlist.move_rows([1, 2], 4) is True
    assert [track.title for track in playlist] == ["a", "d", "b", "c"]


def test_move_rows_to_start_and_end() -> None:
    playlist = Playlist([make_track("a"), make_track("b"), make_track("c")])
    assert playlist.move_rows([2], 0) is True
    assert [track.title for track in playlist] == ["c", "a", "b"]
    assert playlist.move_rows([0], 99) is True
    assert [track.title for track in playlist] == ["a", "b", "c"]


def test_move_rows_noop() -> None:
    playlist = Playlist([make_track("a"), make_track("b")])
    assert playlist.move_rows([], 0) is False
    assert playlist.move_rows([0], 0) is False
    assert playlist.move_rows([0], 1) is False


def test_paths_and_clear() -> None:
    playlist = Playlist([make_track("a"), make_track("b")])
    assert playlist.paths == (Path("/music/a.mp3"), Path("/music/b.mp3"))
    assert len(playlist.tracks) == 2
    playlist.clear()
    assert len(playlist) == 0
    assert playlist.paths == ()
