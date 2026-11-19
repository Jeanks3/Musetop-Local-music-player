"""Application entry point."""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from musetop import APP_NAME, __version__
from musetop.app.logging_setup import configure_logging
from musetop.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application with stable application metadata."""

    argv = list(sys.argv if arguments is None else arguments)
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("musetop")
    app.setStyle("Fusion")
    return app


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the desktop application and return the Qt exit code."""

    configure_logging()
    logger.info("Starting Musetop %s", __version__)
    app = create_application(arguments)
    window = MainWindow()
    window.show()
    exit_code = app.exec()
    logger.info("Musetop exited with code %s", exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
