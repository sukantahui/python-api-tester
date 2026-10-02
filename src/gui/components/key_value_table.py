"""
PyRestForge - Key-Value-Description Table Component with Bulk Edit
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.models.request import KeyValueItem
from src.gui.theme import ThemeColors


class KeyValueTableWidget(QWidget):
    """Reusable Key-Value-Description table with active toggles and bulk edit."""

    data_changed = Signal()

    def __init__(self, parent=None, placeholder_key="Key", placeholder_val="Value", allow_bulk: bool = True):
        super().__init__(parent)
        self.placeholder_key = placeholder_key
        self.placeholder_val = placeholder_val
        self.allow_bulk = allow_bulk
        self._is_bulk_mode = False

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header bar with Actions & Bulk Edit Toggle
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        self.add_btn = QPushButton("+ Add Row")
        self.add_btn.clicked.connect(self.add_empty_row)
        top_bar.addWidget(self.add_btn)

        if self.allow_bulk:
            self.bulk_btn = QPushButton("Bulk Edit")
            self.bulk_btn.clicked.connect(self.toggle_bulk_mode)
            top_bar.addWidget(self.bulk_btn)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        self.stack = QStackedWidget()

        # 1. Table View
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", self.placeholder_key, self.placeholder_val, "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 36)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 160)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 140)
        self.table.verticalHeader().setVisible(False)
        self.table.cellChanged.connect(self._on_cell_changed)
        self.stack.addWidget(self.table)

        # 2. Bulk Text View
        self.bulk_edit = QPlainTextEdit()
        self.bulk_edit.setPlaceholderText("key: value\n# or query params\nkey=value")
        self.bulk_edit.textChanged.connect(self._on_bulk_text_changed)
        self.stack.addWidget(self.bulk_edit)

        layout.addWidget(self.stack)

    def set_items(self, items: List[KeyValueItem]) -> None:
        """Populates the table with items."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for item in items:
            self._insert_row(item.key, item.value, item.description or "", item.active)

        if not items:
            self._insert_row("", "", "", True)

        self.table.blockSignals(False)

    def get_items(self) -> List[KeyValueItem]:
        """Extracts items from the active view."""
        if self._is_bulk_mode:
            self._sync_bulk_to_table()

        items: List[KeyValueItem] = []
        for r in range(self.table.rowCount()):
            cb_widget = self.table.cellWidget(r, 0)
            active = True
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb:
                    active = cb.isChecked()

            key_item = self.table.item(r, 1)
            val_item = self.table.item(r, 2)
            desc_item = self.table.item(r, 3)

            k = key_item.text().strip() if key_item else ""
            v = val_item.text().strip() if val_item else ""
            d = desc_item.text().strip() if desc_item else ""

            if k or v:
                items.append(KeyValueItem(key=k, value=v, description=d, active=active))

        return items

    def _insert_row(self, key: str, value: str, desc: str, active: bool) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Checkbox cell
        cb_container = QWidget()
        cb_layout = QHBoxLayout(cb_container)
        cb_layout.setContentsMargins(8, 0, 0, 0)
        cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cb = QCheckBox()
        cb.setChecked(active)
        cb.stateChanged.connect(lambda: self.data_changed.emit())
        cb_layout.addWidget(cb)
        self.table.setCellWidget(row, 0, cb_container)

        # Key, Value, Description items
        self.table.setItem(row, 1, QTableWidgetItem(key))
        self.table.setItem(row, 2, QTableWidgetItem(value))
        self.table.setItem(row, 3, QTableWidgetItem(desc))
        return row

    def add_empty_row(self) -> None:
        self.table.blockSignals(True)
        self._insert_row("", "", "", True)
        self.table.blockSignals(False)
        self.table.setCurrentCell(self.table.rowCount() - 1, 1)
        self.data_changed.emit()

    def _on_cell_changed(self, row: int, col: int) -> None:
        # If user typed in the last row, auto-add a new empty row
        if row == self.table.rowCount() - 1:
            item = self.table.item(row, col)
            if item and item.text().strip():
                self.table.blockSignals(True)
                self._insert_row("", "", "", True)
                self.table.blockSignals(False)

        self.data_changed.emit()

    def toggle_bulk_mode(self) -> None:
        if not self._is_bulk_mode:
            # Switch to Bulk Edit
            items = self.get_items()
            lines = [f"{it.key}: {it.value}" for it in items if it.key]
            self.bulk_edit.blockSignals(True)
            self.bulk_edit.setPlainText("\n".join(lines))
            self.bulk_edit.blockSignals(False)
            self.stack.setCurrentIndex(1)
            self.bulk_btn.setText("Table View")
            self._is_bulk_mode = True
        else:
            # Switch back to Table View
            self._sync_bulk_to_table()
            self.stack.setCurrentIndex(0)
            self.bulk_btn.setText("Bulk Edit")
            self._is_bulk_mode = False

    def _sync_bulk_to_table(self) -> None:
        lines = self.bulk_edit.toPlainText().splitlines()
        items: List[KeyValueItem] = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                items.append(KeyValueItem(key=k.strip(), value=v.strip(), active=True))
            elif "=" in line:
                k, v = line.split("=", 1)
                items.append(KeyValueItem(key=k.strip(), value=v.strip(), active=True))
            else:
                items.append(KeyValueItem(key=line, value="", active=True))
        self.set_items(items)

    def _on_bulk_text_changed(self) -> None:
        self.data_changed.emit()
