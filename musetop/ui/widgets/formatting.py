"""Small formatting helpers shared by widgets."""

from __future__ import annotations

import math


def format_duration(seconds: float | int | None) -> str:
    """Format seconds as ``m:ss`` or ``h:mm:ss``."""

    if seconds is None:
        return "0:00"
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return "0:00"
    if not math.isfinite(value) or value < 0:
        value = 0.0
    total = int(round(value))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
