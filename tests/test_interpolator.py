"""
Unit tests for Variable Interpolator Engine
"""

import pytest
import re
from src.core.engine.interpolator import VariableInterpolator
from src.core.models.environment import EnvVariable, SubEnvironmentModel, WorkspaceEnvironments
from src.core.models.request import RequestModel, HttpMethod


def test_static_interpolation():
    interpolator = VariableInterpolator(context={"baseUrl": "https://api.io", "userId": "42"})
    assert interpolator.interpolate_string("{{baseUrl}}/users/{{userId}}") == "https://api.io/users/42"


def test_dynamic_guid_generator():
    interpolator = VariableInterpolator()
    res = interpolator.interpolate_string("prefix-{{$guid}}-suffix")
    guid_val = res.replace("prefix-", "").replace("-suffix", "")
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", guid_val)


def test_dynamic_timestamp_generator():
    interpolator = VariableInterpolator()
    res = interpolator.interpolate_string("{{$timestamp}}")
    assert res.isdigit()
    assert int(res) > 1700000000


def test_dynamic_random_email():
    interpolator = VariableInterpolator()
    res = interpolator.interpolate_string("{{$randomEmail}}")
    assert "@example.com" in res
    assert res.startswith("user_")


def test_dynamic_random_int():
    interpolator = VariableInterpolator()
    res = interpolator.interpolate_string("{{$randomInt, 50, 60}}")
    val = int(res)
    assert 50 <= val <= 60


def test_workspace_hierarchy_resolution():
    envs = WorkspaceEnvironments(
        base_variables=[
            EnvVariable(key="baseUrl", value="https://base.org"),
            EnvVariable(key="envName", value="base")
        ],
        sub_environments=[
            SubEnvironmentModel(
                id="sub_prod",
                name="Production",
                variables=[
                    EnvVariable(key="baseUrl", value="https://prod.org"),
                    EnvVariable(key="envName", value="production")
                ]
            )
        ]
    )

    interp_base = VariableInterpolator.from_workspace_environments(envs)
    assert interp_base.interpolate_string("{{baseUrl}}") == "https://base.org"

    interp_prod = VariableInterpolator.from_workspace_environments(envs, active_sub_env_id="sub_prod")
    assert interp_prod.interpolate_string("{{baseUrl}}") == "https://prod.org"
