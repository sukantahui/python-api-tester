"""
PyRestForge - Environment and Variable Domain Models (Pydantic v2)
"""

import uuid
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class EnvVariable(BaseModel):
    id: str = Field(default_factory=lambda: f"var_{uuid.uuid4().hex[:8]}")
    key: str
    value: str
    enabled: bool = True
    is_secret: bool = False
    description: Optional[str] = ""


class SubEnvironmentModel(BaseModel):
    id: str = Field(default_factory=lambda: f"subenv_{uuid.uuid4().hex[:8]}")
    name: str = "New Environment"
    color: Optional[str] = "#7C3AED"
    variables: List[EnvVariable] = Field(default_factory=list)


class WorkspaceEnvironments(BaseModel):
    base_variables: List[EnvVariable] = Field(default_factory=list)
    sub_environments: List[SubEnvironmentModel] = Field(default_factory=list)
    active_sub_env_id: Optional[str] = None
