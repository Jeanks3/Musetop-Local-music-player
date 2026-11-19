from __future__ import annotations

import logging
from pathlib import Path

from musetop.app.logging_setup import LOGGER_NAME, configure_logging


def test_logging_writes_to_rotating_file(tmp_path: Path) -> None:
    logger = configure_logging(logging.INFO, tmp_path / "logs")
    logger.info("Prueba de registro")
    for handler in logger.handlers:
        handler.flush()
    log_file = tmp_path / "logs" / "musetop.log"
    assert log_file.is_file()
    assert "Prueba de registro" in log_file.read_text(encoding="utf-8")


def test_logging_is_idempotent(tmp_path: Path) -> None:
    logger = configure_logging(logging.INFO, tmp_path / "logs")
    logger = configure_logging(logging.DEBUG, tmp_path / "logs")
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert logging.getLogger(LOGGER_NAME) is logger
