"""
PyRestForge - User Settings and Configuration Storage
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.utils.helpers import get_app_data_dir


class UserConfig(BaseModel):
    theme: str = "dark"
    active_workspace_id: Optional[str] = None
    default_timeout: float = 30.0
    follow_redirects: bool = True
    validate_ssl: bool = True
    proxy_url: Optional[str] = None
    font_size: int = 13
    editor_font_family: str = "JetBrains Mono, Consolas, Courier New, monospace"


class ConfigStore:
    """Manages application-wide user preferences in JSON."""

    def __init__(self):
        self.config_path = get_app_data_dir() / "config.json"
        self._config: UserConfig = self.load()

    def load(self) -> UserConfig:
        if self.config_path.exists():
            try:
                content = self.config_path.read_text(encoding="utf-8")
                return UserConfig.model_validate_json(content)
            except Exception:
                pass
        return UserConfig()

    def get_config(self) -> UserConfig:
        return self._config

    def save(self, config: Optional[UserConfig] = None) -> None:
        if config:
            self._config = config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(self._config.model_dump_json(indent=2), encoding="utf-8")
