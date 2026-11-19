"""Locate and import libmpv without relying on the system loader cache.

Development machines and packaged builds may ship libmpv next to the
application. When the library is not registered with the platform loader, this
module preloads it and provides a narrow ``find_library`` shim so ``python-mpv``
can use it. Importing this module never performs network access.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import logging
import os
import sys
import threading
from pathlib import Path
from types import ModuleType

from musetop.app import paths

logger = logging.getLogger(__name__)

_mpv_module: ModuleType | None = None
_load_error: str | None = None
_lock = threading.Lock()
_dll_directory_handle: object | None = None


def candidate_libraries() -> list[Path]:
    """Return existing libmpv candidates in priority order."""

    candidates: list[Path] = []
    override = os.environ.get("MUSETOP_LIBMPV")
    if override:
        candidates.append(Path(override).expanduser())

    vendor_dir = paths.vendor_lib_dir()
    if sys.platform.startswith("win"):
        candidates.extend(
            [
                vendor_dir / "mpv-2.dll",
                vendor_dir / "libmpv-2.dll",
                vendor_dir / "mpv-1.dll",
            ]
        )
    elif sys.platform == "darwin":
        candidates.extend([vendor_dir / "libmpv.dylib", vendor_dir / "libmpv.2.dylib"])
    else:
        candidates.extend([vendor_dir / "libmpv.so.2", vendor_dir / "libmpv.so"])

    discovered = ctypes.util.find_library("mpv")
    if discovered:
        candidates.append(Path(discovered))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen and candidate.exists():
            seen.add(key)
            unique.append(candidate)
    return unique


def _preload(library_path: Path) -> None:
    global _dll_directory_handle
    library_dir = library_path.parent
    if sys.platform.startswith("win"):
        if hasattr(os, "add_dll_directory"):
            _dll_directory_handle = os.add_dll_directory(str(library_dir))
        ctypes.CDLL(str(library_path))
        return
    ctypes.CDLL(str(library_path), mode=ctypes.RTLD_GLOBAL)


def load_mpv_module() -> ModuleType:
    """Import ``mpv``, preloading a locally bundled libmpv when necessary."""

    global _mpv_module, _load_error

    with _lock:
        if _mpv_module is not None:
            return _mpv_module

        try:
            import mpv as module

            _mpv_module = module
            return module
        except (ImportError, OSError) as first_error:
            _load_error = str(first_error)
            logger.debug("Standard libmpv lookup failed: %s", first_error)

        libraries = candidate_libraries()
        if not libraries:
            raise OSError(
                "No se encontró libmpv. Instala libmpv o coloca la biblioteca en vendor/lib."
            )

        library_path = libraries[0]
        try:
            _preload(library_path)
        except OSError as exc:
            raise OSError(
                f"No se pudo cargar libmpv desde {library_path}: {exc}"
            ) from exc

        original_find_library = ctypes.util.find_library

        def find_library(name: str) -> str | None:
            if name == "mpv":
                return str(library_path)
            return original_find_library(name)

        ctypes.util.find_library = find_library
        try:
            import mpv as module

            _mpv_module = module
            _load_error = None
            return module
        except (ImportError, OSError) as exc:
            _load_error = str(exc)
            raise OSError(f"No se pudo iniciar libmpv desde {library_path}: {exc}") from exc
        finally:
            ctypes.util.find_library = original_find_library


def mpv_load_error() -> str | None:
    """Return the last libmpv loading error, if any."""

    return _load_error


def reset_mpv_module_cache() -> None:
    """Clear the cached module; used by tests."""

    global _mpv_module, _load_error, _dll_directory_handle
    with _lock:
        _mpv_module = None
        _load_error = None
        if _dll_directory_handle is not None:
            close = getattr(_dll_directory_handle, "close", None)
            if callable(close):
                close()
            _dll_directory_handle = None
