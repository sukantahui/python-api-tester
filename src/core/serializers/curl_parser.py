"""
PyRestForge - cURL Command Ingestion & Multi-Language Code Generator
"""

import json
import re
import shlex
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from src.core.models.auth import AuthConfig, AuthType
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel
from src.utils.logger import logger


class CurlParser:
    """Parses cURL commands into RequestModel objects."""

    @classmethod
    def parse_curl(cls, curl_command: str) -> RequestModel:
        """Converts a standard cURL terminal command into a RequestModel."""
        clean_cmd = curl_command.strip().replace("\\\n", " ").replace("\\\r\n", " ")
        try:
            tokens = shlex.split(clean_cmd)
        except Exception:
            tokens = clean_cmd.split()

        if tokens and tokens[0] == "curl":
            tokens = tokens[1:]

        method = HttpMethod.GET
        url = ""
        headers: List[HeaderItem] = []
        data_parts: List[str] = []
        auth_cfg = AuthConfig()

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ("-X", "--request") and i + 1 < len(tokens):
                m_str = tokens[i + 1].upper()
                if m_str in [m.value for m in HttpMethod]:
                    method = HttpMethod(m_str)
                i += 2
            elif tok in ("-H", "--header") and i + 1 < len(tokens):
                h_val = tokens[i + 1]
                if ":" in h_val:
                    k, v = h_val.split(":", 1)
                    headers.append(HeaderItem(key=k.strip(), value=v.strip(), active=True))
                i += 2
            elif tok in ("-d", "--data", "--data-raw", "--data-binary") and i + 1 < len(tokens):
                data_parts.append(tokens[i + 1])
                if method == HttpMethod.GET:
                    method = HttpMethod.POST
                i += 2
            elif tok in ("-u", "--user") and i + 1 < len(tokens):
                u_val = tokens[i + 1]
                if ":" in u_val:
                    u, p = u_val.split(":", 1)
                    auth_cfg.type = AuthType.BASIC
                    auth_cfg.basic_username = u
                    auth_cfg.basic_password = p
                i += 2
            elif not tok.startswith("-") and not url:
                url = tok
                i += 1
            else:
                i += 1

        body_cfg = BodyConfig()
        if data_parts:
            combined_data = "&".join(data_parts)
            # Detect JSON vs plain
            if (combined_data.startswith("{") and combined_data.endswith("}")) or any(h.key.lower() == "content-type" and "json" in h.value.lower() for h in headers):
                body_cfg.mode = BodyMode.JSON
                body_cfg.raw = combined_data
            else:
                body_cfg.mode = BodyMode.RAW
                body_cfg.raw = combined_data

        # Check Bearer in Authorization header
        for h in headers:
            if h.key.lower() == "authorization" and h.value.lower().startswith("bearer "):
                auth_cfg.type = AuthType.BEARER
                auth_cfg.bearer_token = h.value[7:].strip()

        return RequestModel(
            name="Imported cURL Request",
            method=method,
            url=url,
            headers=headers,
            auth=auth_cfg,
            body=body_cfg
        )


class CodeSnippetGenerator:
    """Generates ready-to-run code snippets in multiple programming languages."""

    @classmethod
    def to_python_httpx(cls, req: RequestModel) -> str:
        headers_dict = {h.key: h.value for h in req.headers if h.active}
        params_dict = {p.key: p.value for p in req.params if p.active}
        
        lines = [
            "import httpx",
            "",
            f"url = {json.dumps(req.url)}",
            f"headers = {json.dumps(headers_dict, indent=4)}",
            f"params = {json.dumps(params_dict, indent=4)}",
        ]

        if req.body.mode == BodyMode.JSON and req.body.raw:
            lines.append(f"json_payload = {req.body.raw}")
            lines.append(f"response = httpx.{req.method.value.lower()}(url, headers=headers, params=params, json=json_payload)")
        elif req.body.mode == BodyMode.RAW and req.body.raw:
            lines.append(f"content = {json.dumps(req.body.raw)}")
            lines.append(f"response = httpx.{req.method.value.lower()}(url, headers=headers, params=params, content=content)")
        else:
            lines.append(f"response = httpx.{req.method.value.lower()}(url, headers=headers, params=params)")

        lines.append("")
        lines.append("print(response.status_code)")
        lines.append("print(response.text)")
        return "\n".join(lines)

    @classmethod
    def to_python_requests(cls, req: RequestModel) -> str:
        headers_dict = {h.key: h.value for h in req.headers if h.active}
        params_dict = {p.key: p.value for p in req.params if p.active}
        
        lines = [
            "import requests",
            "",
            f"url = {json.dumps(req.url)}",
            f"headers = {json.dumps(headers_dict, indent=4)}",
            f"params = {json.dumps(params_dict, indent=4)}",
        ]

        if req.body.mode == BodyMode.JSON and req.body.raw:
            lines.append(f"data = {json.dumps(req.body.raw)}")
            lines.append(f"response = requests.request('{req.method.value}', url, headers=headers, params=params, data=data)")
        else:
            lines.append(f"response = requests.request('{req.method.value}', url, headers=headers, params=params)")

        lines.append("")
        lines.append("print(response.status_code)")
        lines.append("print(response.text)")
        return "\n".join(lines)

    @classmethod
    def to_curl(cls, req: RequestModel) -> str:
        parts = [f"curl --location --request {req.method.value} '{req.url}'"]
        for h in req.headers:
            if h.active:
                parts.append(f"  --header '{h.key}: {h.value}'")
        if req.body.mode == BodyMode.JSON and req.body.raw:
            clean_body = req.body.raw.replace("'", "'\\''")
            parts.append(f"  --data-raw '{clean_body}'")
        elif req.body.mode == BodyMode.RAW and req.body.raw:
            clean_body = req.body.raw.replace("'", "'\\''")
            parts.append(f"  --data '{clean_body}'")
        return " \\\n".join(parts)

    @classmethod
    def to_javascript_fetch(cls, req: RequestModel) -> str:
        headers_dict = {h.key: h.value for h in req.headers if h.active}
        options: Dict[str, Any] = {
            "method": req.method.value,
            "headers": headers_dict
        }
        if req.body.mode in (BodyMode.JSON, BodyMode.RAW) and req.body.raw:
            options["body"] = req.body.raw

        return f"""const url = '{req.url}';
const options = {json.dumps(options, indent=2)};

fetch(url, options)
  .then(res => res.json())
  .then(json => console.log(json))
  .catch(err => console.error('error:' + err));"""

    @classmethod
    def to_go(cls, req: RequestModel) -> str:
        raw_body_escaped = req.body.raw if req.body.raw else ""
        header_lines = "\n".join([f'\treq.Header.Add("{h.key}", "{h.value}")' for h in req.headers if h.active])
        return f"""package main

import (
	"fmt"
	"io"
	"net/http"
	"strings"
)

func main() {{
	url := "{req.url}"
	method := "{req.method.value}"

	payload := strings.NewReader(`{raw_body_escaped}`)

	client := &http.Client{{}}
	req, err := http.NewRequest(method, url, payload)

	if err != nil {{
		fmt.Println(err)
		return
	}}
{header_lines}

	res, err := client.Do(req)
	if err != nil {{
		fmt.Println(err)
		return
	}}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {{
		fmt.Println(err)
		return
	}}
	fmt.Println(string(body))
}}"""
