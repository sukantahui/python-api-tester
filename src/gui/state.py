"""
PyRestForge - Reactive Application State Controller (Qt Signals)
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal

from src.core.models.environment import WorkspaceEnvironments
from src.core.models.history import HistoryEntryModel
from src.core.models.request import RequestModel
from src.core.models.response import ResponseModel
from src.core.models.workspace import WorkspaceModel
from src.core.storage.config_store import ConfigStore, UserConfig
from src.core.storage.history_store import HistoryStore
from src.core.storage.workspace_store import WorkspaceStore
from src.utils.logger import logger


class AppState(QObject):
    """Global reactive state bus for PyRestForge."""

    workspace_loaded = Signal(WorkspaceModel)
    workspace_saved = Signal()
    active_request_changed = Signal(RequestModel)
    environment_changed = Signal(str)  # active_sub_env_id or name
    request_dispatched = Signal(RequestModel)
    response_received = Signal(ResponseModel)
    history_updated = Signal()
    status_message_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.workspace_store = WorkspaceStore()
        self.history_store = HistoryStore()
        self.config_store = ConfigStore()

        self.current_config: UserConfig = self.config_store.get_config()
        self.current_workspace: Optional[WorkspaceModel] = None
        self.current_request: Optional[RequestModel] = None
        self.active_sub_env_id: Optional[str] = None
        self.is_request_in_flight: bool = False

        self._initialize_initial_workspace()

    def _initialize_initial_workspace(self) -> None:
        """Loads workspace on startup from config or first available."""
        workspaces = self.workspace_store.list_workspaces()
        target_id = self.current_config.active_workspace_id
        
        if not target_id or not any(w["id"] == target_id for w in workspaces):
            target_id = workspaces[0]["id"] if workspaces else "ws_default"

        self.load_workspace(target_id)

    def load_workspace(self, workspace_id: str) -> None:
        """Switches the active workspace."""
        try:
            ws = self.workspace_store.load_workspace(workspace_id)
            self.current_workspace = ws
            self.active_sub_env_id = ws.environments.active_sub_env_id

            # Select first request in workspace or folder
            self.current_request = None
            if ws.requests:
                self.current_request = ws.requests[0]
            elif ws.folders and ws.folders[0].requests:
                self.current_request = ws.folders[0].requests[0]

            self.current_config.active_workspace_id = ws.id
            self.config_store.save(self.current_config)

            self.workspace_loaded.emit(ws)
            if self.current_request:
                self.active_request_changed.emit(self.current_request)

            self.status_message_updated.emit(f"Loaded workspace: {ws.name}")
        except Exception as e:
            logger.error(f"Failed to load workspace {workspace_id}: {e}")
            self.status_message_updated.emit(f"Error loading workspace: {e}")

    def save_current_workspace(self) -> None:
        """Persists active workspace to disk."""
        if self.current_workspace:
            try:
                self.current_workspace.environments.active_sub_env_id = self.active_sub_env_id
                self.workspace_store.save_workspace(self.current_workspace)
                self.workspace_saved.emit()
            except Exception as e:
                logger.error(f"Failed to save workspace: {e}")

    def select_request(self, request: RequestModel) -> None:
        """Sets active request."""
        self.current_request = request
        self.active_request_changed.emit(request)

    def set_active_environment(self, env_id_or_name: Optional[str]) -> None:
        """Sets active sub-environment."""
        self.active_sub_env_id = env_id_or_name
        if self.current_workspace:
            self.current_workspace.environments.active_sub_env_id = env_id_or_name
            self.save_current_workspace()
        self.environment_changed.emit(env_id_or_name or "")

    def record_history(self, response: ResponseModel) -> None:
        """Saves response run to history."""
        if not self.current_workspace or not self.current_request:
            return

        entry = HistoryEntryModel(
            workspace_id=self.current_workspace.id,
            request_id=self.current_request.id,
            request_name=self.current_request.name,
            method=self.current_request.method.value,
            url=self.current_request.url,
            status_code=response.status_code,
            duration_ms=response.timings.total_ms,
            response_size=response.raw_bytes_size,
            request_snapshot=self.current_request,
            response_snapshot=response
        )
        self.history_store.add_entry(entry)
        self.history_updated.emit()
