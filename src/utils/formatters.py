"""
PyRestForge - Data Formatters and Size/Latency Converters
"""

import json
import xml.dom.minidom
from typing import Any, Optional


def format_size(bytes_count: int) -> str:
    """Format bytes count into human readable units (B, KB, MB, GB)."""
    if bytes_count < 0:
        return "0 B"
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def format_latency(ms: float) -> str:
    """Format millisecond duration into ms or seconds."""
    if ms < 0:
        return "0 ms"
    if ms < 1000:
        return f"{int(ms)} ms" if ms.is_integer() else f"{ms:.1f} ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f} s"
    else:
        minutes = int(ms // 60000)
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"


def pretty_print_json(raw_text: str, indent: int = 2) -> str:
    """Prettify JSON string with indentation."""
    try:
        parsed = json.loads(raw_text)
        return json.dumps(parsed, indent=indent, ensure_ascii=False)
    except Exception:
        return raw_text


def minify_json(raw_text: str) -> str:
    """Minify JSON string removing all whitespace."""
    try:
        parsed = json.loads(raw_text)
        return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
    except Exception:
        return raw_text


def pretty_print_xml(raw_text: str, indent: str = "  ") -> str:
    """Prettify XML string with indentation."""
    try:
        dom = xml.dom.minidom.parseString(raw_text)
        return dom.toprettyxml(indent=indent)
    except Exception:
        return raw_text


def get_status_category(status_code: int) -> str:
    """Returns CSS/Theme category token for HTTP status code (2xx, 3xx, 4xx, 5xx)."""
    if 200 <= status_code < 300:
        return "status-2xx"
    elif 300 <= status_code < 400:
        return "status-3xx"
    elif 400 <= status_code < 500:
        return "status-4xx"
    elif status_code >= 500:
        return "status-5xx"
    return "status-unknown"
