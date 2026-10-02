"""
Unit tests for Postman Collection v2.1 Parser and Exporter
"""

from pathlib import Path
import pytest
from src.core.models.request import HttpMethod
from src.core.models.workspace import WorkspaceModel
from src.core.serializers.postman_parser import PostmanParser


def test_postman_collection_import_and_export():
    sample_file = Path("samples/sample_collection.json")
    if sample_file.exists():
        ws = PostmanParser.import_postman("""
        {
            "info": {
                "name": "Imported Test Postman Collection",
                "description": "Postman import test",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Auth",
                    "item": [
                        {
                            "name": "Login Request",
                            "request": {
                                "method": "POST",
                                "url": {
                                    "raw": "https://api.test.com/login",
                                    "query": [{"key": "timeout", "value": "10"}]
                                },
                                "header": [{"key": "Content-Type", "value": "application/json"}],
                                "body": {
                                    "mode": "raw",
                                    "raw": "{\\"user\\": \\"tester\\"}"
                                }
                            }
                        }
                    ]
                }
            ],
            "variable": [
                {"key": "baseUrl", "value": "https://api.test.com"}
            ]
        }
        """)

        assert ws.name == "Imported Test Postman Collection"
        assert len(ws.folders) == 1
        assert ws.folders[0].name == "Auth"
        assert len(ws.folders[0].requests) == 1
        assert ws.folders[0].requests[0].name == "Login Request"
        assert ws.folders[0].requests[0].method == HttpMethod.POST

        # Test Export
        exported_json = PostmanParser.export_postman(ws)
        assert "schema.getpostman.com" in exported_json
        assert "Login Request" in exported_json
