"""
Unit tests for AsyncHttpEngine with HTTP mocking (respx)
"""

import pytest
import respx
import httpx
from src.core.engine.http_client import AsyncHttpEngine
from src.core.models.auth import AuthConfig, AuthType, ApiKeyLocation
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel


@pytest.mark.asyncio
@respx.mock
async def test_http_get_request():
    respx.get("https://api.example.com/v1/users").respond(
        status_code=200,
        json={"data": [{"id": 1, "name": "Alice"}]},
        headers={"Content-Type": "application/json"}
    )

    engine = AsyncHttpEngine(workspace_id="test_ws")
    req = RequestModel(
        method=HttpMethod.GET,
        url="https://api.example.com/v1/users",
        params=[ParamItem(key="limit", value="10", active=True)]
    )

    response, _ = await engine.send_async(req)
    assert response.status_code == 200
    assert response.status_text == "OK"
    assert "Alice" in response.body


@pytest.mark.asyncio
@respx.mock
async def test_http_post_json_with_bearer():
    respx.post("https://api.example.com/v1/login").respond(
        status_code=201,
        json={"access_token": "mock_jwt_xyz"},
        headers={"Content-Type": "application/json"}
    )

    engine = AsyncHttpEngine(workspace_id="test_ws")
    req = RequestModel(
        method=HttpMethod.POST,
        url="https://api.example.com/v1/login",
        headers=[HeaderItem(key="Content-Type", value="application/json", active=True)],
        auth=AuthConfig(type=AuthType.BEARER, bearer_token="initial_token"),
        body=BodyConfig(mode=BodyMode.JSON, raw='{"username": "admin"}')
    )

    response, _ = await engine.send_async(req)
    assert response.status_code == 201
    assert "mock_jwt_xyz" in response.body


@pytest.mark.asyncio
@respx.mock
async def test_http_post_with_test_assertion():
    respx.post("https://api.example.com/v1/auth").respond(
        status_code=200,
        json={"token": "secret_abc"}
    )

    engine = AsyncHttpEngine(workspace_id="test_ws")
    req = RequestModel(
        method=HttpMethod.POST,
        url="https://api.example.com/v1/auth",
        tests="def test_token(res, env):\n    assert res.status_code == 200\n    env.set('captured_token', res.json()['token'])"
    )

    response, mutated_vars = await engine.send_async(req)
    assert response.status_code == 200
    assert len(response.test_results) == 1
    assert response.test_results[0].passed is True
    assert mutated_vars.get("captured_token") == "secret_abc"
