"""
PyRestForge - General Helper Functions & Platform Utilities
"""

import os
import sys
import platform
import uuid
from pathlib import Path
from typing import Dict, Any


def get_app_data_dir() -> Path:
    """Returns local storage directory ~/.pyrestforge."""
    home = Path.home()
    app_dir = home / ".pyrestforge"
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "workspaces").mkdir(parents=True, exist_ok=True)
    (app_dir / "logs").mkdir(parents=True, exist_ok=True)
    (app_dir / "cookies").mkdir(parents=True, exist_ok=True)
    return app_dir


def generate_id(prefix: str = "item") -> str:
    """Generates unique prefixed ID string."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_macos() -> bool:
    return platform.system().lower() == "darwin"


def is_linux() -> bool:
    return platform.system().lower() == "linux"
