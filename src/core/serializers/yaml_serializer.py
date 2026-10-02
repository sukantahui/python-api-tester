"""
PyRestForge - YAML Serialization & Deserialization Engine (ruamel.yaml)
"""

import io
from pathlib import Path
from typing import Any, Dict, Optional, Union
from ruamel.yaml import YAML

from src.core.models.workspace import WorkspaceModel
from src.utils.logger import logger


class YamlSerializer:
    """High-fidelity YAML serializer/deserializer preserving comments and dictionary ordering."""

    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def serialize_workspace(self, workspace: WorkspaceModel, strip_secrets: bool = False) -> str:
        """Serializes a WorkspaceModel into a structured YAML string."""
        data = workspace.model_dump(mode="json", exclude_none=True)

        if strip_secrets:
            # Mask or remove secrets in base and sub-environments
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

        stream = io.StringIO()
        self.yaml.dump(payload, stream)
        return stream.getvalue()

    def deserialize_workspace(self, yaml_content: str) -> WorkspaceModel:
        """Parses a YAML string into a valid WorkspaceModel."""
        parsed = self.yaml.load(yaml_content)
        if not isinstance(parsed, dict):
            raise ValueError("Invalid YAML collection format: Root must be a mapping dictionary.")

        if "workspace" in parsed:
            ws_data = parsed["workspace"]
        else:
            ws_data = parsed

        return WorkspaceModel.model_validate(ws_data)

    def save_to_file(self, workspace: WorkspaceModel, file_path: Union[str, Path], strip_secrets: bool = False) -> None:
        """Writes workspace YAML to a file."""
        content = self.serialize_workspace(workspace, strip_secrets=strip_secrets)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def load_from_file(self, file_path: Union[str, Path]) -> WorkspaceModel:
        """Reads workspace YAML from a file."""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        return self.deserialize_workspace(content)
