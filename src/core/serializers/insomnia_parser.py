"""
PyRestForge - Insomnia v4 Collection Importer & Exporter
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional
import yaml

from src.core.models.auth import AuthConfig, AuthType
from src.core.models.environment import EnvVariable, SubEnvironmentModel, WorkspaceEnvironments
from src.core.models.folder import FolderModel
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel
from src.core.models.workspace import WorkspaceModel
from src.utils.logger import logger


class InsomniaParser:
    """Bi-directional parser and exporter for Insomnia v4 export bundles."""

    @classmethod
    def import_insomnia(cls, content: str) -> WorkspaceModel:
        """Parses an Insomnia v4 JSON or YAML export bundle."""
        try:
            data = json.loads(content)
        except Exception:
            data = yaml.safe_load(content)

        if not isinstance(data, dict) or data.get("_type") != "export":
            # Fallback check if resources list exists
            if not isinstance(data, dict) or "resources" not in data:
                raise ValueError("Invalid Insomnia format: Missing export resources array.")

        resources = data.get("resources", [])

        # 1. Workspace
        ws_res = next((r for r in resources if r.get("_type") == "workspace"), None)
        ws_name = ws_res.get("name", "Imported Insomnia Workspace") if ws_res else "Imported Insomnia Workspace"
        ws_desc = ws_res.get("description", "") if ws_res else ""

        workspace = WorkspaceModel(
            name=ws_name,
            description=ws_desc,
            environments=WorkspaceEnvironments()
        )

        # 2. Environments
        for r in resources:
            if r.get("_type") == "environment":
                env_data = r.get("data", {})
                parent_id = r.get("parentId")
                env_name = r.get("name", "Environment")

                env_vars = [
                    EnvVariable(key=str(k), value=str(v))
                    for k, v in env_data.items()
                ]

                # If root environment or parent is workspace
                if parent_id == (ws_res.get("_id") if ws_res else None) or r.get("name") == "Base Environment":
                    workspace.environments.base_variables.extend(env_vars)
                else:
                    workspace.environments.sub_environments.append(
                        SubEnvironmentModel(
                            name=env_name,
                            color=r.get("color") or "#7C3AED",
                            variables=env_vars
                        )
                    )

        # 3. Folders (request_group)
        folder_dict: Dict[str, FolderModel] = {}
        for r in resources:
            if r.get("_type") == "request_group":
                folder_id = r.get("_id", f"fld_{uuid.uuid4().hex[:8]}")
                folder = FolderModel(
                    id=folder_id,
                    parent_id=r.get("parentId"),
                    name=r.get("name", "New Folder"),
                    description=r.get("description", ""),
                    meta_sort_key=int(r.get("metaSortKey", 0))
                )
                folder_dict[folder_id] = folder

        # 4. Requests
        req_dict: Dict[str, RequestModel] = {}
        for r in resources:
            if r.get("_type") == "request":
                req_id = r.get("_id", f"req_{uuid.uuid4().hex[:8]}")
                method_str = r.get("method", "GET").upper()
                method = HttpMethod(method_str) if method_str in [m.value for m in HttpMethod] else HttpMethod.GET

                # Headers
                headers: List[HeaderItem] = []
                for h in r.get("headers", []):
                    headers.append(HeaderItem(
                        key=h.get("name", ""),
                        value=h.get("value", ""),
                        description=h.get("description", ""),
                        active=not h.get("disabled", False)
                    ))

                # Parameters
                params: List[ParamItem] = []
                for p in r.get("parameters", []):
                    params.append(ParamItem(
                        key=p.get("name", ""),
                        value=p.get("value", ""),
                        description=p.get("description", ""),
                        active=not p.get("disabled", False)
                    ))

                # Auth
                auth_cfg = AuthConfig()
                raw_auth = r.get("authentication", {})
                auth_type = raw_auth.get("type")
                if auth_type == "bearer":
                    auth_cfg.type = AuthType.BEARER
                    auth_cfg.bearer_token = raw_auth.get("token")
                    auth_cfg.bearer_prefix = raw_auth.get("prefix", "Bearer")
                elif auth_type == "basic":
                    auth_cfg.type = AuthType.BASIC
                    auth_cfg.basic_username = raw_auth.get("username")
                    auth_cfg.basic_password = raw_auth.get("password")
                elif auth_type == "apikey":
                    auth_cfg.type = AuthType.API_KEY
                    auth_cfg.api_key_name = raw_auth.get("key")
                    auth_cfg.api_key_value = raw_auth.get("value")

                # Body
                body_cfg = BodyConfig()
                raw_body = r.get("body", {})
                mime_type = raw_body.get("mimeType", "")
                body_text = raw_body.get("text", "")

                if "json" in mime_type or (body_text.startswith("{") and body_text.endswith("}")):
                    body_cfg.mode = BodyMode.JSON
                    body_cfg.raw = body_text
                elif "graphql" in mime_type:
                    body_cfg.mode = BodyMode.GRAPHQL
                    body_cfg.graphql.query = body_text
                elif body_text:
                    body_cfg.mode = BodyMode.RAW
                    body_cfg.raw = body_text

                req = RequestModel(
                    id=req_id,
                    parent_id=r.get("parentId"),
                    name=r.get("name", "Request"),
                    method=method,
                    url=r.get("url", ""),
                    description=r.get("description", ""),
                    params=params,
                    headers=headers,
                    auth=auth_cfg,
                    body=body_cfg,
                    meta_sort_key=int(r.get("metaSortKey", 0))
                )
                req_dict[req_id] = req

        # Link Folders and Requests into Hierarchy
        for f_id, folder in folder_dict.items():
            p_id = folder.parent_id
            if p_id and p_id in folder_dict:
                folder_dict[p_id].folders.append(folder)
            else:
                workspace.folders.append(folder)

        for r_id, req in req_dict.items():
            p_id = req.parent_id
            if p_id and p_id in folder_dict:
                folder_dict[p_id].requests.append(req)
            else:
                workspace.requests.append(req)

        return workspace

    @classmethod
    def export_insomnia(cls, workspace: WorkspaceModel) -> str:
        """Exports a WorkspaceModel to Insomnia v4 JSON format."""
        ws_id = f"wrk_{uuid.uuid4().hex[:12]}"
        now_ts = int(time.time() * 1000)

        resources: List[Dict[str, Any]] = [
            {
                "_id": ws_id,
                "parentId": None,
                "modified": now_ts,
                "created": now_ts,
                "name": workspace.name,
                "description": workspace.description or "",
                "scope": "collection",
                "_type": "workspace"
            }
        ]

        # Base Environment
        base_env_data = {v.key: v.value for v in workspace.environments.base_variables}
        base_env_id = f"env_{uuid.uuid4().hex[:12]}"
        resources.append({
            "_id": base_env_id,
            "parentId": ws_id,
            "modified": now_ts,
            "created": now_ts,
            "name": "Base Environment",
            "data": base_env_data,
            "_type": "environment"
        })

        # Sub-Environments
        for sub in workspace.environments.sub_environments:
            sub_data = {v.key: v.value for v in sub.variables}
            resources.append({
                "_id": f"env_{uuid.uuid4().hex[:12]}",
                "parentId": base_env_id,
                "modified": now_ts,
                "created": now_ts,
                "name": sub.name,
                "data": sub_data,
                "color": sub.color,
                "_type": "environment"
            })

        # Traverse folders & requests
        def export_folder(folder: FolderModel, parent_id: str):
            fld_id = f"fld_{uuid.uuid4().hex[:12]}"
            resources.append({
                "_id": fld_id,
                "parentId": parent_id,
                "modified": now_ts,
                "created": now_ts,
                "name": folder.name,
                "description": folder.description or "",
                "environment": {},
                "_type": "request_group"
            })

            for req in folder.requests:
                export_request(req, fld_id)

            for sub_fld in folder.folders:
                export_folder(sub_fld, fld_id)

        def export_request(req: RequestModel, parent_id: str):
            req_id = f"req_{uuid.uuid4().hex[:12]}"
            headers_list = [
                {"name": h.key, "value": h.value, "disabled": not h.active, "description": h.description or ""}
                for h in req.headers
            ]
            params_list = [
                {"name": p.key, "value": p.value, "disabled": not p.active, "description": p.description or ""}
                for p in req.params
            ]

            body_dict: Dict[str, Any] = {}
            if req.body.mode == BodyMode.JSON:
                body_dict = {"mimeType": "application/json", "text": req.body.raw or ""}
            elif req.body.mode == BodyMode.RAW:
                body_dict = {"mimeType": "text/plain", "text": req.body.raw or ""}
            elif req.body.mode == BodyMode.GRAPHQL:
                body_dict = {"mimeType": "application/graphql", "text": req.body.graphql.query}

            auth_dict: Dict[str, Any] = {}
            if req.auth.type == AuthType.BEARER:
                auth_dict = {"type": "bearer", "token": req.auth.bearer_token, "prefix": req.auth.bearer_prefix or "Bearer"}
            elif req.auth.type == AuthType.BASIC:
                auth_dict = {"type": "basic", "username": req.auth.basic_username, "password": req.auth.basic_password}

            resources.append({
                "_id": req_id,
                "parentId": parent_id,
                "modified": now_ts,
                "created": now_ts,
                "name": req.name,
                "description": req.description or "",
                "url": req.url,
                "method": req.method.value,
                "headers": headers_list,
                "parameters": params_list,
                "body": body_dict,
                "authentication": auth_dict,
                "_type": "request"
            })

        for folder in workspace.folders:
            export_folder(folder, ws_id)

        for req in workspace.requests:
            export_request(req, ws_id)

        bundle = {
            "_type": "export",
            "__export_format": 4,
            "__export_date": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "__export_source": "pyrestforge.desktop.app:v1.0.0",
            "resources": resources
        }

        return json.dumps(bundle, indent=2)
