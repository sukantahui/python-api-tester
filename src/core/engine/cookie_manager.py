"""
PyRestForge - Cookie Jar Manager (RFC 6265 Compliant)
"""

import http.cookiejar
from pathlib import Path
from typing import Dict, List, Optional
import httpx

from src.core.models.response import CookieItem
from src.utils.helpers import get_app_data_dir


class PersistentCookieManager:
    """Manages workspace cookie jars, persistent storage, and serialization."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.cookie_file = get_app_data_dir() / "cookies" / f"{workspace_id}.cookies"
        self.jar = http.cookiejar.MozillaCookieJar(filename=str(self.cookie_file))
        self.load()

    def load(self) -> None:
        """Loads cookies from disk if exists."""
        if self.cookie_file.exists():
            try:
                self.jar.load(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass

    def save(self) -> None:
        """Saves cookies to disk."""
        try:
            self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
            self.jar.save(ignore_discard=True, ignore_expires=True)
        except Exception:
            pass

    def get_httpx_cookies(self) -> httpx.Cookies:
        """Converts internal cookie jar to httpx.Cookies."""
        cookies = httpx.Cookies()
        for cookie in self.jar:
            cookies.set(
                name=cookie.name,
                value=cookie.value,
                domain=cookie.domain,
                path=cookie.path
            )
        return cookies

    def update_from_response(self, response: httpx.Response) -> List[CookieItem]:
        """Extracts Set-Cookie headers from HTTP response and updates the cookie jar."""
        extracted: List[CookieItem] = []
        for name, value in response.cookies.items():
            cookie_item = CookieItem(
                name=name,
                value=value,
                domain=response.url.host,
                path="/",
                http_only=False,
                secure=response.url.scheme == "https"
            )
            extracted.append(cookie_item)

        self.save()
        return extracted

    def get_all_cookies(self) -> List[CookieItem]:
        """Returns all cookies as CookieItem models."""
        items: List[CookieItem] = []
        for c in self.jar:
            items.append(CookieItem(
                name=c.name,
                value=c.value,
                domain=c.domain,
                path=c.path,
                expires=str(c.expires) if c.expires else None,
                http_only=bool(c.has_nonstandard_attr('HttpOnly')),
                secure=c.secure
            ))
        return items

    def clear(self) -> None:
        """Clears all cookies in the jar."""
        self.jar.clear()
        if self.cookie_file.exists():
            try:
                self.cookie_file.unlink()
            except Exception:
                pass
