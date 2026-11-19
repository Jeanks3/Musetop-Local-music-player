"""Theme tokens, color math and WCAG contrast helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_SYSTEM = "system"

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def normalize_hex(color: str) -> str:
    """Validate and lowercase a ``#rrggbb`` color."""

    if not _HEX_COLOR.match(color):
        raise ValueError(f"Invalid color: {color}")
    return color.lower()


def _channels(color: str) -> tuple[int, int, int]:
    value = normalize_hex(color).lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _linear(channel: int) -> float:
    srgb = channel / 255.0
    if srgb <= 0.04045:
        return srgb / 12.92
    return ((srgb + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """Return WCAG relative luminance for an sRGB color."""

    red, green, blue = _channels(color)
    return 0.2126 * _linear(red) + 0.7152 * _linear(green) + 0.0722 * _linear(blue)


def contrast_ratio(first: str, second: str) -> float:
    """Return the WCAG 2.1 contrast ratio between two colors."""

    lighter = max(relative_luminance(first), relative_luminance(second))
    darker = min(relative_luminance(first), relative_luminance(second))
    return (lighter + 0.05) / (darker + 0.05)


def blend(first: str, second: str, amount: float) -> str:
    """Blend two colors; ``amount`` 0 returns first and 1 returns second."""

    ratio = max(0.0, min(1.0, amount))
    first_rgb = _channels(first)
    second_rgb = _channels(second)
    mixed = tuple(round(a + (b - a) * ratio) for a, b in zip(first_rgb, second_rgb))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def best_text_color(background: str) -> str:
    """Return black or white with the strongest contrast on ``background``."""

    black = contrast_ratio("#000000", background)
    white = contrast_ratio("#ffffff", background)
    return "#000000" if black >= white else "#ffffff"


def ensure_visible_accent(color: str, background: str, surface: str) -> str:
    """Make an accent visible against both window and surface colors."""

    color = normalize_hex(color)
    target = "#ffffff" if relative_luminance(background) < 0.5 else "#000000"
    for step in range(0, 21):
        candidate = color if step == 0 else blend(color, target, step * 0.05)
        if (
            contrast_ratio(candidate, background) >= 3.0
            and contrast_ratio(candidate, surface) >= 3.0
        ):
            return candidate
    return target


def _contrast_variant(
    accent: str,
    on_accent: str,
    background: str,
    surface: str,
    amount: float,
) -> str:
    """Shift a state color while preserving AA text contrast and visibility."""

    target = "#000000" if on_accent == "#ffffff" else "#ffffff"
    candidate = blend(accent, target, amount)
    if (
        contrast_ratio(on_accent, candidate) >= 4.5
        and contrast_ratio(candidate, background) >= 3.0
        and contrast_ratio(candidate, surface) >= 3.0
    ):
        return candidate
    return accent


@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Resolved colors used by QSS, icons and the Qt palette."""

    mode: str
    background: str
    surface: str
    surface_alt: str
    text: str
    text_muted: str
    border: str
    hover: str
    pressed: str
    disabled_text: str
    accent: str
    on_accent: str
    accent_hover: str
    accent_pressed: str
    shadow: str


_LIGHT_BASE = {
    "background": "#f5f7fb",
    "surface": "#ffffff",
    "surface_alt": "#eef3f9",
    "text": "#161c26",
    "text_muted": "#556172",
    "border": "#d2dae5",
    "hover": "#e7eef7",
    "pressed": "#dce5f1",
    "disabled_text": "#7b8796",
    "shadow": "#c7d1de",
}

_DARK_BASE = {
    "background": "#10141a",
    "surface": "#181e27",
    "surface_alt": "#1e2631",
    "text": "#eef2f7",
    "text_muted": "#a6b1c0",
    "border": "#2e3846",
    "hover": "#232b36",
    "pressed": "#2c3542",
    "disabled_text": "#74808f",
    "shadow": "#080b0f",
}


def build_palette(mode: str, accent_color: str) -> ThemePalette:
    """Build a contrast-checked palette for light or dark mode."""

    resolved = THEME_DARK if mode == THEME_DARK else THEME_LIGHT
    base = _DARK_BASE if resolved == THEME_DARK else _LIGHT_BASE
    accent = ensure_visible_accent(accent_color, base["background"], base["surface"])
    on_accent = best_text_color(accent)
    return ThemePalette(
        mode=resolved,
        background=base["background"],
        surface=base["surface"],
        surface_alt=base["surface_alt"],
        text=base["text"],
        text_muted=base["text_muted"],
        border=base["border"],
        hover=base["hover"],
        pressed=base["pressed"],
        disabled_text=base["disabled_text"],
        accent=accent,
        on_accent=on_accent,
        accent_hover=_contrast_variant(
            accent, on_accent, base["background"], base["surface"], 0.12
        ),
        accent_pressed=_contrast_variant(
            accent, on_accent, base["background"], base["surface"], 0.2
        ),
        shadow=base["shadow"],
    )
