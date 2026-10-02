"""
PyRestForge - JSON Serialization & Deserialization Engine (orjson / stdlib)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
import orjson

from src.core.models.workspace import WorkspaceModel
from src.utils.logger import logger


class JsonSerializer:
    """High-performance JSON serializer using orjson."""

    @staticmethod
    def serialize_workspace(workspace: WorkspaceModel, pretty: bool = True, strip_secrets: bool = False) -> str:
        """Serializes a WorkspaceModel into a structured JSON string."""
        data = workspace.model_dump(mode="json", exclude_none=True)

        if strip_secrets:
            if "environments" in data:
                envs = data["environments"]
                if "base_variables" in envs:
                    for var in envs["base_variables"]:
                        if var.get("is_secret"):
                            var["value"] = "{{SECRET_MASKED}}"
                if "sub_environments" in envs:
                    for sub in envs["sub_environments"]:
                        for var in sub.get("variables", []):
                            if var.get("is_secret"):
                                var["value"] = "{{SECRET_MASKED}}"

        payload = {
            "schema_version": "1.0.0",
            "workspace": data
        }

        option = orjson.OPT_INDENT_2 if pretty else 0
        return orjson.dumps(payload, option=option).decode("utf-8")

    @staticmethod
    def deserialize_workspace(json_content: str) -> WorkspaceModel:
        """Parses a JSON string into a valid WorkspaceModel."""
        parsed = orjson.loads(json_content)
        if not isinstance(parsed, dict):
            raise ValueError("Invalid JSON collection: Root must be a dictionary object.")

        if "workspace" in parsed:
            ws_data = parsed["workspace"]
        else:
            ws_data = parsed

        return WorkspaceModel.model_validate(ws_data)

    @classmethod
    def save_to_file(cls, workspace: WorkspaceModel, file_path: Union[str, Path], pretty: bool = True, strip_secrets: bool = False) -> None:
        """Writes workspace JSON to file."""
        content = cls.serialize_workspace(workspace, pretty=pretty, strip_secrets=strip_secrets)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> WorkspaceModel:
        """Reads workspace JSON from file."""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        return cls.deserialize_workspace(content)
