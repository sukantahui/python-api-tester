"""
PySide6 GUI Component & State tests using pytest-qt
"""

import pytest
from PySide6.QtCore import Qt
from src.core.models.request import HttpMethod, RequestModel
from src.core.models.workspace import WorkspaceModel
from src.gui.app import MainWindow
from src.gui.components.sidebar import SidebarWidget
from src.gui.components.url_bar import UrlBarWidget
from src.gui.components.request_tabs import RequestTabsWidget
from src.gui.components.response_viewer import ResponseViewerWidget


def test_url_bar_widget(qtbot):
    widget = UrlBarWidget()
    qtbot.addWidget(widget)

    req = RequestModel(name="Test Req", method=HttpMethod.POST, url="https://httpbin.org/post")
    widget.set_request(req)

    assert widget.method_combo.currentText() == "POST"
    assert widget.url_input.text() == "https://httpbin.org/post"

    # Modify method
    widget.method_combo.setCurrentText("PUT")
    assert req.method == HttpMethod.PUT


def test_request_tabs_widget(qtbot):
    widget = RequestTabsWidget()
    qtbot.addWidget(widget)

    req = RequestModel(name="Tabs Test", method=HttpMethod.GET, url="https://httpbin.org/get")
    widget.set_request(req)

    assert widget.tabs.count() == 6
    assert "Params" in widget.tabs.tabText(0)
    assert "Headers" in widget.tabs.tabText(1)


def test_main_window_initialization(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)

    assert win.windowTitle().startswith("PyRestForge")
    assert win.sidebar is not None
    assert win.url_bar is not None
    assert win.response_viewer is not None
