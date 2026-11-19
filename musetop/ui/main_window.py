"""Main application window and file loading orchestration."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QSize, Qt
from PySide6.QtGui import QAction, QCloseEvent, QColor, QDragEnterEvent, QDropEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from musetop.app.config import AppConfig, ConfigManager
from musetop.core.audio_engine import AudioEngine, PlaybackMode
from musetop.core.formats import FILE_DIALOG_FILTER, ScanResult, scan_paths
from musetop.core.tags_reader import read_track
from musetop.ui.icons.svg_icons import clear_icon_cache, render_icon
from musetop.ui.theme.colors import THEME_DARK, THEME_LIGHT, THEME_SYSTEM, ThemePalette
from musetop.ui.theme.manager import ThemeManager
from musetop.ui.widgets.player_bar import PlayerBar
from musetop.ui.widgets.playlist_model import PlaylistTableModel
from musetop.ui.widgets.playlist_view import PlaylistView

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Musetop main window. Playback decisions are delegated to the engine."""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        engine: AudioEngine | None = None,
        parent: QWidget | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__(parent)
        self._config_manager = config_manager or ConfigManager()
        self.theme_manager = theme_manager or ThemeManager(self._config_manager)
        self._config: AppConfig = self.theme_manager.config
        self.theme_manager.apply_current()
        self._owns_engine = engine is None
        self.engine: AudioEngine = engine if engine is not None else AudioEngine(parent=self)
        self._last_directory = Path.home()

        self.setWindowTitle("Musetop")
        self.setMinimumSize(860, 560)
        self.resize(1040, 680)
        self.setAcceptDrops(True)

        self._build_ui()
        self.theme_manager.palette_changed.connect(self._on_palette_changed)
        self._connect_engine()
        self._on_palette_changed(self.theme_manager.palette)
        self._update_track_count()
        self._update_actions()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.playlist_model = PlaylistTableModel(parent=self)
        self.playlist_view = PlaylistView(self)
        self.playlist_view.setModel(self.playlist_model)
        self.playlist_view.doubleClicked.connect(self._on_double_clicked)
        self.playlist_view.files_dropped.connect(self.load_paths)
        self.playlist_view.delete_requested.connect(self.remove_selected)
        self.playlist_view.reordered.connect(self._on_reordered)
        self.playlist_view.selectionModel().selectionChanged.connect(self._update_actions)

        self.player_bar = PlayerBar(self)
        self.player_bar.play_pause_requested.connect(self._on_play_pause)
        self.player_bar.stop_requested.connect(self._on_stop)
        self.player_bar.next_requested.connect(self._on_next)
        self.player_bar.previous_requested.connect(self._on_previous)
        self.player_bar.seek_requested.connect(self._on_seek)
        self.player_bar.volume_changed.connect(self._on_volume)
        self.player_bar.repeat_toggled.connect(self._on_repeat_toggled)

        central = QWidget(self)
        central.setObjectName("centralWidget")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 10, 16, 0)
        layout.setSpacing(8)
        layout.addWidget(self.playlist_view, 1)
        layout.addWidget(self.player_bar)
        self.setCentralWidget(central)

        self._build_toolbar()
        self.track_count_label = QLabel()
        self.track_count_label.setObjectName("trackCountLabel")
        self.statusBar().addPermanentWidget(self.track_count_label)
        self.statusBar().showMessage("Listo")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Principal", self)
        toolbar.setObjectName("mainToolBar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        self._toolbar = toolbar

        self.open_files_action = QAction("Abrir archivos", self)
        self.open_files_action.setToolTip("Abrir uno o varios archivos de audio")
        self.open_files_action.setShortcut("Ctrl+O")
        self.open_files_action.triggered.connect(self.open_files_dialog)
        toolbar.addAction(self.open_files_action)

        self.open_folder_action = QAction("Abrir carpeta", self)
        self.open_folder_action.setToolTip("Cargar los archivos de audio de una carpeta")
        self.open_folder_action.setShortcut("Ctrl+Shift+O")
        self.open_folder_action.triggered.connect(self.open_folder_dialog)
        toolbar.addAction(self.open_folder_action)

        toolbar.addSeparator()

        self.remove_action = QAction("Quitar", self)
        self.remove_action.setToolTip("Quitar las pistas seleccionadas")
        self.remove_action.triggered.connect(self.remove_selected)
        toolbar.addAction(self.remove_action)

        toolbar.addSeparator()
        theme_label = QLabel("Tema", self)
        theme_label.setObjectName("toolbarLabel")
        toolbar.addWidget(theme_label)
        self.theme_combo = QComboBox(self)
        self.theme_combo.setObjectName("themeCombo")
        self.theme_combo.addItem("Seguir al sistema", THEME_SYSTEM)
        self.theme_combo.addItem("Claro", THEME_LIGHT)
        self.theme_combo.addItem("Oscuro", THEME_DARK)
        index = self.theme_combo.findData(self._config.theme)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.setToolTip("Elegir el tema de la interfaz")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        toolbar.addWidget(self.theme_combo)

        self.accent_button = QPushButton("Acento", self)
        self.accent_button.setObjectName("accentButton")
        self.accent_button.setToolTip("Elegir el color de acento")
        self.accent_button.setIconSize(QSize(16, 16))
        self.accent_button.clicked.connect(self._choose_accent)
        toolbar.addWidget(self.accent_button)

        self.reset_appearance_action = QAction("Restablecer", self)
        self.reset_appearance_action.setToolTip("Restablecer las preferencias visuales")
        self.reset_appearance_action.triggered.connect(self._reset_appearance)
        toolbar.addAction(self.reset_appearance_action)

    def _connect_engine(self) -> None:
        self.engine.state_changed.connect(self._on_state_changed)
        self.engine.position_changed.connect(self.player_bar.set_position)
        self.engine.duration_changed.connect(self.player_bar.set_duration)
        self.engine.track_changed.connect(self._on_track_changed)
        self.engine.volume_changed.connect(self.player_bar.set_volume)
        self.engine.error_occurred.connect(self._on_engine_error)
        self.engine.playback_finished.connect(self._on_playback_finished)
        self.player_bar.set_volume(self.engine.volume)
        mode = getattr(self.engine.mode, "value", self.engine.mode)
        self.player_bar.set_repeat_checked(mode == PlaybackMode.REPEAT_ALL.value)
        self.player_bar.set_state(getattr(self.engine.state, "value", self.engine.state))

    def _on_palette_changed(self, palette: ThemePalette) -> None:
        self._config = self.theme_manager.config
        clear_icon_cache()
        self._apply_icon_colors(palette)
        with QSignalBlocker(self.theme_combo):
            index = self.theme_combo.findData(self._config.theme)
            self.theme_combo.setCurrentIndex(max(0, index))

    def _apply_icon_colors(self, palette: ThemePalette) -> None:
        self.open_files_action.setIcon(render_icon("file_plus", palette.text))
        self.open_folder_action.setIcon(render_icon("folder", palette.text))
        self.remove_action.setIcon(render_icon("trash", palette.text))
        self.reset_appearance_action.setIcon(render_icon("reset", palette.text))
        self.setWindowIcon(render_icon("app", palette.accent, 64))
        self.player_bar.refresh_icons(palette.text, palette.accent, palette.on_accent)
        self._update_accent_swatch(palette)

    def _update_accent_swatch(self, palette: ThemePalette) -> None:
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(palette.accent))
        self.accent_button.setIcon(QIcon(pixmap))

    def _on_theme_selected(self, _index: int) -> None:
        theme = self.theme_combo.currentData()
        if isinstance(theme, str):
            self.theme_manager.set_theme(theme)

    def _choose_accent(self) -> None:
        chosen = QColorDialog.getColor(
            QColor(self.theme_manager.palette.accent),
            self,
            "Color de acento",
        )
        if chosen.isValid():
            self.theme_manager.set_accent(chosen.name())

    def _reset_appearance(self) -> None:
        self.theme_manager.reset()
        self.statusBar().showMessage("Apariencia restablecida.", 4000)

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------
    def open_files_dialog(self) -> None:
        """Open the system file picker and append supported files."""

        selected, _ = QFileDialog.getOpenFileNames(
            self,
            "Abrir archivos de audio",
            str(self._last_directory),
            FILE_DIALOG_FILTER,
        )
        if selected:
            self._last_directory = Path(selected[0]).parent
            self.load_paths(selected)

    def open_folder_dialog(self) -> None:
        """Open the system folder picker and append direct audio files."""

        selected = QFileDialog.getExistingDirectory(
            self,
            "Abrir carpeta",
            str(self._last_directory),
        )
        if selected:
            self._last_directory = Path(selected)
            self.load_paths([selected])

    def load_paths(self, inputs: Sequence[str | Path]) -> None:
        """Scan and append supported files, reporting rejected items clearly."""

        if not inputs:
            return
        result = scan_paths(inputs)
        tracks = [read_track(path) for path in result.files]
        added = self.playlist_model.add_tracks(tracks)
        if added:
            self._sync_engine()
            self.statusBar().showMessage(f"Se agregaron {added} pistas a la lista.", 5000)
            logger.info("Added %s tracks from %s input paths", added, len(inputs))
            self._update_track_count()
        self._report_scan_problems(result)
        self._update_actions()

    def _report_scan_problems(self, result: ScanResult) -> None:
        messages: list[str] = []
        if result.rejected:
            names = self._summarize_paths(result.rejected)
            messages.append(
                "Formatos no compatibles:\n"
                f"{names}\n\n"
                "Formatos admitidos: MP3, FLAC, WAV, OGG, OPUS, M4A y AAC."
            )
        if result.empty_folders:
            names = self._summarize_paths(result.empty_folders)
            messages.append(f"La carpeta no contiene archivos de audio compatibles:\n{names}")
        if result.missing:
            names = self._summarize_paths(result.missing)
            messages.append(f"No se encontró la ruta:\n{names}")
        if not messages:
            return
        QMessageBox.warning(self, "No se pudieron cargar algunos elementos", "\n\n".join(messages))

    @staticmethod
    def _summarize_paths(items: Sequence[Path], limit: int = 8) -> str:
        names = [item.name or str(item) for item in items[:limit]]
        if len(items) > limit:
            names.append(f"y {len(items) - limit} mas")
        return "\n".join(names)

    # ------------------------------------------------------------------
    # Playlist operations
    # ------------------------------------------------------------------
    def remove_selected(self) -> None:
        """Remove selected rows from the playlist."""

        selection = self.playlist_view.selectionModel()
        if selection is None:
            return
        rows = sorted({index.row() for index in selection.selectedRows()})
        if not rows:
            return
        removed = self.playlist_model.remove_rows(rows)
        if removed:
            self._sync_engine()
            self._update_track_count()
            self.statusBar().showMessage(f"Se quitaron {len(removed)} pistas.", 5000)
            self._update_actions()

    def _sync_engine(self) -> None:
        self.engine.set_playlist(self.playlist_model.playlist.paths, preserve_current=True)

    def _on_double_clicked(self, index) -> None:
        if not index.isValid():
            return
        track = self.playlist_model.track_at(index.row())
        if track is None:
            return
        self.engine.set_playlist(self.playlist_model.playlist.paths, preserve_current=True)
        if not self.engine.play_index(index.row()):
            self.statusBar().showMessage("No se pudo iniciar la reproducción.", 5000)

    def _on_reordered(self) -> None:
        self._sync_engine()
        self.statusBar().showMessage("Lista reordenada.", 3000)

    # ------------------------------------------------------------------
    # Playback actions
    # ------------------------------------------------------------------
    def _on_play_pause(self) -> None:
        if len(self.playlist_model.playlist) == 0:
            self.statusBar().showMessage("La lista está vacía. Abre archivos o una carpeta.", 5000)
            return
        self.engine.toggle_pause()

    def _on_stop(self) -> None:
        self.engine.stop()
        self.player_bar.reset_progress()

    def _on_next(self) -> None:
        self.engine.next()

    def _on_previous(self) -> None:
        self.engine.previous()

    def _on_seek(self, seconds: float) -> None:
        self.engine.seek(seconds)

    def _on_volume(self, volume: int) -> None:
        self.engine.set_volume(volume)

    def _on_repeat_toggled(self, checked: bool) -> None:
        self.engine.set_mode(PlaybackMode.REPEAT_ALL if checked else PlaybackMode.SEQUENTIAL)

    # ------------------------------------------------------------------
    # Engine signals
    # ------------------------------------------------------------------
    def _on_state_changed(self, state: str) -> None:
        self.player_bar.set_state(state)

    def _on_track_changed(self, index: int) -> None:
        track = self.playlist_model.track_at(index)
        self.player_bar.set_track(track)
        if track is not None:
            self.player_bar.set_duration(track.duration)
        else:
            self.player_bar.reset_progress()
        self._update_track_count()

    def _on_engine_error(self, message: str) -> None:
        logger.error("Audio engine error: %s", message)
        self.statusBar().showMessage(message, 8000)
        QMessageBox.critical(self, "Error de reproducción", message)

    def _on_playback_finished(self) -> None:
        self.statusBar().showMessage("Reproducción finalizada.", 4000)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    def _update_actions(self) -> None:
        selection = self.playlist_view.selectionModel()
        has_selection = bool(selection and selection.selectedRows())
        self.remove_action.setEnabled(has_selection)

    def _update_track_count(self) -> None:
        count = len(self.playlist_model.playlist)
        self.track_count_label.setText(f"{count} pistas" if count != 1 else "1 pista")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                self.load_paths(paths)
                event.acceptProposedAction()
                return
        super().dropEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._owns_engine:
            self.engine.shutdown()
        event.accept()
