"""
PyRestForge - HTTP Response & Diagnostics Models (Pydantic v2)
"""

import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class NetworkTimingModel(BaseModel):
    dns_ms: float = 0.0
    tcp_ms: float = 0.0
    tls_ms: float = 0.0
    ttfb_ms: float = 0.0
    download_ms: float = 0.0
    total_ms: float = 0.0


class SslCertificateModel(BaseModel):
    subject: Optional[str] = None
    issuer: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    cipher: Optional[str] = None
    tls_version: Optional[str] = None


class CookieItem(BaseModel):
    name: str
    value: str
    domain: Optional[str] = None
    path: Optional[str] = "/"
    expires: Optional[str] = None
    http_only: bool = False
    secure: bool = False


class TestAssertionResult(BaseModel):
    name: str
    passed: bool
    error_message: Optional[str] = None
    duration_ms: float = 0.0


class ResponseModel(BaseModel):
    request_id: str
    status_code: int = 0
    status_text: str = ""
    http_version: str = "HTTP/1.1"
    headers: List[Dict[str, str]] = Field(default_factory=list)
    cookies: List[CookieItem] = Field(default_factory=list)
    body: str = ""
    raw_bytes_size: int = 0
    content_type: str = "text/plain"
    timings: NetworkTimingModel = Field(default_factory=NetworkTimingModel)
    certificate: Optional[SslCertificateModel] = None
    test_results: List[TestAssertionResult] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    error_message: Optional[str] = None
