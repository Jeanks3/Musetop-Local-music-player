from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QItemSelectionModel, Qt

from musetop.app.config import ConfigManager
from musetop.ui.main_window import MainWindow
from tests.fake_engine import FakeEngine


@pytest.fixture()
def window(qtbot, tmp_path: Path):
    engine = FakeEngine()
    instance = MainWindow(ConfigManager(tmp_path / "settings.json"), engine)
    qtbot.addWidget(instance)
    instance.show()
    yield instance
    instance.close()


def make_files(folder: Path, names: list[str]) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        path = folder / name
        path.write_bytes(b"")
        paths.append(path)
    return paths


def test_starts_empty(window: MainWindow) -> None:
    assert window.playlist_model.rowCount() == 0
    assert window.player_bar.title_label.text() == "Sin reproducción"
    assert window.track_count_label.text() == "0 pistas"


def test_load_folder_with_mixed_formats_and_report_unsupported(
    window: MainWindow, tmp_path: Path, monkeypatch
) -> None:
    folder = tmp_path / "music"
    files = make_files(folder, ["a.mp3", "b.flac", "cover.jpg"])
    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("x", encoding="utf-8")
    captured: list[str] = []
    monkeypatch.setattr(
        "musetop.ui.main_window.QMessageBox.warning",
        lambda parent, title, message: captured.append(message),
    )

    window.load_paths([folder, unsupported])

    assert window.playlist_model.rowCount() == 2
    assert len(window.engine.paths) == 2
    assert window.track_count_label.text() == "2 pistas"
    assert captured
    assert "Formatos no compatibles" in captured[0]
    assert files[2].name not in captured[0]


def test_load_only_unsupported_shows_message(window: MainWindow, tmp_path: Path, monkeypatch) -> None:
    unsupported = tmp_path / "documento.pdf"
    unsupported.write_bytes(b"")
    captured: list[str] = []
    monkeypatch.setattr(
        "musetop.ui.main_window.QMessageBox.warning",
        lambda parent, title, message: captured.append(message),
    )
    window.load_paths([unsupported])
    assert window.playlist_model.rowCount() == 0
    assert captured and "MP3, FLAC, WAV, OGG, OPUS, M4A y AAC" in captured[0]


def test_empty_folder_shows_message(window: MainWindow, tmp_path: Path, monkeypatch) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    captured: list[str] = []
    monkeypatch.setattr(
        "musetop.ui.main_window.QMessageBox.warning",
        lambda parent, title, message: captured.append(message),
    )
    window.load_paths([empty])
    assert captured and "no contiene archivos de audio compatibles" in captured[0]


def test_duplicate_load_is_ignored(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["a.mp3", "b.ogg"])
    window.load_paths(files)
    window.load_paths(files)
    assert window.playlist_model.rowCount() == 2


def test_double_click_plays_selected_row(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["a.mp3", "b.flac", "c.opus"])
    window.load_paths(files)
    index = window.playlist_model.index(1, 0)
    window.playlist_view.doubleClicked.emit(index)
    assert window.engine.last_play_index == 1
    assert window.engine.paths == files
    assert window.player_bar.title_label.text() == "b"


def test_remove_selected_multiple_rows(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["a.mp3", "b.flac", "c.opus", "d.ogg"])
    window.load_paths(files)
    selection = window.playlist_view.selectionModel()
    flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
    selection.select(window.playlist_model.index(0, 0), flags)
    selection.select(window.playlist_model.index(2, 0), flags)
    window.remove_selected()
    assert window.playlist_model.rowCount() == 2
    assert [track.title for track in window.playlist_model.playlist] == ["b", "d"]
    assert len(window.engine.paths) == 2


def test_reorder_syncs_engine(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["a.mp3", "b.flac", "c.opus"])
    window.load_paths(files)
    assert window.playlist_model.move_tracks([0], 3) is True
    window.playlist_view.reordered.emit()
    assert [path.name for path in window.engine.paths] == ["b.flac", "c.opus", "a.mp3"]


def test_repeat_toggle_updates_mode(window: MainWindow) -> None:
    window.player_bar.repeat_button.setChecked(True)
    assert window.engine.mode.value == "repeat_all"
    window.player_bar.repeat_button.setChecked(False)
    assert window.engine.mode.value == "sequential"


def test_volume_slider_updates_engine(window: MainWindow) -> None:
    window.player_bar.volume_slider.setValue(37)
    assert window.engine.volume == 37


def test_seek_slider_emits_seconds(window: MainWindow) -> None:
    window.player_bar.set_duration(100.0)
    window.player_bar.progress_slider.setValue(500)
    window.player_bar.progress_slider.sliderReleased.emit()
    assert window.engine.last_seek == pytest.approx(50.0, abs=0.1)


def test_play_with_empty_playlist_reports_status(window: MainWindow) -> None:
    window._on_play_pause()
    assert "vacia" in window.statusBar().currentMessage()


def test_stop_resets_progress(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["a.mp3"])
    window.load_paths(files)
    window.engine.position = 10.0
    window.player_bar.current_time.setText("0:10")
    window._on_stop()
    assert window.player_bar.current_time.text() == "0:00"


def test_tree_drop_slot_accepts_paths(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["dropped.mp3"])
    window.playlist_view.files_dropped.emit(files)
    assert window.playlist_model.rowCount() == 1


def test_500_file_ui_load_under_five_seconds(window: MainWindow, tmp_path: Path) -> None:
    import time

    folder = tmp_path / "many"
    folder.mkdir()
    for index in range(500):
        (folder / f"track_{index:03d}.mp3").write_bytes(b"")
    started = time.perf_counter()
    window.load_paths([folder])
    elapsed = time.perf_counter() - started
    assert window.playlist_model.rowCount() == 500
    assert elapsed < 5.0


def test_track_changed_updates_info(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["artist_song.mp3"])
    window.load_paths(files)
    window.playlist_view.doubleClicked.emit(window.playlist_model.index(0, 0))
    assert window.player_bar.title_label.text() == "artist_song"
    assert "Artista desconocido" in window.player_bar.subtitle_label.text()


def test_close_does_not_shutdown_injected_engine(qtbot, tmp_path: Path) -> None:
    engine = FakeEngine()
    window = MainWindow(ConfigManager(tmp_path / "settings.json"), engine)
    qtbot.addWidget(window)
    window.close()
    assert "shutdown" not in engine.calls


def test_remove_action_enabled_with_selection(window: MainWindow, tmp_path: Path) -> None:
    files = make_files(tmp_path / "music", ["a.mp3"])
    window.load_paths(files)
    assert not window.remove_action.isEnabled()
    window.playlist_view.selectRow(0)
    assert window.remove_action.isEnabled()
    window.remove_selected()
    assert not window.remove_action.isEnabled()
