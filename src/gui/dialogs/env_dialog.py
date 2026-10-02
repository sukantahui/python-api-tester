"""
PyRestForge - Environment Variables Management Dialog
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.models.environment import EnvVariable, SubEnvironmentModel, WorkspaceEnvironments
from src.core.models.workspace import WorkspaceModel
from src.gui.components.key_value_table import KeyValueTableWidget
from src.gui.theme import ThemeColors


class EnvironmentDialog(QDialog):
    """Modal for managing base and sub-environment variables."""

    environments_updated = Signal()

    def __init__(self, workspace: WorkspaceModel, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.setWindowTitle(f"Manage Environments — {workspace.name}")
        self.resize(720, 480)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Environments List
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Environments"))

        self.env_list = QListWidget()
        self.env_list.currentRowChanged.connect(self._on_env_selected)
        left_layout.addWidget(self.env_list)

        btn_row = QHBoxLayout()
        add_sub_btn = QPushButton("+ Sub-Env")
        add_sub_btn.clicked.connect(self._add_sub_environment)
        del_sub_btn = QPushButton("Delete")
        del_sub_btn.clicked.connect(self._delete_sub_environment)
        btn_row.addWidget(add_sub_btn)
        btn_row.addWidget(del_sub_btn)
        left_layout.addLayout(btn_row)

        splitter.addWidget(left_panel)

        # Right: Variables Table for selected env
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.env_title = QLabel("Base Environment Variables")
        self.env_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(self.env_title)

        self.var_table = KeyValueTableWidget(placeholder_key="Variable Name", placeholder_val="Variable Value")
        self.var_table.data_changed.connect(self._save_active_vars)
        right_layout.addWidget(self.var_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([200, 520])
        layout.addWidget(splitter, stretch=1)

        # Bottom Buttons
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        close_btn = QPushButton("Done")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)
        layout.addLayout(bottom_bar)

        self._populate_list()

    def _populate_list(self) -> None:
        self.env_list.clear()
        self.env_list.addItem("Base Environment (Shared)")

        for sub in self.workspace.environments.sub_environments:
            self.env_list.addItem(f"📁 {sub.name}")

        self.env_list.setCurrentRow(0)

    def _on_env_selected(self, row: int) -> None:
        if row == 0:
            self.env_title.setText("Base Environment Variables")
            self.var_table.set_items(self.workspace.environments.base_variables)
        elif row > 0:
            sub = self.workspace.environments.sub_environments[row - 1]
            self.env_title.setText(f"{sub.name} Variables")
            self.var_table.set_items(sub.variables)

    def _save_active_vars(self) -> None:
        row = self.env_list.currentRow()
        items = self.var_table.get_items()
        converted = [
            EnvVariable(key=it.key, value=it.value, description=it.description, enabled=it.active)
            for it in items
        ]

        if row == 0:
            self.workspace.environments.base_variables = converted
        elif row > 0:
            sub = self.workspace.environments.sub_environments[row - 1]
            sub.variables = converted

        self.environments_updated.emit()

    def _add_sub_environment(self) -> None:
        name, ok = QInputDialog.getText(self, "New Sub-Environment", "Environment Name (e.g. Staging):")
        if ok and name:
            new_sub = SubEnvironmentModel(name=name)
            self.workspace.environments.sub_environments.append(new_sub)
            self._populate_list()
            self.env_list.setCurrentRow(len(self.workspace.environments.sub_environments))
            self.environments_updated.emit()

    def _delete_sub_environment(self) -> None:
        row = self.env_list.currentRow()
        if row <= 0:
            QMessageBox.information(self, "Info", "Cannot delete Base Environment.")
            return

        sub = self.workspace.environments.sub_environments[row - 1]
        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete environment '{sub.name}'?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.workspace.environments.sub_environments.pop(row - 1)
            self._populate_list()
            self.env_list.setCurrentRow(0)
            self.environments_updated.emit()
