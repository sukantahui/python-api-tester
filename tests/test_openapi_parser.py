"""
Unit tests for OpenAPI, Insomnia, Postman, cURL Parsers and Script Runner
"""

from pathlib import Path
import pytest

from src.core.engine.script_runner import ScriptEnvContext, ScriptRunner
from src.core.models.request import HttpMethod, RequestModel
from src.core.models.response import ResponseModel
from src.core.serializers.curl_parser import CodeSnippetGenerator, CurlParser
from src.core.serializers.insomnia_parser import InsomniaParser
from src.core.serializers.openapi_parser import OpenAPIParser
from src.core.serializers.postman_parser import PostmanParser


def test_openapi_import_export():
    sample_file = Path("samples/sample_openapi.yaml")
    if sample_file.exists():
        content = sample_file.read_text(encoding="utf-8")
        ws = OpenAPIParser.import_spec(content)
        assert ws.name == "Petstore & Authentication API"
        assert len(ws.folders) > 0

        # Export back
        exported = OpenAPIParser.export_spec(ws, as_yaml=True)
        assert "openapi: 3.1.0" in exported
        assert "/pets" in exported


def test_insomnia_import_export():
    sample_file = Path("samples/sample_insomnia_export.json")
    if sample_file.exists():
        content = sample_file.read_text(encoding="utf-8")
        ws = InsomniaParser.import_insomnia(content)
        assert ws.name == "Sample Insomnia Workspace"
        assert len(ws.folders) > 0
        assert ws.folders[0].requests[0].method in (HttpMethod.GET, HttpMethod.POST)

        exported = InsomniaParser.export_insomnia(ws)
        assert '"_type": "export"' in exported


def test_curl_parser_and_codegen():
    curl_cmd = "curl -X POST https://api.example.com/v1/users -H 'Content-Type: application/json' -H 'Authorization: Bearer my_token' -d '{\"name\":\"Alice\"}'"
    req = CurlParser.parse_curl(curl_cmd)
    assert req.method == HttpMethod.POST
    assert req.url == "https://api.example.com/v1/users"
    assert req.auth.bearer_token == "my_token"
    assert "Alice" in (req.body.raw or "")

    # Code generation
    py_code = CodeSnippetGenerator.to_python_httpx(req)
    assert "import httpx" in py_code
    assert "httpx.post" in py_code

    curl_gen = CodeSnippetGenerator.to_curl(req)
    assert "curl --location --request POST" in curl_gen


def test_script_runner_assertions():
    response = ResponseModel(
        request_id="req_test",
        status_code=200,
        body='{"status": "ok", "token": "jwt_secret_999"}'
    )
    env_ctx = ScriptEnvContext({"initial": "val"})

    test_script = """
def test_status_code(res, env):
    assert res.status_code == 200

def test_token_capture(res, env):
    data = res.json()
    assert data["status"] == "ok"
    env.set("auth_token", data["token"])
"""

    results, mutated = ScriptRunner.execute_tests(test_script, response, env_ctx)
    assert len(results) == 2
    assert all(r.passed for r in results)
    assert mutated.get("auth_token") == "jwt_secret_999"
