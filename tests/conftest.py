import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.core.models.environment import EnvVariable, SubEnvironmentModel, WorkspaceEnvironments
from src.core.models.folder import FolderModel
from src.core.models.request import BodyConfig, BodyMode, HeaderItem, HttpMethod, ParamItem, RequestModel
from src.core.models.workspace import WorkspaceModel


@pytest.fixture
def sample_workspace() -> WorkspaceModel:
    """Fixture providing a complete test workspace with environments, folders, and requests."""
    return WorkspaceModel(
        id="ws_test_001",
        name="Test API Suite",
        description="Comprehensive workspace for unit and integration testing",
        environments=WorkspaceEnvironments(
            base_variables=[
                EnvVariable(key="baseUrl", value="https://httpbin.org"),
                EnvVariable(key="apiVersion", value="v1"),
                EnvVariable(key="secretKey", value="secret_12345", is_secret=True)
            ],
            sub_environments=[
                SubEnvironmentModel(
                    name="Staging",
                    variables=[
                        EnvVariable(key="baseUrl", value="https://staging.httpbin.org")
                    ]
                )
            ]
        ),
        folders=[
            FolderModel(
                id="fld_01",
                name="Auth",
                requests=[
                    RequestModel(
                        id="req_01",
                        name="Login Endpoint",
                        method=HttpMethod.POST,
                        url="{{baseUrl}}/post",
                        headers=[HeaderItem(key="Content-Type", value="application/json", active=True)],
                        body=BodyConfig(mode=BodyMode.JSON, raw='{"user": "tester", "id": "{{$guid}}"}'),
                        tests="def test_status(res, env):\n    assert res.status_code == 200\n"
                    )
                ]
            )
        ]
    )
