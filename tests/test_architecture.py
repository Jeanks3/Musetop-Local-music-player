"""Architecture guard rails: offline-only code and emoji-free user interfaces."""

from __future__ import annotations

import ast
import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "musetop"

FORBIDDEN_NETWORK_MODULES = {
    "requests",
    "httpx",
    "urllib",
    "urllib2",
    "urllib3",
    "socket",
    "http",
    "ftplib",
    "smtplib",
    "telnetlib",
    "xmlrpc",
    "websockets",
    "aiohttp",
}

FORBIDDEN_QT_MODULES = {
    "QtNetwork",
    "QtWebEngineCore",
    "QtWebEngineWidgets",
    "QtWebSockets",
}

EMOJI_PATTERN = re.compile(
    "[" "\U0001F000-\U0001FAFF" "\u2600-\u27BF" "\u2B00-\u2BFF" "\uFE0F" "\u200D" "]"
)


def _python_files() -> list[Path]:
    return sorted(path for path in PACKAGE_ROOT.rglob("*.py") if "__pycache__" not in path.parts)


def _iter_imports(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_package_does_not_import_network_libraries() -> None:
    violations: list[str] = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module_name in _iter_imports(tree):
            root = module_name.split(".", maxsplit=1)[0]
            if root in FORBIDDEN_NETWORK_MODULES:
                violations.append(f"{path.name}: {module_name}")
            if module_name.startswith("PySide6.") and module_name.split(".", maxsplit=1)[1] in FORBIDDEN_QT_MODULES:
                violations.append(f"{path.name}: {module_name}")
    assert not violations, "Network imports are forbidden: " + ", ".join(violations)


def test_no_emoji_characters_in_package_sources() -> None:
    violations: list[str] = []
    for path in PACKAGE_ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".qss", ".svg", ".json", ".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if EMOJI_PATTERN.search(line):
                violations.append(f"{path.relative_to(PACKAGE_ROOT)}:{line_number}")
    assert not violations, "Emoji characters are forbidden in UI sources: " + ", ".join(violations)


def test_core_does_not_import_ui() -> None:
    violations: list[str] = []
    for path in (PACKAGE_ROOT / "core").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module_name in _iter_imports(tree):
            if module_name.startswith("musetop.ui"):
                violations.append(f"{path.name}: {module_name}")
    assert not violations, "Core must remain independent from the view: " + ", ".join(violations)
