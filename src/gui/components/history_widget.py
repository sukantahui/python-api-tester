"""
PyRestForge - Execution History Drawer Component
"""

import time
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.models.history import HistoryEntryModel
from src.core.storage.history_store import HistoryStore
from src.gui.theme import ThemeColors, get_method_color, get_status_color
from src.utils.formatters import format_latency, format_size


class HistoryWidget(QWidget):
    """Drawer displaying historical request executions."""

    history_item_selected = Signal(HistoryEntryModel)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_store = HistoryStore()
        self._entries: List[HistoryEntryModel] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.addWidget(QLabel("Execution History"))
        header.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_history)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Method", "Status", "Request / URL", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 60)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table, stretch=1)

    def load_history(self, workspace_id: str) -> None:
        """Loads execution history for workspace."""
        self._entries = self.history_store.get_history_for_workspace(workspace_id)
        self.table.setRowCount(0)

        for entry in self._entries:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Method
            m_item = QTableWidgetItem(entry.method)
            m_item.setForeground(QColor(get_method_color(entry.method)))
            m_item.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            self.table.setItem(r, 0, m_item)

            # Status
            s_item = QTableWidgetItem(str(entry.status_code) if entry.status_code else "ERR")
            s_item.setForeground(QColor(get_status_color(entry.status_code)))
            self.table.setItem(r, 1, s_item)

            # Name / URL
            desc = f"{entry.request_name} ({entry.url})"
            self.table.setItem(r, 2, QTableWidgetItem(desc))

            # Latency / Time
            lat_desc = format_latency(entry.duration_ms)
            self.table.setItem(r, 3, QTableWidgetItem(lat_desc))

    def clear_history(self) -> None:
        self.history_store.clear_history()
        self.table.setRowCount(0)
        self._entries.clear()

    def _on_cell_clicked(self, row: int, _) -> None:
        if 0 <= row < len(self._entries):
            self.history_item_selected.emit(self._entries[row])
