"""
PyRestForge - OpenAPI 3.0 / 3.1 & Swagger 2.0 Importer & Exporter
"""

import json
from typing import Any, Dict, List, Optional
import yaml

from src.core.models.environment import EnvVariable, WorkspaceEnvironments
from src.core.models.folder import FolderModel
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel
from src.core.models.workspace import WorkspaceModel
from src.utils.logger import logger


class OpenAPIParser:
    """Parses and exports OpenAPI 3.0 / 3.1 and Swagger 2.0 specifications."""

    @classmethod
    def import_spec(cls, content: str) -> WorkspaceModel:
        """Parses an OpenAPI YAML or JSON string into a WorkspaceModel."""
        try:
            data = yaml.safe_load(content)
        except Exception:
            data = json.loads(content)

        if not isinstance(data, dict):
            raise ValueError("Invalid OpenAPI specification: Root must be an object.")

        info = data.get("info", {})
        title = info.get("title", "Imported OpenAPI Specification")
        description = info.get("description", "")
        version = info.get("version", "1.0.0")

        # Base URL from servers
        base_url = "https://api.example.com"
        servers = data.get("servers", [])
        if servers and isinstance(servers, list):
            base_url = servers[0].get("url", base_url)
        elif "host" in data:
            # Swagger 2.0
            scheme = (data.get("schemes") or ["https"])[0]
            base_path = data.get("basePath", "")
            base_url = f"{scheme}://{data['host']}{base_path}"

        workspace = WorkspaceModel(
            name=title,
            description=description,
            version=version,
            environments=WorkspaceEnvironments(
                base_variables=[
                    EnvVariable(key="baseUrl", value=base_url, description="Base API Host URL")
                ]
            )
        )

        paths = data.get("paths", {})
        folder_map: Dict[str, FolderModel] = {}

        for path_key, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Path level parameters
            common_params = path_item.get("parameters", [])

            for method_name, op in path_item.items():
                if method_name.upper() not in [m.value for m in HttpMethod]:
                    continue

                op_summary = op.get("summary") or op.get("operationId") or f"{method_name.upper()} {path_key}"
                op_desc = op.get("description", "")
                tags = op.get("tags", ["Default"])
                tag = tags[0] if tags else "Default"

                # Ensure tag folder exists
                if tag not in folder_map:
                    folder = FolderModel(name=tag, description=f"Endpoints for {tag}")
                    folder_map[tag] = folder
                    workspace.folders.append(folder)
                else:
                    folder = folder_map[tag]

                # Convert OpenAPI path parameters / query parameters
                params_list: List[ParamItem] = []
                headers_list: List[HeaderItem] = []

                all_params = list(common_params) + list(op.get("parameters", []))
                for param in all_params:
                    if not isinstance(param, dict):
                        continue
                    p_name = param.get("name", "")
                    p_in = param.get("in", "query")
                    p_desc = param.get("description", "")
                    schema = param.get("schema", {})
                    p_default = str(schema.get("default", "")) if isinstance(schema, dict) else ""

                    if p_in == "query":
                        params_list.append(ParamItem(
                            key=p_name,
                            value=p_default,
                            description=p_desc,
                            active=True
                        ))
                    elif p_in == "header":
                        headers_list.append(HeaderItem(
                            key=p_name,
                            value=p_default,
                            description=p_desc,
                            active=True
                        ))

                # Body Handling
                body_config = BodyConfig()
                request_body = op.get("requestBody", {})
                if isinstance(request_body, dict):
                    rb_content = request_body.get("content", {})
                    if "application/json" in rb_content:
                        body_config.mode = BodyMode.JSON
                        schema = rb_content["application/json"].get("schema", {})
                        example = rb_content["application/json"].get("example") or schema.get("example")
                        if example:
                            body_config.raw = json.dumps(example, indent=2)
                        else:
                            body_config.raw = "{\n  \n}"
                        headers_list.append(HeaderItem(key="Content-Type", value="application/json", active=True))

                req_model = RequestModel(
                    name=op_summary,
                    method=HttpMethod(method_name.upper()),
                    url=f"{{{{baseUrl}}}}{path_key}",
                    description=op_desc,
                    params=params_list,
                    headers=headers_list,
                    body=body_config
                )

                folder.requests.append(req_model)

        return workspace

    @classmethod
    def export_spec(cls, workspace: WorkspaceModel, as_yaml: bool = True) -> str:
        """Exports a WorkspaceModel into an OpenAPI 3.1 specification."""
        base_url = "https://api.example.com"
        for v in workspace.environments.base_variables:
            if v.key == "baseUrl":
                base_url = v.value

        spec: Dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {
                "title": workspace.name,
                "description": workspace.description or "Exported from PyRestForge",
                "version": workspace.version or "1.0.0"
            },
            "servers": [
                {"url": base_url, "description": "Default Server"}
            ],
            "paths": {}
        }

        # Traverse requests
        def process_request(req: RequestModel, tag_name: str):
            # Extract path from URL by stripping {{baseUrl}}
            url = req.url
            if url.startswith("{{baseUrl}}"):
                path_str = url[11:]
            elif url.startswith("http"):
                from urllib.parse import urlparse
                path_str = urlparse(url).path
            else:
                path_str = url if url.startswith("/") else f"/{url}"

            if not path_str:
                path_str = "/"

            if path_str not in spec["paths"]:
                spec["paths"][path_str] = {}

            method_lower = req.method.value.lower()
            operation: Dict[str, Any] = {
                "tags": [tag_name],
                "summary": req.name,
                "description": req.description or "",
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful operation"
                    }
                }
            }

            for p in req.params:
                if p.active and p.key:
                    operation["parameters"].append({
                        "name": p.key,
                        "in": "query",
                        "description": p.description or "",
                        "schema": {"type": "string", "default": p.value}
                    })

            for h in req.headers:
                if h.active and h.key and h.key.lower() not in ("content-type", "accept", "authorization"):
                    operation["parameters"].append({
                        "name": h.key,
                        "in": "header",
                        "description": h.description or "",
                        "schema": {"type": "string", "default": h.value}
                    })

            if req.body.mode == BodyMode.JSON and req.body.raw:
                try:
                    parsed = json.loads(req.body.raw)
                    operation["requestBody"] = {
                        "content": {
                            "application/json": {
                                "example": parsed
                            }
                        }
                    }
                except Exception:
                    pass

            spec["paths"][path_str][method_lower] = operation

        for folder in workspace.folders:
            for req in folder.requests:
                process_request(req, folder.name)

        for req in workspace.requests:
            process_request(req, "Default")

        if as_yaml:
            return yaml.dump(spec, sort_keys=False)
        return json.dumps(spec, indent=2)
