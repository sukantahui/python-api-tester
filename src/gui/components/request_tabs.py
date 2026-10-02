"""
PyRestForge - Request Builder Tabs Container
"""

from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from src.core.models.request import HeaderItem, ParamItem, RequestModel
from src.gui.components.auth_widget import AuthWidget
from src.gui.components.body_widget import BodyWidget
from src.gui.components.code_editor import CodeEditor
from src.gui.components.key_value_table import KeyValueTableWidget


class RequestTabsWidget(QWidget):
    """Tabs container for Params, Headers, Auth, Body, Pre-request script, and Tests."""

    request_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_request: Optional[RequestModel] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # 1. Query Params Tab
        self.params_table = KeyValueTableWidget(placeholder_key="Param Name", placeholder_val="Param Value")
        self.params_table.data_changed.connect(self._on_params_changed)
        self.tabs.addTab(self.params_table, "Params")

        # 2. Headers Tab
        self.headers_table = KeyValueTableWidget(placeholder_key="Header Name", placeholder_val="Header Value")
        self.headers_table.data_changed.connect(self._on_headers_changed)
        self.tabs.addTab(self.headers_table, "Headers")

        # 3. Auth Tab
        self.auth_widget = AuthWidget()
        self.auth_widget.auth_changed.connect(self._on_subcomponent_changed)
        self.tabs.addTab(self.auth_widget, "Auth")

        # 4. Body Tab
        self.body_widget = BodyWidget()
        self.body_widget.body_changed.connect(self._on_subcomponent_changed)
        self.tabs.addTab(self.body_widget, "Body")

        # 5. Pre-request Script Tab
        self.pre_script_editor = CodeEditor(language="python")
        self.pre_script_editor.setPlaceholderText("# Python Pre-Request Script\n# Example: req.headers['X-Timestamp'] = str(int(time.time()))")
        self.pre_script_editor.textChanged.connect(self._on_pre_script_changed)
        self.tabs.addTab(self.pre_script_editor, "Pre-request")

        # 6. Tests Tab
        self.tests_editor = CodeEditor(language="python")
        self.tests_editor.setPlaceholderText("# Python Post-Response Assertions\n# Example:\n# def test_status(res, env):\n#     assert res.status_code == 200\n#     env.set('token', res.json()['token'])")
        self.tests_editor.textChanged.connect(self._on_tests_changed)
        self.tabs.addTab(self.tests_editor, "Tests")

        layout.addWidget(self.tabs)

    def set_request(self, request: RequestModel) -> None:
        self._current_request = request

        self.params_table.set_items(request.params)
        self.headers_table.set_items(request.headers)
        self.auth_widget.set_request(request)
        self.body_widget.set_request(request)

        self.pre_script_editor.blockSignals(True)
        self.pre_script_editor.setPlainText(request.pre_request_script or "")
        self.pre_script_editor.blockSignals(False)

        self.tests_editor.blockSignals(True)
        self.tests_editor.setPlainText(request.tests or "")
        self.tests_editor.blockSignals(False)

        self._update_tab_badges()

    def _update_tab_badges(self) -> None:
        if not self._current_request:
            return

        p_count = len([p for p in self._current_request.params if p.active and p.key])
        self.tabs.setTabText(0, f"Params ({p_count})" if p_count else "Params")

        h_count = len([h for h in self._current_request.headers if h.active and h.key])
        self.tabs.setTabText(1, f"Headers ({h_count})" if h_count else "Headers")

    def _on_params_changed(self) -> None:
        if self._current_request:
            items = self.params_table.get_items()
            self._current_request.params = [
                ParamItem(key=it.key, value=it.value, description=it.description, active=it.active)
                for it in items
            ]
            self._update_tab_badges()
            self.request_modified.emit()

    def _on_headers_changed(self) -> None:
        if self._current_request:
            items = self.headers_table.get_items()
            self._current_request.headers = [
                HeaderItem(key=it.key, value=it.value, description=it.description, active=it.active)
                for it in items
            ]
            self._update_tab_badges()
            self.request_modified.emit()

    def _on_pre_script_changed(self) -> None:
        if self._current_request:
            self._current_request.pre_request_script = self.pre_script_editor.toPlainText()
            self.request_modified.emit()

    def _on_tests_changed(self) -> None:
        if self._current_request:
            self._current_request.tests = self.tests_editor.toPlainText()
            self.request_modified.emit()

    def _on_subcomponent_changed(self) -> None:
        self._update_tab_badges()
        self.request_modified.emit()
