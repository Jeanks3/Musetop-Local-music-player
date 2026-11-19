"""Read title, artist, album and duration with mutagen.

Tag support varies by container. Missing tags fall back to the filename stem
and clearly labeled Spanish placeholders, never to an exception.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile

logger = logging.getLogger(__name__)

UNKNOWN_ARTIST = "Artista desconocido"
UNKNOWN_ALBUM = "Álbum desconocido"

_TEXT_KEYS: dict[str, tuple[str, ...]] = {
    "title": ("title", "TIT2", "\xa9nam"),
    "artist": ("artist", "TPE1", "\xa9ART"),
    "album": ("album", "TALB", "\xa9alb"),
}


@dataclass(frozen=True, slots=True)
class TrackInfo:
    """Display metadata for one audio file."""

    path: Path
    title: str
    artist: str
    album: str
    duration: float

    @classmethod
    def from_path(cls, path: str | Path) -> "TrackInfo":
        """Read metadata from ``path``."""

        return read_track(path)


def _text_from_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return _text_from_value(value[0]) if value else ""
    text = str(value).strip()
    return text


def _extract(tags: Any, keys: tuple[str, ...]) -> str:
    if tags is None:
        return ""
    for key in keys:
        try:
            value = tags.get(key)
        except (AttributeError, KeyError, TypeError):
            continue
        if value is None:
            continue
        text = _text_from_value(value)
        if text:
            return text
    return ""


def read_track(path: str | Path) -> TrackInfo:
    """Return best-effort metadata for a local audio file."""

    file_path = Path(path)
    title = file_path.stem
    artist = UNKNOWN_ARTIST
    album = UNKNOWN_ALBUM
    duration = 0.0

    try:
        audio = MutagenFile(str(file_path), easy=True)
    except Exception as exc:  # mutagen raises several format-specific errors
        logger.warning("Could not read tags from %s: %s", file_path, exc)
        return TrackInfo(file_path, title, artist, album, duration)

    if audio is None:
        return TrackInfo(file_path, title, artist, album, duration)

    info = getattr(audio, "info", None)
    length = getattr(info, "length", 0.0)
    try:
        duration = max(0.0, float(length))
    except (TypeError, ValueError):
        duration = 0.0

    tags = getattr(audio, "tags", None)
    read_title = _extract(tags, _TEXT_KEYS["title"])
    read_artist = _extract(tags, _TEXT_KEYS["artist"])
    read_album = _extract(tags, _TEXT_KEYS["album"])

    if not (read_title or read_artist or read_album):
        try:
            raw_audio = MutagenFile(str(file_path), easy=False)
        except Exception as exc:
            logger.debug("Could not read raw tags from %s: %s", file_path, exc)
            raw_audio = None
        if raw_audio is not None:
            raw_tags = getattr(raw_audio, "tags", None)
            read_title = read_title or _extract(raw_tags, _TEXT_KEYS["title"])
            read_artist = read_artist or _extract(raw_tags, _TEXT_KEYS["artist"])
            read_album = read_album or _extract(raw_tags, _TEXT_KEYS["album"])

    return TrackInfo(
        path=file_path,
        title=read_title or title,
        artist=read_artist or artist,
        album=read_album or album,
        duration=duration,
    )
