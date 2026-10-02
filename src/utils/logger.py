"""
PyRestForge - Structured Logging Utility
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_log_dir() -> Path:
    log_dir = Path.home() / ".pyrestforge" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name: str = "pyrestforge", log_file: Optional[str] = "app.log", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        try:
            log_path = get_log_dir() / log_file
            file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
            file_formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger


logger = setup_logger()
