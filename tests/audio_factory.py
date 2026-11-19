"""Generate real audio fixtures with ffmpeg for integration tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Container extension -> ffmpeg encoder arguments.
ENCODERS: dict[str, list[str]] = {
    ".mp3": ["-c:a", "libmp3lame", "-b:a", "128k"],
    ".flac": ["-c:a", "flac"],
    ".wav": ["-c:a", "pcm_s16le"],
    ".ogg": ["-c:a", "libvorbis", "-q:a", "4"],
    ".opus": ["-c:a", "libopus", "-b:a", "96k"],
    ".m4a": ["-c:a", "aac", "-b:a", "128k"],
    ".aac": ["-c:a", "aac", "-b:a", "128k", "-f", "adts"],
}

SUPPORTED_TEST_FORMATS = (".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a")


def ffmpeg_available() -> bool:
    """Return whether ffmpeg can be executed."""

    return shutil.which("ffmpeg") is not None


def generate_audio(
    path: Path,
    *,
    duration: float = 3.0,
    frequency: int = 440,
    tags: dict[str, str] | None = None,
) -> Path:
    """Create a sine-wave audio file at ``path`` using ffmpeg."""

    if not ffmpeg_available():
        raise RuntimeError("ffmpeg is required to generate audio fixtures")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoder = ENCODERS[path.suffix.lower()]
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency}:duration={duration}:sample_rate=44100",
        *encoder,
    ]
    for key, value in (tags or {}).items():
        command.extend(["-metadata", f"{key}={value}"])
    command.append(str(path))
    subprocess.run(command, check=True, capture_output=True)
    return path
