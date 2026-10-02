"""
PyRestForge - HTTP Request Domain Models (Pydantic v2)
"""

import uuid
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.models.auth import AuthConfig


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class KeyValueItem(BaseModel):
    id: str = Field(default_factory=lambda: f"kv_{uuid.uuid4().hex[:8]}")
    key: str = ""
    value: str = ""
    description: Optional[str] = ""
    active: bool = True


class ParamItem(KeyValueItem):
    pass


class HeaderItem(KeyValueItem):
    pass


class FormDataItem(KeyValueItem):
    is_file: bool = False
    file_path: Optional[str] = None
    content_type: Optional[str] = None


class BodyMode(str, Enum):
    NONE = "none"
    JSON = "json"
    FORM_DATA = "form_data"
    URLENCODED = "urlencoded"
    RAW = "raw"
    GRAPHQL = "graphql"
    BINARY = "binary"


class RawSyntax(str, Enum):
    TEXT = "text"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    JAVASCRIPT = "javascript"


class GraphQLConfig(BaseModel):
    query: str = ""
    variables: str = "{}"


class BodyConfig(BaseModel):
    mode: BodyMode = Field(default=BodyMode.NONE)
    raw: Optional[str] = ""
    raw_syntax: RawSyntax = Field(default=RawSyntax.JSON)
    form_data: List[FormDataItem] = Field(default_factory=list)
    urlencoded: List[KeyValueItem] = Field(default_factory=list)
    graphql: GraphQLConfig = Field(default_factory=GraphQLConfig)
    binary_file_path: Optional[str] = None


class RequestModel(BaseModel):
    id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    parent_id: Optional[str] = None
    name: str = "New Request"
    method: HttpMethod = Field(default=HttpMethod.GET)
    url: str = ""
    description: Optional[str] = ""
    params: List[ParamItem] = Field(default_factory=list)
    headers: List[HeaderItem] = Field(default_factory=list)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    body: BodyConfig = Field(default_factory=BodyConfig)
    pre_request_script: Optional[str] = None
    tests: Optional[str] = None
    timeout: Optional[float] = 30.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    meta_sort_key: int = 0
