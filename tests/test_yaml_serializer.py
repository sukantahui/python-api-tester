"""
Unit tests for YAML & JSON Serializers
"""

import pytest
from src.core.models.workspace import WorkspaceModel
from src.core.serializers.yaml_serializer import YamlSerializer
from src.core.serializers.json_serializer import JsonSerializer


def test_yaml_roundtrip_fidelity(sample_workspace: WorkspaceModel):
    serializer = YamlSerializer()
    yaml_str = serializer.serialize_workspace(sample_workspace)
    assert "schema_version" in yaml_str
    assert "Test API Suite" in yaml_str
    assert "https://httpbin.org" in yaml_str

    deserialized = serializer.deserialize_workspace(yaml_str)
    assert deserialized.name == sample_workspace.name
    assert len(deserialized.folders) == len(sample_workspace.folders)
    assert deserialized.folders[0].requests[0].name == "Login Endpoint"


def test_yaml_secret_stripping(sample_workspace: WorkspaceModel):
    serializer = YamlSerializer()
    yaml_str = serializer.serialize_workspace(sample_workspace, strip_secrets=True)
    assert "secret_12345" not in yaml_str
    assert "{{SECRET_MASKED}}" in yaml_str


def test_json_roundtrip_fidelity(sample_workspace: WorkspaceModel):
    serializer = JsonSerializer()
    json_str = serializer.serialize_workspace(sample_workspace, pretty=True)
    assert "Test API Suite" in json_str

    deserialized = serializer.deserialize_workspace(json_str)
    assert deserialized.name == sample_workspace.name
    assert deserialized.environments.base_variables[0].key == "baseUrl"
