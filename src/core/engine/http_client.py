"""
PyRestForge - Asynchronous HTTP/1.1 & HTTP/2 Network Engine (httpx)
"""

import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import httpx

from src.core.engine.cert_manager import CertManager
from src.core.engine.cookie_manager import PersistentCookieManager
from src.core.engine.network_timing import NetworkProfiler
from src.core.engine.script_runner import ScriptRunner, ScriptEnvContext
from src.core.models.auth import AuthType, ApiKeyLocation
from src.core.models.request import BodyMode, HttpMethod, RequestModel
from src.core.models.response import NetworkTimingModel, ResponseModel
from src.utils.logger import logger


class AsyncHttpEngine:
    """Core network execution client supporting HTTP/1.1 and HTTP/2."""

    def __init__(self, workspace_id: str = "default"):
        self.workspace_id = workspace_id
        self.cookie_manager = PersistentCookieManager(workspace_id=workspace_id)

    def _prepare_headers_and_params(self, req: RequestModel) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Prepares headers and query params dictionary from request model."""
        headers: Dict[str, str] = {}
        for h in req.headers:
            if h.active and h.key.strip():
                headers[h.key.strip()] = h.value

        params: Dict[str, str] = {}
        for p in req.params:
            if p.active and p.key.strip():
                params[p.key.strip()] = p.value

        # Auth Header / Query injection
        if req.auth.type == AuthType.BEARER and req.auth.bearer_token:
            prefix = req.auth.bearer_prefix or "Bearer"
            headers["Authorization"] = f"{prefix} {req.auth.bearer_token}".strip()
        elif req.auth.type == AuthType.BASIC:
            user = req.auth.basic_username or ""
            pwd = req.auth.basic_password or ""
            creds = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {creds}"
        elif req.auth.type == AuthType.API_KEY and req.auth.api_key_name and req.auth.api_key_value:
            if req.auth.api_key_location == ApiKeyLocation.HEADER:
                headers[req.auth.api_key_name] = req.auth.api_key_value
            else:
                params[req.auth.api_key_name] = req.auth.api_key_value
        elif req.auth.type == AuthType.OAUTH2 and req.auth.oauth2_access_token:
            headers["Authorization"] = f"Bearer {req.auth.oauth2_access_token}"

        return headers, params

    def _prepare_body(self, req: RequestModel, headers: Dict[str, str]) -> Tuple[Optional[Any], Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[bytes]]:
        """Prepares content, json, data, files based on BodyMode."""
        content: Optional[bytes] = None
        json_data: Optional[Any] = None
        data: Optional[Dict[str, Any]] = None
        files: Optional[Dict[str, Any]] = None

        if req.body.mode == BodyMode.NONE:
            return None, None, None, None

        elif req.body.mode == BodyMode.JSON:
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            if req.body.raw:
                try:
                    json_data = json.loads(req.body.raw)
                except Exception:
                    content = req.body.raw.encode("utf-8")

        elif req.body.mode == BodyMode.URLENCODED:
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            form_dict: Dict[str, str] = {}
            for item in req.body.urlencoded:
                if item.active and item.key.strip():
                    form_dict[item.key.strip()] = item.value
            data = form_dict

        elif req.body.mode == BodyMode.FORM_DATA:
            form_data_dict: Dict[str, Any] = {}
            files_dict: Dict[str, Any] = {}
            for fd in req.body.form_data:
                if not fd.active or not fd.key.strip():
                    continue
                if fd.is_file and fd.file_path:
                    path = Path(fd.file_path)
                    if path.exists():
                        files_dict[fd.key] = (path.name, open(str(path), "rb"), fd.content_type or "application/octet-stream")
                else:
                    form_data_dict[fd.key] = fd.value
            data = form_data_dict if form_data_dict else None
            files = files_dict if files_dict else None

        elif req.body.mode == BodyMode.RAW:
            if req.body.raw:
                content = req.body.raw.encode("utf-8")

        elif req.body.mode == BodyMode.GRAPHQL:
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            gql_vars = {}
            if req.body.graphql.variables:
                try:
                    gql_vars = json.loads(req.body.graphql.variables)
                except Exception:
                    pass
            json_data = {
                "query": req.body.graphql.query,
                "variables": gql_vars
            }

        elif req.body.mode == BodyMode.BINARY and req.body.binary_file_path:
            path = Path(req.body.binary_file_path)
            if path.exists():
                with open(str(path), "rb") as bf:
                    content = bf.read()

        return content, json_data, data, files

    async def send_async(
        self,
        request: RequestModel,
        env_vars: Optional[Dict[str, Any]] = None,
        cancel_event: Optional[asyncio.Event] = None
    ) -> Tuple[ResponseModel, Dict[str, Any]]:
        """Dispatches an HTTP request asynchronously and returns ResponseModel + mutated env vars."""
        env_ctx = ScriptEnvContext(env_vars)

        # 1. Pre-Request script execution
        prepared_req, _ = ScriptRunner.execute_pre_request(
            request.pre_request_script,
            request,
            env_ctx
        )

        headers, params = self._prepare_headers_and_params(prepared_req)
        content, json_data, data, files = self._prepare_body(prepared_req, headers)

        # Target URL validation
        url = prepared_req.url.strip()
        if not url:
            return ResponseModel(
                request_id=request.id,
                status_code=0,
                status_text="Error",
                error_message="Empty URL specified. Please enter a valid URL."
            ), env_ctx.mutated_vars

        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"

        profiler = NetworkProfiler()
        profiler.start()

        timeout_val = httpx.Timeout(timeout=prepared_req.timeout or 30.0, connect=10.0)

        # SSL certificate extraction attempt in parallel
        cert_info = None
        if url.startswith("https://"):
            try:
                cert_info = CertManager.extract_server_certificate(url, timeout=2.0)
            except Exception:
                pass

        # Check if HTTP/2 (h2) package is installed
        use_http2 = False
        try:
            import h2
            use_http2 = True
        except ImportError:
            pass

        try:
            async with httpx.AsyncClient(
                http2=use_http2,
                verify=prepared_req.verify_ssl,
                follow_redirects=prepared_req.follow_redirects,
                timeout=timeout_val,
                cookies=self.cookie_manager.get_httpx_cookies()
            ) as client:
                req_task = client.request(
                    method=prepared_req.method.value,
                    url=url,
                    params=params,
                    headers=headers,
                    content=content,
                    json=json_data,
                    data=data,
                    files=files,
                )

                if cancel_event:
                    # Allow cancellation
                    waiter = asyncio.create_task(cancel_event.wait())
                    http_task = asyncio.create_task(req_task)
                    done, pending = await asyncio.wait([waiter, http_task], return_when=asyncio.FIRST_COMPLETED)
                    if cancel_event.is_set():
                        http_task.cancel()
                        return ResponseModel(
                            request_id=request.id,
                            status_code=0,
                            status_text="Cancelled",
                            error_message="Request was cancelled by user."
                        ), env_ctx.mutated_vars
                    response = await http_task
                else:
                    response = await req_task

                timings = profiler.record_finish(response.elapsed.total_seconds())

                # Extract cookies
                cookies_list = self.cookie_manager.update_from_response(response)

                # Format response headers
                formatted_headers = [{k: v} for k, v in response.headers.items()]

                # Response payload
                response_text = response.text
                raw_size = len(response.content)
                content_type = response.headers.get("content-type", "text/plain")

                resp_model = ResponseModel(
                    request_id=request.id,
                    status_code=response.status_code,
                    status_text=response.reason_phrase or "OK",
                    http_version=response.http_version,
                    headers=formatted_headers,
                    cookies=cookies_list,
                    body=response_text,
                    raw_bytes_size=raw_size,
                    content_type=content_type,
                    timings=timings,
                    certificate=cert_info,
                    timestamp=time.time()
                )

                # Execute tests assertions
                test_results, _ = ScriptRunner.execute_tests(
                    prepared_req.tests,
                    resp_model,
                    env_ctx
                )
                resp_model.test_results = test_results

                return resp_model, env_ctx.mutated_vars

        except httpx.TimeoutException:
            timings = profiler.record_finish()
            return ResponseModel(
                request_id=request.id,
                status_code=0,
                status_text="Timeout",
                timings=timings,
                error_message=f"Request timed out after {prepared_req.timeout} seconds."
            ), env_ctx.mutated_vars
        except httpx.ConnectError as ce:
            timings = profiler.record_finish()
            return ResponseModel(
                request_id=request.id,
                status_code=0,
                status_text="Connection Error",
                timings=timings,
                error_message=f"Failed to connect to host: {str(ce)}"
            ), env_ctx.mutated_vars
        except Exception as e:
            timings = profiler.record_finish()
            return ResponseModel(
                request_id=request.id,
                status_code=0,
                status_text="Error",
                timings=timings,
                error_message=f"Network error: {str(e)}"
            ), env_ctx.mutated_vars

    def send_sync(
        self,
        request: RequestModel,
        env_vars: Optional[Dict[str, Any]] = None
    ) -> Tuple[ResponseModel, Dict[str, Any]]:
        """Synchronous wrapper for executing request in background thread."""
        return asyncio.run(self.send_async(request, env_vars))
