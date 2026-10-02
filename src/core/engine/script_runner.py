"""
PyRestForge - Python Script Sandbox for Pre-Request Hooks & Test Assertions
"""

import base64
import datetime
import hashlib
import hmac
import json
import math
import random
import re
import time
import urllib.parse
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.core.models.request import RequestModel
from src.core.models.response import ResponseModel, TestAssertionResult
from src.utils.logger import logger


class ScriptEnvContext:
    """Environment helper provided to user scripts."""

    def __init__(self, initial_vars: Optional[Dict[str, Any]] = None):
        self._vars: Dict[str, Any] = dict(initial_vars or {})
        self.mutated_vars: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._vars.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._vars[key] = value
        self.mutated_vars[key] = value

    def delete(self, key: str) -> None:
        if key in self._vars:
            del self._vars[key]
        self.mutated_vars[key] = None

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._vars)


class ScriptResponseWrapper:
    """Response object wrapper provided to user test scripts."""

    def __init__(self, response: ResponseModel):
        self.status_code = response.status_code
        self.status_text = response.status_text
        self.headers = {list(h.keys())[0]: list(h.values())[0] for h in response.headers if h}
        self.elapsed_ms = response.timings.total_ms
        self.text = response.body
        self._cached_json: Optional[Any] = None

    def json(self) -> Any:
        if self._cached_json is None:
            self._cached_json = json.loads(self.text)
        return self._cached_json


class ScriptRunner:
    """Safely executes user pre-request scripts and post-response test assertions."""

    @staticmethod
    def create_safe_globals(env_ctx: ScriptEnvContext) -> Dict[str, Any]:
        return {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "Exception": Exception,
                "AssertionError": AssertionError,
                "ValueError": ValueError,
                "KeyError": KeyError,
                "TypeError": TypeError,
            },
            "json": json,
            "math": math,
            "time": time,
            "datetime": datetime,
            "re": re,
            "uuid": uuid,
            "random": random,
            "hashlib": hashlib,
            "hmac": hmac,
            "base64": base64,
            "urllib": urllib.parse,
            "env": env_ctx,
        }

    @classmethod
    def execute_pre_request(
        cls,
        script_code: Optional[str],
        request: RequestModel,
        env_ctx: ScriptEnvContext
    ) -> Tuple[RequestModel, Dict[str, Any]]:
        """Runs pre-request script modifying request or environment variables."""
        if not script_code or not script_code.strip():
            return request, env_ctx.mutated_vars

        safe_globals = cls.create_safe_globals(env_ctx)
        safe_globals["req"] = request

        try:
            exec(script_code, safe_globals)
            # If function `pre_request(req, env)` is defined, execute it
            if "pre_request" in safe_globals and callable(safe_globals["pre_request"]):
                safe_globals["pre_request"](request, env_ctx)
        except Exception as e:
            logger.error(f"Error executing pre-request script: {e}")

        return request, env_ctx.mutated_vars

    @classmethod
    def execute_tests(
        cls,
        test_script_code: Optional[str],
        response: ResponseModel,
        env_ctx: ScriptEnvContext
    ) -> Tuple[List[TestAssertionResult], Dict[str, Any]]:
        """Runs post-response test assertions and returns pass/fail report."""
        test_results: List[TestAssertionResult] = []
        if not test_script_code or not test_script_code.strip():
            return test_results, env_ctx.mutated_vars

        safe_globals = cls.create_safe_globals(env_ctx)
        res_wrapper = ScriptResponseWrapper(response)
        safe_globals["res"] = res_wrapper
        safe_globals["response"] = res_wrapper

        start_time = time.perf_counter()
        try:
            exec(test_script_code, safe_globals)

            # Check if functions matching test_* exist
            test_funcs = [
                (k, v) for k, v in safe_globals.items()
                if k.startswith("test_") and callable(v)
            ]

            if test_funcs:
                for func_name, func in test_funcs:
                    f_start = time.perf_counter()
                    try:
                        # Try calling with (res, env) or no args
                        try:
                            func(res_wrapper, env_ctx)
                        except TypeError:
                            func()
                        
                        duration = (time.perf_counter() - f_start) * 1000.0
                        test_results.append(TestAssertionResult(
                            name=func_name.replace("test_", "").replace("_", " ").title(),
                            passed=True,
                            duration_ms=round(duration, 2)
                        ))
                    except AssertionError as ae:
                        duration = (time.perf_counter() - f_start) * 1000.0
                        test_results.append(TestAssertionResult(
                            name=func_name.replace("test_", "").replace("_", " ").title(),
                            passed=False,
                            error_message=str(ae) or "Assertion failed",
                            duration_ms=round(duration, 2)
                        ))
                    except Exception as ex:
                        duration = (time.perf_counter() - f_start) * 1000.0
                        test_results.append(TestAssertionResult(
                            name=func_name.replace("test_", "").replace("_", " ").title(),
                            passed=False,
                            error_message=f"Error: {str(ex)}",
                            duration_ms=round(duration, 2)
                        ))
            else:
                # Top level script ran with no functions without throwing error
                duration = (time.perf_counter() - start_time) * 1000.0
                test_results.append(TestAssertionResult(
                    name="Script Execution",
                    passed=True,
                    duration_ms=round(duration, 2)
                ))
        except AssertionError as ae:
            duration = (time.perf_counter() - start_time) * 1000.0
            test_results.append(TestAssertionResult(
                name="Assertion Check",
                passed=False,
                error_message=str(ae) or "Assertion failed",
                duration_ms=round(duration, 2)
            ))
        except Exception as ex:
            duration = (time.perf_counter() - start_time) * 1000.0
            test_results.append(TestAssertionResult(
                name="Script Error",
                passed=False,
                error_message=str(ex),
                duration_ms=round(duration, 2)
            ))

        return test_results, env_ctx.mutated_vars
