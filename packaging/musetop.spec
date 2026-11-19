# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for Windows 10+ and Linux (onedir build)."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent
ICON_DIR = ROOT / "musetop" / "ui" / "icons"
RESOURCE_DIR = ROOT / "musetop" / "resources"
VENDOR_DIR = ROOT / "vendor" / "lib"

datas = [
    (str(RESOURCE_DIR / "musetop.png"), "resources"),
    (str(RESOURCE_DIR / "musetop.svg"), "resources"),
]
datas += [(str(path), "musetop/ui/icons") for path in sorted(ICON_DIR.glob("*.svg"))]

binaries = []
if sys.platform.startswith("win"):
    library_names = ("mpv-2.dll", "libmpv-2.dll", "mpv-1.dll")
    icon = str(ROOT / "packaging" / "musetop.ico")
elif sys.platform == "darwin":
    library_names = ("libmpv.dylib", "libmpv.2.dylib")
    icon = None
else:
    library_names = ("libmpv.so.2", "libmpv.so")
    icon = None

for library_name in library_names:
    candidate = VENDOR_DIR / library_name
    if candidate.exists():
        binaries.append((str(candidate), "vendor/lib"))
        break

hiddenimports = collect_submodules("mutagen")

a = Analysis(
    [str(ROOT / "musetop" / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="musetop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="musetop",
)
