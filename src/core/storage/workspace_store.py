"""
PyRestForge - Local Workspace Storage & Persistence Manager
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from src.core.models.environment import EnvVariable, WorkspaceEnvironments
from src.core.models.folder import FolderModel
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel
from src.core.models.workspace import WorkspaceModel
from src.core.serializers.yaml_serializer import YamlSerializer
from src.core.serializers.json_serializer import JsonSerializer
from src.utils.helpers import get_app_data_dir
from src.utils.logger import logger


class WorkspaceStore:
    """Manages workspace persistence on local disk as YAML/JSON files."""

    def __init__(self):
        self.workspaces_dir = get_app_data_dir() / "workspaces"
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        self.yaml_serializer = YamlSerializer()
        self.json_serializer = JsonSerializer()

    def list_workspaces(self) -> List[Dict[str, str]]:
        """Returns list of all available workspaces with their IDs and names."""
        items: List[Dict[str, str]] = []
        yaml_files = list(self.workspaces_dir.glob("*.yaml")) + list(self.workspaces_dir.glob("*.yml"))
        
        for file in yaml_files:
            try:
                ws = self.yaml_serializer.load_from_file(file)
                items.append({
                    "id": ws.id,
                    "name": ws.name,
                    "path": str(file),
                    "format": "yaml"
                })
            except Exception as e:
                logger.debug(f"Error reading workspace file {file}: {e}")

        # If no workspaces found, create default workspace
        if not items:
            default_ws = self.create_default_workspace()
            items.append({
                "id": default_ws.id,
                "name": default_ws.name,
                "path": str(self.workspaces_dir / f"{default_ws.id}.yaml"),
                "format": "yaml"
            })

        return items

    def load_workspace(self, workspace_id: str) -> WorkspaceModel:
        """Loads workspace by ID from disk."""
        yaml_path = self.workspaces_dir / f"{workspace_id}.yaml"
        if yaml_path.exists():
            return self.yaml_serializer.load_from_file(yaml_path)

        json_path = self.workspaces_dir / f"{workspace_id}.json"
        if json_path.exists():
            return self.json_serializer.load_from_file(json_path)

        # Fallback to creating a new workspace
        ws = WorkspaceModel(id=workspace_id, name="Default Workspace")
        self.save_workspace(ws)
        return ws

    def save_workspace(self, workspace: WorkspaceModel) -> None:
        """Saves workspace to disk as YAML."""
        yaml_path = self.workspaces_dir / f"{workspace.id}.yaml"
        self.yaml_serializer.save_to_file(workspace, yaml_path)

    def delete_workspace(self, workspace_id: str) -> None:
        """Deletes workspace file from disk."""
        yaml_path = self.workspaces_dir / f"{workspace_id}.yaml"
        if yaml_path.exists():
            yaml_path.unlink()
        json_path = self.workspaces_dir / f"{workspace_id}.json"
        if json_path.exists():
            json_path.unlink()

    def create_default_workspace(self) -> WorkspaceModel:
        """Creates an initial starter workspace with realistic requests."""
        ws = WorkspaceModel(
            id="ws_default",
            name="Sample API Collection",
            description="Starter workspace demonstrating HTTP methods, variables, and assertions.",
            environments=WorkspaceEnvironments(
                base_variables=[
                    EnvVariable(key="baseUrl", value="https://httpbin.org", description="HTTPBin Echo Server")
                ]
            ),
            folders=[
                FolderModel(
                    name="HTTP Methods",
                    description="Standard REST operations",
                    requests=[
                        RequestModel(
                            name="Get Origin IP",
                            method=HttpMethod.GET,
                            url="{{baseUrl}}/ip",
                            headers=[HeaderItem(key="Accept", value="application/json", active=True)],
                            tests="def test_ip(res, env):\n    assert res.status_code == 200\n    assert 'origin' in res.json()\n"
                        ),
                        RequestModel(
                            name="Echo POST JSON",
                            method=HttpMethod.POST,
                            url="{{baseUrl}}/post",
                            headers=[HeaderItem(key="Content-Type", value="application/json", active=True)],
                            body=BodyConfig(
                                mode=BodyMode.JSON,
                                raw='{\n  "message": "Hello from PyRestForge!",\n  "timestamp": "{{$timestamp}}"\n}'
                            ),
                            tests="def test_echo(res, env):\n    assert res.status_code == 200\n    assert res.json()['json']['message'] == 'Hello from PyRestForge!'\n"
                        )
                    ]
                )
            ]
        )
        self.save_workspace(ws)
        return ws
