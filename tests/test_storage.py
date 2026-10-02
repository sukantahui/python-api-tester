"""
Unit tests for Storage Layer (WorkspaceStore, HistoryStore, ConfigStore)
"""

import pytest
import time
from src.core.models.history import HistoryEntryModel
from src.core.models.request import RequestModel, HttpMethod
from src.core.models.response import ResponseModel, NetworkTimingModel
from src.core.models.workspace import WorkspaceModel
from src.core.storage.config_store import ConfigStore, UserConfig
from src.core.storage.history_store import HistoryStore
from src.core.storage.workspace_store import WorkspaceStore


def test_workspace_store_lifecycle():
    store = WorkspaceStore()
    ws = WorkspaceModel(id="ws_unit_test_99", name="Unit Test Workspace")
    store.save_workspace(ws)

    loaded = store.load_workspace("ws_unit_test_99")
    assert loaded.id == "ws_unit_test_99"
    assert loaded.name == "Unit Test Workspace"

    workspaces = store.list_workspaces()
    assert any(w["id"] == "ws_unit_test_99" for w in workspaces)

    # Cleanup
    store.delete_workspace("ws_unit_test_99")


def test_history_store_lifecycle():
    store = HistoryStore()
    req = RequestModel(id="req_hist_01", name="Hist Req", method=HttpMethod.GET, url="https://api.io")
    resp = ResponseModel(request_id="req_hist_01", status_code=200, status_text="OK", timings=NetworkTimingModel(total_ms=120.5))

    entry = HistoryEntryModel(
        workspace_id="ws_hist_test",
        request_id="req_hist_01",
        request_name="Hist Req",
        method="GET",
        url="https://api.io",
        status_code=200,
        duration_ms=120.5,
        response_size=256,
        request_snapshot=req,
        response_snapshot=resp
    )

    store.add_entry(entry)
    entries = store.get_history_for_workspace("ws_hist_test")
    assert len(entries) >= 1
    assert entries[0].request_name == "Hist Req"
    assert entries[0].status_code == 200

    store.clear_history("ws_hist_test")


def test_config_store():
    store = ConfigStore()
    cfg = store.get_config()
    cfg.default_timeout = 45.0
    store.save(cfg)

    reloaded = store.load()
    assert reloaded.default_timeout == 45.0
