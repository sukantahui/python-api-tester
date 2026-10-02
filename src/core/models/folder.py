"""
PyRestForge - Folder & Hierarchy Domain Models (Pydantic v2)
"""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from src.core.models.auth import AuthConfig
from src.core.models.request import RequestModel


class FolderModel(BaseModel):
    id: str = Field(default_factory=lambda: f"fld_{uuid.uuid4().hex[:8]}")
    parent_id: Optional[str] = None
    name: str = "New Folder"
    description: Optional[str] = ""
    auth: AuthConfig = Field(default_factory=AuthConfig)
    folders: List["FolderModel"] = Field(default_factory=list)
    requests: List[RequestModel] = Field(default_factory=list)
    meta_sort_key: int = 0


# Handle recursive self-referential Pydantic model
FolderModel.model_rebuild()
