"""
PyRestForge - Variable Interpolation & Dynamic Generator Engine
"""

import datetime
import random
import re
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from src.core.models.environment import EnvVariable, SubEnvironmentModel, WorkspaceEnvironments
from src.core.models.request import RequestModel, ParamItem, HeaderItem, BodyConfig, FormDataItem, KeyValueItem
from src.utils.logger import logger


class VariableInterpolator:
    """
    Interpolates double-curly braces {{variable}} in strings, request URLs,
    headers, query parameters, auth values, and body payloads.
    
    Supports:
    1. Static Environment variables from Global / Workspace / Sub-Environment.
    2. Dynamic Generators:
       - {{$guid}} or {{$uuid}} -> RFC 4122 v4 UUID
       - {{$timestamp}} -> Current Unix epoch in seconds
       - {{$isoTimestamp}} -> Current ISO 8601 UTC timestamp
       - {{$randomInt, min, max}} -> Random integer between min and max
       - {{$randomEmail}} -> Unique synthetic email address
       - {{$randomString, len}} -> Alphanumeric string
    """

    VAR_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_$.:,\s\-]+)\}\}")

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context: Dict[str, Any] = context or {}

    @classmethod
    def from_workspace_environments(
        cls,
        environments: Optional[WorkspaceEnvironments] = None,
        active_sub_env_id: Optional[str] = None,
        runtime_overrides: Optional[Dict[str, Any]] = None
    ) -> "VariableInterpolator":
        """Builds combined dictionary of active variables following hierarchy."""
        merged_vars: Dict[str, Any] = {}

        if environments:
            # 1. Base Workspace Variables
            for var in environments.base_variables:
                if var.enabled:
                    merged_vars[var.key] = var.value

            # 2. Sub-Environment Variables
            target_env_id = active_sub_env_id or environments.active_sub_env_id
            if target_env_id:
                for sub_env in environments.sub_environments:
                    if sub_env.id == target_env_id or sub_env.name == target_env_id:
                        for var in sub_env.variables:
                            if var.enabled:
                                merged_vars[var.key] = var.value
                        break

        # 3. Runtime Script Overrides
        if runtime_overrides:
            merged_vars.update(runtime_overrides)

        return cls(context=merged_vars)

    def resolve_dynamic_generator(self, tag: str) -> Optional[str]:
        """Resolves dynamic macros like {{$guid}}, {{$timestamp}}, {{$randomInt, 1, 100}}."""
        tag = tag.strip()
        
        # Secret tag strip preview if formatted as SECRET:var_name
        if tag.startswith("SECRET:"):
            key = tag[7:].strip()
            return str(self.context.get(key, f"{{{{{tag}}}}}"))

        if tag in ("$guid", "$uuid"):
            return str(uuid.uuid4())
        
        if tag == "$timestamp":
            return str(int(time.time()))
        
        if tag == "$isoTimestamp":
            return datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        if tag == "$randomEmail":
            rand_suffix = secrets.token_hex(4)
            return f"user_{rand_suffix}@example.com"
        
        if tag.startswith("$randomInt"):
            # Syntax: {{$randomInt, 1, 100}} or {{$randomInt}}
            parts = [p.strip() for p in tag.split(",")]
            min_val = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            max_val = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1000
            return str(random.randint(min_val, max_val))
        
        if tag.startswith("$randomString"):
            parts = [p.strip() for p in tag.split(",")]
            length = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            return secrets.token_urlsafe(length)[:length]

        return None

    def interpolate_string(self, text: Optional[str], max_depth: int = 5) -> str:
        """Interpolates variables recursively inside a given text string."""
        if not text:
            return ""

        current_text = str(text)
        depth = 0

        while depth < max_depth and "{{" in current_text and "}}" in current_text:
            matched = False

            def replace_match(match: re.Match) -> str:
                nonlocal matched
                tag = match.group(1).strip()
                
                # Check dynamic generator
                dynamic_val = self.resolve_dynamic_generator(tag)
                if dynamic_val is not None:
                    matched = True
                    return dynamic_val

                # Check static environment variable
                if tag in self.context:
                    matched = True
                    return str(self.context[tag])

                # Keep unresolved token
                return match.group(0)

            new_text = self.VAR_PATTERN.sub(replace_match, current_text)
            if not matched or new_text == current_text:
                break
            current_text = new_text
            depth += 1

        return current_text

    def interpolate_request(self, req: RequestModel) -> RequestModel:
        """Returns a cloned RequestModel with all templated strings interpolated."""
        # Deep clone via model_dump
        data = req.model_dump()
        cloned = RequestModel.model_validate(data)

        # 1. URL
        cloned.url = self.interpolate_string(cloned.url)

        # 2. Query Params
        for p in cloned.params:
            if p.active:
                p.key = self.interpolate_string(p.key)
                p.value = self.interpolate_string(p.value)

        # 3. Headers
        for h in cloned.headers:
            if h.active:
                h.key = self.interpolate_string(h.key)
                h.value = self.interpolate_string(h.value)

        # 4. Auth
        if cloned.auth.bearer_token:
            cloned.auth.bearer_token = self.interpolate_string(cloned.auth.bearer_token)
        if cloned.auth.basic_username:
            cloned.auth.basic_username = self.interpolate_string(cloned.auth.basic_username)
        if cloned.auth.basic_password:
            cloned.auth.basic_password = self.interpolate_string(cloned.auth.basic_password)
        if cloned.auth.api_key_name:
            cloned.auth.api_key_name = self.interpolate_string(cloned.auth.api_key_name)
        if cloned.auth.api_key_value:
            cloned.auth.api_key_value = self.interpolate_string(cloned.auth.api_key_value)
        if cloned.auth.oauth2_access_token:
            cloned.auth.oauth2_access_token = self.interpolate_string(cloned.auth.oauth2_access_token)

        # 5. Body
        if cloned.body.raw:
            cloned.body.raw = self.interpolate_string(cloned.body.raw)
        
        for fd in cloned.body.form_data:
            if fd.active:
                fd.key = self.interpolate_string(fd.key)
                fd.value = self.interpolate_string(fd.value)

        for ue in cloned.body.urlencoded:
            if ue.active:
                ue.key = self.interpolate_string(ue.key)
                ue.value = self.interpolate_string(ue.value)

        if cloned.body.graphql:
            cloned.body.graphql.query = self.interpolate_string(cloned.body.graphql.query)
            cloned.body.graphql.variables = self.interpolate_string(cloned.body.graphql.variables)

        return cloned
