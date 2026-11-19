"""Build the Musetop application directory with PyInstaller.

Usage:
    python packaging/build.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "packaging" / "musetop.spec"
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def main() -> int:
    """Run PyInstaller and copy Linux desktop metadata next to the binary."""

    if not (ROOT / "vendor" / "lib").is_dir():
        print("Warning: vendor/lib does not exist; the system must provide libmpv.")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD),
        str(SPEC),
    ]
    result = subprocess.run(command, cwd=str(ROOT))
    if result.returncode != 0:
        return result.returncode

    application_dir = DIST / "musetop"
    if not sys.platform.startswith("win"):
        desktop_source = ROOT / "packaging" / "musetop.desktop"
        if desktop_source.is_file() and application_dir.is_dir():
            shutil.copy2(desktop_source, application_dir / "musetop.desktop")
            icon_source = ROOT / "packaging" / "musetop.svg"
            if icon_source.is_file():
                shutil.copy2(icon_source, application_dir / "musetop.svg")
    print(f"Build completed: {application_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
