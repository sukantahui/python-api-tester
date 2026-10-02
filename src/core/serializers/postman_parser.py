"""
PyRestForge - Postman Collection v2.1 Importer & Exporter
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from src.core.models.auth import AuthConfig, AuthType
from src.core.models.environment import EnvVariable, WorkspaceEnvironments
from src.core.models.folder import FolderModel
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel
from src.core.models.workspace import WorkspaceModel
from src.utils.logger import logger


class PostmanParser:
    """Bi-directional parser and exporter for Postman Collection v2.1."""

    @classmethod
    def import_postman(cls, content: str) -> WorkspaceModel:
        """Parses a Postman Collection v2.1 JSON string."""
        data = json.loads(content)
        if not isinstance(data, dict) or "info" not in data:
            raise ValueError("Invalid Postman Collection: Missing 'info' object.")

        info = data.get("info", {})
        ws_name = info.get("name", "Imported Postman Collection")
        ws_desc = info.get("description", "")

        workspace = WorkspaceModel(
            name=ws_name,
            description=ws_desc,
            environments=WorkspaceEnvironments()
        )

        # Variables
        for var in data.get("variable", []):
            workspace.environments.base_variables.append(EnvVariable(
                key=var.get("key", ""),
                value=str(var.get("value", "")),
                description=var.get("description", "")
            ))

        def parse_item_list(items: List[Dict[str, Any]], parent_folder: Optional[FolderModel] = None):
            for item in items:
                if "item" in item:
                    # It's a folder
                    folder = FolderModel(
                        name=item.get("name", "Folder"),
                        description=item.get("description", "")
                    )
                    if parent_folder:
                        parent_folder.folders.append(folder)
                    else:
                        workspace.folders.append(folder)
                    parse_item_list(item.get("item", []), folder)
                elif "request" in item:
                    # It's a request
                    req_obj = item.get("request", {})
                    req_name = item.get("name", "Request")
                    req_model = cls._parse_postman_request(req_name, req_obj)
                    if parent_folder:
                        parent_folder.requests.append(req_model)
                    else:
                        workspace.requests.append(req_model)

        parse_item_list(data.get("item", []))
        return workspace

    @classmethod
    def _parse_postman_request(cls, name: str, req_obj: Dict[str, Any]) -> RequestModel:
        method_str = req_obj.get("method", "GET").upper()
        method = HttpMethod(method_str) if method_str in [m.value for m in HttpMethod] else HttpMethod.GET

        # URL
        url_obj = req_obj.get("url", "")
        url_str = ""
        params_list: List[ParamItem] = []

        if isinstance(url_obj, str):
            url_str = url_obj
        elif isinstance(url_obj, dict):
            url_str = url_obj.get("raw", "")
            for q in url_obj.get("query", []):
                params_list.append(ParamItem(
                    key=q.get("key", ""),
                    value=q.get("value", ""),
                    description=q.get("description", ""),
                    active=not q.get("disabled", False)
                ))

        # Headers
        headers_list: List[HeaderItem] = []
        for h in req_obj.get("header", []):
            headers_list.append(HeaderItem(
                key=h.get("key", ""),
                value=h.get("value", ""),
                description=h.get("description", ""),
                active=not h.get("disabled", False)
            ))

        # Auth
        auth_cfg = AuthConfig()
        raw_auth = req_obj.get("auth", {})
        auth_type = raw_auth.get("type")
        if auth_type == "bearer":
            bearer_vals = {v.get("key"): v.get("value") for v in raw_auth.get("bearer", [])}
            auth_cfg.type = AuthType.BEARER
            auth_cfg.bearer_token = bearer_vals.get("token")
        elif auth_type == "basic":
            basic_vals = {v.get("key"): v.get("value") for v in raw_auth.get("basic", [])}
            auth_cfg.type = AuthType.BASIC
            auth_cfg.basic_username = basic_vals.get("username")
            auth_cfg.basic_password = basic_vals.get("password")

        # Body
        body_cfg = BodyConfig()
        raw_body = req_obj.get("body", {})
        body_mode = raw_body.get("mode", "")

        if body_mode == "raw":
            body_cfg.mode = BodyMode.JSON if "json" in raw_body.get("options", {}).get("raw", {}).get("language", "") else BodyMode.RAW
            body_cfg.raw = raw_body.get("raw", "")
        elif body_mode == "graphql":
            body_cfg.mode = BodyMode.GRAPHQL
            body_cfg.graphql.query = raw_body.get("graphql", {}).get("query", "")
            body_cfg.graphql.variables = raw_body.get("graphql", {}).get("variables", "{}")

        return RequestModel(
            name=name,
            method=method,
            url=url_str,
            description=req_obj.get("description", ""),
            params=params_list,
            headers=headers_list,
            auth=auth_cfg,
            body=body_cfg
        )

    @classmethod
    def export_postman(cls, workspace: WorkspaceModel) -> str:
        """Exports a WorkspaceModel to Postman Collection v2.1 JSON."""
        collection_id = str(uuid.uuid4())

        def export_request_item(req: RequestModel) -> Dict[str, Any]:
            header_items = [
                {"key": h.key, "value": h.value, "type": "text", "disabled": not h.active}
                for h in req.headers
            ]

            body_dict: Dict[str, Any] = {}
            if req.body.mode == BodyMode.JSON:
                body_dict = {
                    "mode": "raw",
                    "raw": req.body.raw or "",
                    "options": {"raw": {"language": "json"}}
                }
            elif req.body.mode == BodyMode.RAW:
                body_dict = {"mode": "raw", "raw": req.body.raw or ""}

            return {
                "name": req.name,
                "request": {
                    "method": req.method.value,
                    "header": header_items,
                    "body": body_dict,
                    "url": {
                        "raw": req.url,
                        "query": [
                            {"key": p.key, "value": p.value, "disabled": not p.active}
                            for p in req.params
                        ]
                    },
                    "description": req.description or ""
                }
            }

        def export_folder_item(folder: FolderModel) -> Dict[str, Any]:
            items: List[Dict[str, Any]] = []
            for sub_fld in folder.folders:
                items.append(export_folder_item(sub_fld))
            for req in folder.requests:
                items.append(export_request_item(req))
            return {
                "name": folder.name,
                "description": folder.description or "",
                "item": items
            }

        root_items: List[Dict[str, Any]] = []
        for folder in workspace.folders:
            root_items.append(export_folder_item(folder))
        for req in workspace.requests:
            root_items.append(export_request_item(req))

        collection = {
            "info": {
                "_postman_id": collection_id,
                "name": workspace.name,
                "description": workspace.description or "",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": root_items,
            "variable": [
                {"key": v.key, "value": v.value, "type": "string"}
                for v in workspace.environments.base_variables
            ]
        }

        return json.dumps(collection, indent=2)
