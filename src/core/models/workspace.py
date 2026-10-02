"""
PyRestForge - Workspace Domain Models (Pydantic v2)
"""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from src.core.models.environment import WorkspaceEnvironments
from src.core.models.folder import FolderModel
from src.core.models.request import RequestModel


class WorkspaceModel(BaseModel):
    id: str = Field(default_factory=lambda: f"ws_{uuid.uuid4().hex[:8]}")
    name: str = "My Workspace"
    description: Optional[str] = ""
    version: str = "1.0.0"
    environments: WorkspaceEnvironments = Field(default_factory=WorkspaceEnvironments)
    folders: List[FolderModel] = Field(default_factory=list)
    requests: List[RequestModel] = Field(default_factory=list)
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
