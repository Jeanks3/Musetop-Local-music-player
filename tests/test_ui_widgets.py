from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from musetop.core.tags_reader import TrackInfo
from musetop.ui.icons.svg_icons import ICON_NAMES, clear_icon_cache, icon_path, render_icon
from musetop.ui.widgets.formatting import format_duration
from musetop.ui.widgets.player_bar import PlayerBar
from musetop.ui.widgets.playlist_model import ROW_MIME_TYPE, PlaylistTableModel


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0:00"),
        (59, "0:59"),
        (60, "1:00"),
        (3599, "59:59"),
        (3600, "1:00:00"),
        (None, "0:00"),
        (-5, "0:00"),
        (float("nan"), "0:00"),
    ],
)
def test_format_duration(seconds, expected: str) -> None:
    assert format_duration(seconds) == expected


def test_player_bar_metadata_and_position(qtbot) -> None:
    bar = PlayerBar()
    qtbot.addWidget(bar)
    track = TrackInfo(Path("/music/a.mp3"), "Titulo", "Artista", "Album", 125.0)
    bar.set_track(track)
    assert bar.title_label.text() == "Titulo"
    assert bar.subtitle_label.text() == "Artista - Album"
    bar.set_duration(125.0)
    assert bar.total_time.text() == "2:05"
    bar.set_position(65.0)
    assert bar.current_time.text() == "1:05"
    assert 500 <= bar.progress_slider.value() <= 530
    bar.set_track(None)
    assert bar.title_label.text() == "Sin reproducción"


def test_player_bar_state_changes_tooltip(qtbot) -> None:
    bar = PlayerBar()
    qtbot.addWidget(bar)
    assert bar.play_button.toolTip() == "Reproducir"
    bar.set_state("playing")
    assert bar.play_button.toolTip() == "Pausar"
    bar.set_state("paused")
    assert bar.play_button.toolTip() == "Reproducir"


def test_player_bar_volume_is_clamped_to_slider(qtbot) -> None:
    bar = PlayerBar()
    qtbot.addWidget(bar)
    bar.set_volume(150)
    assert bar.volume_slider.value() == 100
    bar.set_volume(-5)
    assert bar.volume_slider.value() == 0


def test_player_bar_repeat_signal(qtbot) -> None:
    bar = PlayerBar()
    qtbot.addWidget(bar)
    with qtbot.waitSignal(bar.repeat_toggled) as blocker:
        bar.repeat_button.setChecked(True)
    assert blocker.args == [True]


def test_playlist_model_columns_and_data() -> None:
    from musetop.core.playlist import Playlist

    playlist = Playlist(
        [
            TrackInfo(Path("/music/a.mp3"), "A", "Artista A", "Album A", 61.0),
            TrackInfo(Path("/music/b.flac"), "B", "Artista B", "Album B", 125.0),
        ]
    )
    model = PlaylistTableModel(playlist)
    assert model.rowCount() == 2
    assert model.columnCount() == 5
    assert model.headerData(1, Qt.Orientation.Horizontal) == "Título"
    assert model.data(model.index(0, 0)) == "1"
    assert model.data(model.index(1, 1)) == "B"
    assert model.data(model.index(1, 4)) == "2:05"
    assert model.data(model.index(0, 1), Qt.ItemDataRole.UserRole) == playlist[0]
    assert str(playlist[0].path) in model.data(model.index(0, 1), Qt.ItemDataRole.ToolTipRole)
    assert model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsDragEnabled
    assert model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsSelectable


def test_playlist_model_mime_and_mutations() -> None:
    from musetop.core.playlist import Playlist

    playlist = Playlist(
        [
            TrackInfo(Path("/music/a.mp3"), "A", "Artist", "Album", 1.0),
            TrackInfo(Path("/music/b.mp3"), "B", "Artist", "Album", 1.0),
            TrackInfo(Path("/music/c.mp3"), "C", "Artist", "Album", 1.0),
        ]
    )
    model = PlaylistTableModel(playlist)
    mime = model.mimeData([model.index(0, 0), model.index(2, 0)])
    assert mime.hasFormat(ROW_MIME_TYPE)
    assert bytes(mime.data(ROW_MIME_TYPE)) == b"0,2"
    assert model.supportedDropActions() == Qt.DropAction.MoveAction
    assert model.move_tracks([0], 3) is True
    assert [track.title for track in playlist] == ["B", "C", "A"]
    removed = model.remove_rows([1])
    assert [track.title for track in removed] == ["C"]
    assert model.rowCount() == 2


def test_all_icons_exist_and_render(qtbot) -> None:
    clear_icon_cache()
    for name in ICON_NAMES:
        path = icon_path(name)
        assert path.is_file(), name
        svg = path.read_text(encoding="utf-8")
        assert "currentColor" in svg
        icon = render_icon(name, "#112233")
        assert not icon.isNull()
        assert not icon.pixmap(24, 24).isNull()
    assert render_icon("missing-icon", "#000000").isNull()


def test_icon_cache_reuses_instances() -> None:
    clear_icon_cache()
    first = render_icon("play", "#ff0000")
    second = render_icon("play", "#FF0000")
    assert first is second
