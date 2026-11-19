"""Central logging setup. Application code must use ``logging``, never prints."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from musetop.app import paths

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
LOGGER_NAME = "musetop"
_HANDLER_MARKER = "_musetop_handler"


def configure_logging(
    level: int = logging.INFO,
    log_directory: Path | None = None,
) -> logging.Logger:
    """Configure the ``musetop`` logger and return it.

    The function is idempotent: existing Musetop handlers are replaced instead
    of duplicated. If the log directory cannot be created, a console handler is
    installed so the application still reports diagnostics.
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(LOG_FORMAT)
    directory = paths.ensure_directory(log_directory or paths.log_dir())
    try:
        file_handler = RotatingFileHandler(
            directory / "musetop.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
    except OSError as exc:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        setattr(console_handler, _HANDLER_MARKER, True)
        logger.addHandler(console_handler)
        logger.warning("Could not open the log file: %s", exc)
        return logger

    file_handler.setFormatter(formatter)
    setattr(file_handler, _HANDLER_MARKER, True)
    logger.addHandler(file_handler)
    return logger
