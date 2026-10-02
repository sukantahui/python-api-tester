"""
PyRestForge - Main Application Entry Point
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.gui.app import MainWindow
from src.utils.logger import logger


def main() -> int:
    """Initializes and runs the PyRestForge application."""
    logger.info("Starting PyRestForge Desktop Application...")

    # Enable High DPI Scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("PyRestForge")
    app.setOrganizationName("PyRestForge")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
