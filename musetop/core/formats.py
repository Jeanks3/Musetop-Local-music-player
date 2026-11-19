"""Supported audio containers and filesystem scanning helpers."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac"}
)

FILE_DIALOG_FILTER = (
    "Archivos de audio (*.mp3 *.flac *.wav *.ogg *.opus *.m4a *.aac);;"
    "Todos los archivos (*)"
)


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Outcome of scanning user-provided files and folders."""

    files: tuple[Path, ...] = ()
    rejected: tuple[Path, ...] = ()
    empty_folders: tuple[Path, ...] = ()
    missing: tuple[Path, ...] = ()

    @property
    def is_empty(self) -> bool:
        """Whether no supported file was found."""

        return not self.files


def is_supported_file(path: str | Path) -> bool:
    """Return whether ``path`` exists and has a supported audio extension."""

    candidate = Path(path)
    return candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS


def _dedupe(paths: Iterable[Path]) -> tuple[Path, ...]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            resolved = path.resolve(strict=False)
        except OSError:
            resolved = path.absolute()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return tuple(unique)


def scan_paths(inputs: Iterable[str | Path]) -> ScanResult:
    """Collect supported files from explicit files and direct folder children.

    Folder scanning is intentionally non-recursive. Unsupported explicit files
    are reported, while unsupported files inside a folder are ignored.
    """

    found: list[Path] = []
    rejected: list[Path] = []
    empty_folders: list[Path] = []
    missing: list[Path] = []

    for raw in inputs:
        path = Path(raw).expanduser()
        if not path.exists():
            missing.append(path)
            continue
        if path.is_dir():
            try:
                children = sorted(
                    (child for child in path.iterdir() if child.is_file()),
                    key=lambda child: child.name.casefold(),
                )
            except OSError as exc:
                logger.warning("Could not list folder %s: %s", path, exc)
                missing.append(path)
                continue
            supported = [child for child in children if child.suffix.lower() in SUPPORTED_EXTENSIONS]
            if supported:
                found.extend(supported)
            else:
                empty_folders.append(path)
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(path)
        else:
            rejected.append(path)

    return ScanResult(
        files=_dedupe(found),
        rejected=tuple(rejected),
        empty_folders=tuple(empty_folders),
        missing=tuple(missing),
    )
