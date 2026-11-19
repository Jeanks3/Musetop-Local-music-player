"""Qt table model backed by the core :class:`Playlist`."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from PySide6.QtCore import QAbstractTableModel, QMimeData, QModelIndex, Qt

from musetop.core.playlist import Playlist
from musetop.core.tags_reader import TrackInfo
from musetop.ui.widgets.formatting import format_duration

ROW_MIME_TYPE = "application/x-musetop-rows"


class PlaylistTableModel(QAbstractTableModel):
    """Read-only table model with drag support for row reordering."""

    HEADERS = ("#", "Título", "Artista", "Álbum", "Duración")
    COLUMN_NUMBER = 0
    COLUMN_TITLE = 1
    COLUMN_ARTIST = 2
    COLUMN_ALBUM = 3
    COLUMN_DURATION = 4

    def __init__(self, playlist: Playlist | None = None, parent=None) -> None:
        super().__init__(parent)
        self._playlist = playlist if playlist is not None else Playlist()

    @property
    def playlist(self) -> Playlist:
        """Return the backing playlist."""

        return self._playlist

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._playlist)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = 0):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        if 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = 0):
        if not index.isValid() or not 0 <= index.row() < len(self._playlist):
            return None
        track = self._playlist[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_value(track, index.column())
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in {self.COLUMN_NUMBER, self.COLUMN_DURATION}:
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.UserRole:
            return track
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(track.path)
        return None

    def _display_value(self, track: TrackInfo, column: int) -> str:
        if column == self.COLUMN_NUMBER:
            return str(self._playlist.index_of(track.path) + 1)
        if column == self.COLUMN_TITLE:
            return track.title
        if column == self.COLUMN_ARTIST:
            return track.artist
        if column == self.COLUMN_ALBUM:
            return track.album
        if column == self.COLUMN_DURATION:
            return format_duration(track.duration)
        return ""

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.isValid():
            return base | Qt.ItemFlag.ItemIsDragEnabled
        return base | Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self) -> list[str]:  # noqa: N802
        return [ROW_MIME_TYPE]

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:  # noqa: N802
        rows = sorted({index.row() for index in indexes if index.isValid()})
        payload = QMimeData()
        payload.setData(ROW_MIME_TYPE, ",".join(str(row) for row in rows).encode("ascii"))
        return payload

    def supportedDropActions(self) -> Qt.DropAction:  # noqa: N802
        return Qt.DropAction.MoveAction

    def track_at(self, row: int) -> TrackInfo | None:
        """Return the track at ``row`` or None."""

        if 0 <= row < len(self._playlist):
            return self._playlist[row]
        return None

    def add_tracks(self, tracks: Iterable[TrackInfo]) -> int:
        """Append tracks and reset the model."""

        self.beginResetModel()
        added = self._playlist.add_tracks(tracks)
        self.endResetModel()
        return added

    def remove_rows(self, rows: Sequence[int]) -> list[TrackInfo]:
        """Remove rows and reset the model."""

        self.beginResetModel()
        removed = self._playlist.remove_rows(rows)
        self.endResetModel()
        return removed

    def move_tracks(self, rows: Sequence[int], destination: int) -> bool:
        """Move rows to ``destination`` and reset the model when changed."""

        self.beginResetModel()
        changed = self._playlist.move_rows(rows, destination)
        self.endResetModel()
        return changed

    def refresh(self) -> None:
        """Reset the model around external playlist mutation."""

        self.beginResetModel()
        self.endResetModel()
