"""Playlist table view with external file drops and internal row moves."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from musetop.ui.widgets.playlist_model import ROW_MIME_TYPE, PlaylistTableModel


class PlaylistView(QTableView):
    """Table with double-click playback, row reordering and file drops."""

    files_dropped = Signal(list)
    delete_requested = Signal()
    reordered = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("playlistView")
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self._configure_columns()

    def setModel(self, model) -> None:  # noqa: N802
        super().setModel(model)
        self._configure_columns()

    def _configure_columns(self) -> None:
        header = self.horizontalHeader()
        header.setHighlightSections(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(PlaylistTableModel.COLUMN_NUMBER, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(PlaylistTableModel.COLUMN_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(PlaylistTableModel.COLUMN_ARTIST, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(PlaylistTableModel.COLUMN_ALBUM, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(PlaylistTableModel.COLUMN_DURATION, QHeaderView.ResizeMode.ResizeToContents)

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() or event.mimeData().hasFormat(ROW_MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() or event.mimeData().hasFormat(ROW_MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        mime = event.mimeData()
        if mime.hasUrls():
            paths = [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
                event.acceptProposedAction()
                return
        if mime.hasFormat(ROW_MIME_TYPE):
            payload = bytes(mime.data(ROW_MIME_TYPE)).decode("ascii", errors="ignore")
            rows = [int(part) for part in payload.split(",") if part.strip().isdigit()]
            if not rows:
                rows = sorted({index.row() for index in self.selectedIndexes()})
            destination = self._drop_destination(event)
            model = self.model()
            if isinstance(model, PlaylistTableModel) and rows:
                if model.move_tracks(rows, destination):
                    self.reordered.emit()
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def _drop_destination(self, event: QDropEvent) -> int:
        index = self.indexAt(event.position().toPoint())
        if not index.isValid():
            model = self.model()
            return model.rowCount() if model is not None else 0
        destination = index.row()
        if self.dropIndicatorPosition() == QAbstractItemView.DropIndicatorPosition.BelowItem:
            destination += 1
        return destination

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in {Qt.Key.Key_Delete, Qt.Key.Key_Backspace}:
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)
