"""
PyRestForge - Response Inspector & Timeline Viewer Component
"""

import json
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.core.models.response import ResponseModel
from src.gui.components.code_editor import CodeEditor
from src.gui.theme import ThemeColors, get_status_color
from src.utils.formatters import format_latency, format_size, pretty_print_json, pretty_print_xml


class ResponseViewerWidget(QWidget):
    """Insomnia-grade Response Inspector with Pretty/Raw/Preview, Headers, Cookies, and Timeline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_response: Optional[ResponseModel] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. Top Response Status & Metrics Header Bar
        self.metrics_bar = QFrame()
        self.metrics_bar.setStyleSheet(f"background-color: {ThemeColors.BG_PANEL}; border-radius: 6px; padding: 4px;")
        m_layout = QHBoxLayout(self.metrics_bar)
        m_layout.setContentsMargins(8, 4, 8, 4)
        m_layout.setSpacing(12)

        self.status_pill = QLabel("Ready")
        self.status_pill.setStyleSheet(f"background-color: {ThemeColors.BG_HOVER}; color: {ThemeColors.TEXT_MUTED}; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
        m_layout.addWidget(self.status_pill)

        self.latency_pill = QLabel("0 ms")
        self.latency_pill.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-weight: 500;")
        m_layout.addWidget(self.latency_pill)

        self.size_pill = QLabel("0 B")
        self.size_pill.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-weight: 500;")
        m_layout.addWidget(self.size_pill)

        m_layout.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy_body)
        m_layout.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save...")
        self.save_btn.clicked.connect(self._save_body_to_file)
        m_layout.addWidget(self.save_btn)

        layout.addWidget(self.metrics_bar)

        # 2. Response Tabs Container
        self.tabs = QTabWidget()

        # Tab 1: Body (Pretty / Raw / Preview)
        body_page = QWidget()
        b_layout = QVBoxLayout(body_page)
        b_layout.setContentsMargins(0, 4, 0, 0)
        b_layout.setSpacing(4)

        b_subbar = QHBoxLayout()
        b_subbar.addWidget(QLabel("Format:"))
        self.body_mode_btn_pretty = QPushButton("Pretty")
        self.body_mode_btn_raw = QPushButton("Raw")
        self.body_mode_btn_preview = QPushButton("Preview")
        self.body_mode_btn_pretty.clicked.connect(lambda: self.body_stack.setCurrentIndex(0))
        self.body_mode_btn_raw.clicked.connect(lambda: self.body_stack.setCurrentIndex(1))
        self.body_mode_btn_preview.clicked.connect(lambda: self.body_stack.setCurrentIndex(2))
        b_subbar.addWidget(self.body_mode_btn_pretty)
        b_subbar.addWidget(self.body_mode_btn_raw)
        b_subbar.addWidget(self.body_mode_btn_preview)
        b_subbar.addStretch()
        b_layout.addLayout(b_subbar)

        self.body_stack = QStackedWidget()
        # Pretty mode editor
        self.pretty_editor = CodeEditor(language="json")
        self.pretty_editor.setReadOnly(True)
        self.body_stack.addWidget(self.pretty_editor)

        # Raw mode editor
        self.raw_editor = CodeEditor(language="text")
        self.raw_editor.setReadOnly(True)
        self.body_stack.addWidget(self.raw_editor)

        # Preview HTML mode
        self.preview_browser = QTextBrowser()
        self.body_stack.addWidget(self.preview_browser)

        b_layout.addWidget(self.body_stack, stretch=1)
        self.tabs.addTab(body_page, "Response Body")

        # Tab 2: Response Headers
        self.headers_table = QTableWidget(0, 2)
        self.headers_table.setHorizontalHeaderLabels(["Header", "Value"])
        self.headers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.headers_table.setColumnWidth(0, 220)
        self.headers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.headers_table.verticalHeader().setVisible(False)
        self.tabs.addTab(self.headers_table, "Headers")

        # Tab 3: Response Cookies
        self.cookies_table = QTableWidget(0, 4)
        self.cookies_table.setHorizontalHeaderLabels(["Name", "Value", "Domain", "Flags"])
        self.cookies_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cookies_table.verticalHeader().setVisible(False)
        self.tabs.addTab(self.cookies_table, "Cookies")

        # Tab 4: Timeline & SSL
        timeline_page = QWidget()
        t_layout = QVBoxLayout(timeline_page)
        self.timeline_browser = QTextBrowser()
        self.timeline_browser.setFont(QFont("JetBrains Mono", 11))
        t_layout.addWidget(self.timeline_browser)
        self.tabs.addTab(timeline_page, "Timeline & SSL")

        # Tab 5: Test Results
        self.test_results_table = QTableWidget(0, 3)
        self.test_results_table.setHorizontalHeaderLabels(["Status", "Assertion / Test Name", "Message / Duration"])
        self.test_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.test_results_table.setColumnWidth(0, 70)
        self.test_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.test_results_table.setColumnWidth(1, 200)
        self.test_results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.test_results_table.verticalHeader().setVisible(False)
        self.tabs.addTab(self.test_results_table, "Test Results")

        layout.addWidget(self.tabs, stretch=1)

        # 3. Bottom Filter Bar (JSONPath Search)
        filter_bar = QHBoxLayout()
        self.jsonpath_input = QLineEdit()
        self.jsonpath_input.setPlaceholderText("Filter JSON body with JSONPath (e.g. $.data[0].id) or text search...")
        self.jsonpath_input.returnPressed.connect(self._apply_jsonpath_filter)
        filter_bar.addWidget(self.jsonpath_input, stretch=1)
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self._apply_jsonpath_filter)
        filter_bar.addWidget(filter_btn)
        layout.addLayout(filter_bar)

    def set_response(self, response: Optional[ResponseModel]) -> None:
        """Renders response data in all viewer tabs."""
        self._current_response = response
        if not response:
            self._clear_view()
            return

        # 1. Update Status & Metrics Header
        status_col = get_status_color(response.status_code)
        if response.status_code > 0:
            self.status_pill.setText(f"{response.status_code} {response.status_text}")
            self.status_pill.setStyleSheet(f"background-color: {status_col}; color: #FFFFFF; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
        else:
            self.status_pill.setText(response.status_text or "Error")
            self.status_pill.setStyleSheet(f"background-color: {ThemeColors.STATUS_5XX}; color: #FFFFFF; font-weight: bold; border-radius: 4px; padding: 4px 8px;")

        self.latency_pill.setText(format_latency(response.timings.total_ms))
        self.size_pill.setText(format_size(response.raw_bytes_size))

        # 2. Body Viewers
        body_content = response.body
        if "json" in response.content_type.lower():
            self.pretty_editor.set_language("json")
            self.pretty_editor.setPlainText(pretty_print_json(body_content))
        elif "xml" in response.content_type.lower() or "html" in response.content_type.lower():
            self.pretty_editor.set_language("xml")
            self.pretty_editor.setPlainText(pretty_print_xml(body_content))
        else:
            self.pretty_editor.set_language("text")
            self.pretty_editor.setPlainText(body_content)

        self.raw_editor.setPlainText(body_content)
        self.preview_browser.setHtml(body_content)

        # 3. Headers
        self.headers_table.setRowCount(0)
        for h in response.headers:
            for k, v in h.items():
                r = self.headers_table.rowCount()
                self.headers_table.insertRow(r)
                self.headers_table.setItem(r, 0, QTableWidgetItem(k))
                self.headers_table.setItem(r, 1, QTableWidgetItem(v))
        self.tabs.setTabText(1, f"Headers ({len(response.headers)})")

        # 4. Cookies
        self.cookies_table.setRowCount(0)
        for c in response.cookies:
            r = self.cookies_table.rowCount()
            self.cookies_table.insertRow(r)
            self.cookies_table.setItem(r, 0, QTableWidgetItem(c.name))
            self.cookies_table.setItem(r, 1, QTableWidgetItem(c.value))
            self.cookies_table.setItem(r, 2, QTableWidgetItem(c.domain or "/"))
            flags = []
            if c.http_only:
                flags.append("HttpOnly")
            if c.secure:
                flags.append("Secure")
            self.cookies_table.setItem(r, 3, QTableWidgetItem(", ".join(flags)))
        self.tabs.setTabText(2, f"Cookies ({len(response.cookies)})")

        # 5. Timeline & SSL
        t = response.timings
        timeline_text = [
            f"=== Network Latency Timeline ===",
            f"• DNS Resolution   : {t.dns_ms:.2f} ms",
            f"• TCP Connect      : {t.tcp_ms:.2f} ms",
            f"• TLS Handshake    : {t.tls_ms:.2f} ms",
            f"• Time to 1st Byte : {t.ttfb_ms:.2f} ms",
            f"• Content Download : {t.download_ms:.2f} ms",
            f"--------------------------------",
            f"• Total Elapsed    : {t.total_ms:.2f} ms",
            "",
        ]
        if response.certificate:
            cert = response.certificate
            timeline_text.extend([
                f"=== SSL / TLS Certificate Info ===",
                f"• Subject     : {cert.subject}",
                f"• Issuer      : {cert.issuer}",
                f"• Valid From  : {cert.valid_from}",
                f"• Valid To    : {cert.valid_to}",
                f"• Cipher      : {cert.cipher}",
                f"• Protocol    : {cert.tls_version}",
            ])
        self.timeline_browser.setPlainText("\n".join(timeline_text))

        # 6. Test Results
        self.test_results_table.setRowCount(0)
        passed_count = sum(1 for tr in response.test_results if tr.passed)
        for tr in response.test_results:
            r = self.test_results_table.rowCount()
            self.test_results_table.insertRow(r)
            status_item = QTableWidgetItem("PASS" if tr.passed else "FAIL")
            status_item.setForeground(QColor(ThemeColors.STATUS_2XX if tr.passed else ThemeColors.STATUS_5XX))
            self.test_results_table.setItem(r, 0, status_item)
            self.test_results_table.setItem(r, 1, QTableWidgetItem(tr.name))
            msg = f"{tr.duration_ms:.1f}ms" if tr.passed else f"Error: {tr.error_message}"
            self.test_results_table.setItem(r, 2, QTableWidgetItem(msg))
        self.tabs.setTabText(4, f"Tests ({passed_count}/{len(response.test_results)})" if response.test_results else "Tests")

    def _clear_view(self) -> None:
        self.status_pill.setText("Ready")
        self.status_pill.setStyleSheet(f"background-color: {ThemeColors.BG_HOVER}; color: {ThemeColors.TEXT_MUTED}; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
        self.latency_pill.setText("0 ms")
        self.size_pill.setText("0 B")
        self.pretty_editor.clear()
        self.raw_editor.clear()
        self.preview_browser.clear()
        self.headers_table.setRowCount(0)
        self.cookies_table.setRowCount(0)
        self.timeline_browser.clear()
        self.test_results_table.setRowCount(0)

    def _copy_body(self) -> None:
        if self._current_response and self._current_response.body:
            QApplication.clipboard().setText(self._current_response.body)

    def _save_body_to_file(self) -> None:
        if not self._current_response or not self._current_response.body:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Response Body")
        if file_path:
            Path(file_path).write_text(self._current_response.body, encoding="utf-8")

    def _apply_jsonpath_filter(self) -> None:
        """Filters JSON response using jsonpath-ng or simple substring search."""
        query = self.jsonpath_input.text().strip()
        if not self._current_response or not self._current_response.body:
            return

        if not query:
            self.pretty_editor.setPlainText(pretty_print_json(self._current_response.body))
            return

        try:
            from jsonpath_ng import parse
            data = json.loads(self._current_response.body)
            expr = parse(query)
            matches = [m.value for m in expr.find(data)]
            self.pretty_editor.setPlainText(json.dumps(matches, indent=2))
        except Exception:
            # Fallback to plain substring line search
            matched_lines = [
                line for line in self._current_response.body.splitlines()
                if query.lower() in line.lower()
            ]
            self.pretty_editor.setPlainText("\n".join(matched_lines) if matched_lines else "No matches found.")
