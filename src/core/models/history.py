"""
PyRestForge - Execution History Domain Models (Pydantic v2)
"""

import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field

from src.core.models.request import RequestModel
from src.core.models.response import ResponseModel


class HistoryEntryModel(BaseModel):
    id: str = Field(default_factory=lambda: f"hist_{uuid.uuid4().hex[:10]}")
    workspace_id: str
    request_id: str
    request_name: str
    method: str
    url: str
    status_code: int
    duration_ms: float
    response_size: int
    executed_at: float = Field(default_factory=time.time)
    request_snapshot: RequestModel
    response_snapshot: ResponseModel
