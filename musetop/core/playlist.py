"""Playlist domain model without Qt dependencies."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from musetop.core.tags_reader import TrackInfo


class Playlist:
    """Ordered collection of unique tracks identified by path."""

    def __init__(self, tracks: Iterable[TrackInfo] = ()) -> None:
        self._tracks: list[TrackInfo] = []
        self.add_tracks(tracks)

    def __len__(self) -> int:
        return len(self._tracks)

    def __iter__(self) -> Iterator[TrackInfo]:
        return iter(self._tracks)

    def __getitem__(self, index: int) -> TrackInfo:
        return self._tracks[index]

    @property
    def tracks(self) -> tuple[TrackInfo, ...]:
        """Return an immutable snapshot."""

        return tuple(self._tracks)

    @property
    def paths(self) -> tuple[Path, ...]:
        """Return the ordered paths for the audio engine."""

        return tuple(track.path for track in self._tracks)

    def index_of(self, path: str | Path) -> int:
        """Return the index for ``path`` or -1."""

        candidate = Path(path)
        for index, track in enumerate(self._tracks):
            if track.path == candidate:
                return index
        return -1

    def add_tracks(self, tracks: Iterable[TrackInfo]) -> int:
        """Append tracks whose path is not already present."""

        existing = {track.path for track in self._tracks}
        added = 0
        for track in tracks:
            if track.path in existing:
                continue
            self._tracks.append(track)
            existing.add(track.path)
            added += 1
        return added

    def remove_rows(self, rows: Iterable[int]) -> list[TrackInfo]:
        """Remove rows by index and return the removed tracks."""

        valid = sorted({row for row in rows if 0 <= row < len(self._tracks)}, reverse=True)
        removed: list[TrackInfo] = []
        for row in valid:
            removed.append(self._tracks.pop(row))
        removed.reverse()
        return removed

    def move_rows(self, rows: Sequence[int], destination: int) -> bool:
        """Move rows to ``destination`` using Qt-style before-row semantics."""

        valid_rows = sorted({row for row in rows if 0 <= row < len(self._tracks)})
        if not valid_rows:
            return False
        moving = [self._tracks[row] for row in valid_rows]
        row_set = set(valid_rows)
        remaining = [track for index, track in enumerate(self._tracks) if index not in row_set]
        adjusted = max(0, min(len(remaining), destination - sum(1 for row in valid_rows if row < destination)))
        reordered = remaining[:adjusted] + moving + remaining[adjusted:]
        if reordered == self._tracks:
            return False
        self._tracks = reordered
        return True

    def clear(self) -> None:
        """Remove every track."""

        self._tracks.clear()
