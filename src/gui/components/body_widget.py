"""
PyRestForge - Multi-Mode Request Body Editor Component
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.models.request import BodyConfig, BodyMode, FormDataItem, KeyValueItem, RawSyntax, RequestModel
from src.gui.components.code_editor import CodeEditor
from src.gui.components.key_value_table import KeyValueTableWidget
from src.gui.theme import ThemeColors


class BodyWidget(QWidget):
    """Multi-format request body editor."""

    body_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_request: Optional[RequestModel] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Mode Selector Toolbar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Body Type:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "No Body",
            "JSON",
            "Multipart Form",
            "Form URL-Encoded",
            "Raw Text",
            "GraphQL",
            "Binary File",
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        top_bar.addWidget(self.mode_combo)

        # JSON / Raw Prettify Action Buttons
        self.prettify_btn = QPushButton("Prettify JSON")
        self.prettify_btn.clicked.connect(self._prettify_active_editor)
        top_bar.addWidget(self.prettify_btn)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        self.stack = QStackedWidget()

        # 0. None
        no_body_page = QWidget()
        nb_layout = QVBoxLayout(no_body_page)
        lbl = QLabel("This request does not have a body.")
        lbl.setStyleSheet("color: #94A3B8;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nb_layout.addWidget(lbl)
        self.stack.addWidget(no_body_page)

        # 1. JSON
        self.json_editor = CodeEditor(language="json")
        self.json_editor.textChanged.connect(self._on_json_changed)
        self.stack.addWidget(self.json_editor)

        # 2. Form Data
        self.form_data_table = KeyValueTableWidget(placeholder_key="Field Name", placeholder_val="Field Value")
        self.form_data_table.data_changed.connect(self._on_form_data_changed)
        self.stack.addWidget(self.form_data_table)

        # 3. URL-Encoded
        self.urlencoded_table = KeyValueTableWidget(placeholder_key="Key", placeholder_val="Value")
        self.urlencoded_table.data_changed.connect(self._on_urlencoded_changed)
        self.stack.addWidget(self.urlencoded_table)

        # 4. Raw Text
        self.raw_editor = CodeEditor(language="text")
        self.raw_editor.textChanged.connect(self._on_raw_changed)
        self.stack.addWidget(self.raw_editor)

        # 5. GraphQL
        gql_page = QWidget()
        gql_layout = QVBoxLayout(gql_page)
        gql_layout.setContentsMargins(0, 0, 0, 0)
        gql_splitter = QSplitter(Qt.Orientation.Vertical)

        gql_q_container = QWidget()
        gql_q_layout = QVBoxLayout(gql_q_container)
        gql_q_layout.setContentsMargins(0, 0, 0, 0)
        gql_q_layout.addWidget(QLabel("GraphQL Query / Mutation:"))
        self.gql_query_editor = CodeEditor(language="graphql")
        self.gql_query_editor.textChanged.connect(self._on_graphql_changed)
        gql_q_layout.addWidget(self.gql_query_editor)

        gql_v_container = QWidget()
        gql_v_layout = QVBoxLayout(gql_v_container)
        gql_v_layout.setContentsMargins(0, 0, 0, 0)
        gql_v_layout.addWidget(QLabel("Query Variables (JSON):"))
        self.gql_vars_editor = CodeEditor(language="json")
        self.gql_vars_editor.textChanged.connect(self._on_graphql_changed)
        gql_v_layout.addWidget(self.gql_vars_editor)

        gql_splitter.addWidget(gql_q_container)
        gql_splitter.addWidget(gql_v_container)
        gql_splitter.setSizes([300, 150])
        gql_layout.addWidget(gql_splitter)
        self.stack.addWidget(gql_page)

        # 6. Binary File
        binary_page = QWidget()
        bin_layout = QVBoxLayout(binary_page)
        bin_h = QHBoxLayout()
        self.bin_path_input = QLineEdit()
        self.bin_path_input.setPlaceholderText("Select file to upload as binary body...")
        self.bin_path_input.textChanged.connect(self._on_binary_changed)
        bin_browse = QPushButton("Browse...")
        bin_browse.clicked.connect(self._browse_binary_file)
        bin_h.addWidget(self.bin_path_input, stretch=1)
        bin_h.addWidget(bin_browse)
        bin_layout.addLayout(bin_h)
        bin_layout.addStretch()
        self.stack.addWidget(binary_page)

        layout.addWidget(self.stack, stretch=1)

    def set_request(self, request: RequestModel) -> None:
        self._current_request = request
        body = request.body

        mode_map = {
            BodyMode.NONE: 0,
            BodyMode.JSON: 1,
            BodyMode.FORM_DATA: 2,
            BodyMode.URLENCODED: 3,
            BodyMode.RAW: 4,
            BodyMode.GRAPHQL: 5,
            BodyMode.BINARY: 6,
        }
        idx = mode_map.get(body.mode, 0)

        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(idx)
        self.stack.setCurrentIndex(idx)
        self.prettify_btn.setVisible(idx in (1, 4))
        self.mode_combo.blockSignals(False)

        # Populate controls
        self.json_editor.blockSignals(True)
        self.json_editor.setPlainText(body.raw if body.mode == BodyMode.JSON else "")
        self.json_editor.blockSignals(False)

        self.raw_editor.blockSignals(True)
        self.raw_editor.setPlainText(body.raw if body.mode == BodyMode.RAW else "")
        self.raw_editor.blockSignals(False)

        self.urlencoded_table.set_items(body.urlencoded)
        self.form_data_table.set_items([
            KeyValueItem(key=f.key, value=f.value, description=f.description or "", active=f.active)
            for f in body.form_data
        ])

        self.gql_query_editor.blockSignals(True)
        self.gql_vars_editor.blockSignals(True)
        self.gql_query_editor.setPlainText(body.graphql.query)
        self.gql_vars_editor.setPlainText(body.graphql.variables)
        self.gql_query_editor.blockSignals(False)
        self.gql_vars_editor.blockSignals(False)

        self.bin_path_input.blockSignals(True)
        self.bin_path_input.setText(body.binary_file_path or "")
        self.bin_path_input.blockSignals(False)

    def _on_mode_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.prettify_btn.setVisible(index in (1, 4))
        if not self._current_request:
            return

        mode_list = [
            BodyMode.NONE,
            BodyMode.JSON,
            BodyMode.FORM_DATA,
            BodyMode.URLENCODED,
            BodyMode.RAW,
            BodyMode.GRAPHQL,
            BodyMode.BINARY,
        ]
        self._current_request.body.mode = mode_list[index]
        self.body_changed.emit()

    def _on_json_changed(self) -> None:
        if self._current_request and self.stack.currentIndex() == 1:
            self._current_request.body.raw = self.json_editor.toPlainText()
            self.body_changed.emit()

    def _on_raw_changed(self) -> None:
        if self._current_request and self.stack.currentIndex() == 4:
            self._current_request.body.raw = self.raw_editor.toPlainText()
            self.body_changed.emit()

    def _on_form_data_changed(self) -> None:
        if self._current_request and self.stack.currentIndex() == 2:
            items = self.form_data_table.get_items()
            self._current_request.body.form_data = [
                FormDataItem(key=it.key, value=it.value, description=it.description, active=it.active)
                for it in items
            ]
            self.body_changed.emit()

    def _on_urlencoded_changed(self) -> None:
        if self._current_request and self.stack.currentIndex() == 3:
            self._current_request.body.urlencoded = self.urlencoded_table.get_items()
            self.body_changed.emit()

    def _on_graphql_changed(self) -> None:
        if self._current_request and self.stack.currentIndex() == 5:
            self._current_request.body.graphql.query = self.gql_query_editor.toPlainText()
            self._current_request.body.graphql.variables = self.gql_vars_editor.toPlainText()
            self.body_changed.emit()

    def _on_binary_changed(self, text: str) -> None:
        if self._current_request and self.stack.currentIndex() == 6:
            self._current_request.body.binary_file_path = text
            self.body_changed.emit()

    def _browse_binary_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Binary Body File")
        if file_path:
            self.bin_path_input.setText(file_path)

    def _prettify_active_editor(self) -> None:
        if self.stack.currentIndex() == 1:
            self.json_editor.prettify()
        elif self.stack.currentIndex() == 4:
            self.raw_editor.prettify()
