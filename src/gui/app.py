"""
PyRestForge - Main Application Window & Primary Orchestration (PySide6)
"""

import sys
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.engine.http_client import AsyncHttpEngine
from src.core.engine.interpolator import VariableInterpolator
from src.core.models.request import RequestModel
from src.core.models.response import ResponseModel
from src.core.models.workspace import WorkspaceModel
from src.gui.components.history_widget import HistoryWidget
from src.gui.components.request_tabs import RequestTabsWidget
from src.gui.components.response_viewer import ResponseViewerWidget
from src.gui.components.sidebar import SidebarWidget
from src.gui.components.url_bar import UrlBarWidget
from src.gui.dialogs.code_gen_dialog import CodeGenDialog
from src.gui.dialogs.env_dialog import EnvironmentDialog
from src.gui.dialogs.import_export import ImportExportDialog
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.state import AppState
from src.gui.theme import DARK_STYLESHEET, ThemeColors
from src.utils.logger import logger


class WorkerSignals(QObject):
    finished = Signal(object, dict)  # ResponseModel, mutated_env_vars
    error = Signal(str)


class HttpRequestWorker(QRunnable):
    """Background worker for dispatching network requests off the Qt main thread."""

    def __init__(self, engine: AsyncHttpEngine, request: RequestModel, env_vars: Dict[str, Any]):
        super().__init__()
        self.engine = engine
        self.request = request
        self.env_vars = env_vars
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            response, mutated_vars = self.engine.send_sync(self.request, self.env_vars)
            self.signals.finished.emit(response, mutated_vars)
        except Exception as e:
            logger.error(f"HTTP Worker encountered error: {e}")
            self.signals.error.emit(str(e))


class MainWindow(QMainWindow):
    """Primary Insomnia-grade Desktop API Testing Studio Window."""

    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.thread_pool = QThreadPool.globalInstance()
        self.http_engine = AsyncHttpEngine()

        self.setWindowTitle("PyRestForge — Desktop API Testing Studio")
        self.resize(1360, 850)
        self.setMinimumSize(950, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self._init_ui()
        self._connect_signals()

        # Initial data sync
        if self.state.current_workspace:
            self._on_workspace_loaded(self.state.current_workspace)

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Global Navigation Header Toolbar
        self._create_header_toolbar(root_layout)

        # 2. Main Three-Pane Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Pane: Sidebar Collections & Folders Tree
        self.sidebar = SidebarWidget()
        self.main_splitter.addWidget(self.sidebar)

        # Center Pane: Request Builder (URL Bar + Tabs)
        center_panel = QWidget()
        c_layout = QVBoxLayout(center_panel)
        c_layout.setContentsMargins(8, 8, 8, 8)
        c_layout.setSpacing(8)

        self.url_bar = UrlBarWidget()
        c_layout.addWidget(self.url_bar)

        self.request_tabs = RequestTabsWidget()
        c_layout.addWidget(self.request_tabs, stretch=1)
        self.main_splitter.addWidget(center_panel)

        # Right Pane: Response Inspector
        self.response_viewer = ResponseViewerWidget()
        self.main_splitter.addWidget(self.response_viewer)

        # Drawer Pane: History Panel (Collapsible)
        self.history_widget = HistoryWidget()
        self.history_widget.setVisible(False)
        self.main_splitter.addWidget(self.history_widget)

        # Proportional pane sizes (Sidebar: 280px, Builder: 540px, Response: 540px)
        self.main_splitter.setSizes([280, 540, 540, 0])
        root_layout.addWidget(self.main_splitter, stretch=1)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready • HTTP/2 Enabled • SSL Verification Active")

        # Shortcuts
        self._init_shortcuts()

    def _create_header_toolbar(self, parent_layout: QVBoxLayout) -> None:
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background-color: {ThemeColors.BG_SIDEBAR}; border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE}; padding: 6px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(12, 4, 12, 4)
        t_layout.setSpacing(10)

        # App Brand Title
        brand_lbl = QLabel("PyRestForge")
        brand_lbl.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        brand_lbl.setStyleSheet(f"color: {ThemeColors.ACCENT_PRIMARY}; margin-right: 12px;")
        t_layout.addWidget(brand_lbl)

        # Environment Selector
        t_layout.addWidget(QLabel("Environment:"))
        self.env_combo = QComboBox()
        self.env_combo.setMinimumWidth(160)
        self.env_combo.currentIndexChanged.connect(self._on_env_combo_changed)
        t_layout.addWidget(self.env_combo)

        env_manage_btn = QPushButton("Manage Envs")
        env_manage_btn.clicked.connect(self._open_env_dialog)
        t_layout.addWidget(env_manage_btn)

        t_layout.addStretch()

        # Action Buttons
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self._open_import_dialog)
        t_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._open_export_dialog)
        t_layout.addWidget(self.export_btn)

        self.codegen_btn = QPushButton("Generate Code")
        self.codegen_btn.clicked.connect(self._open_codegen_dialog)
        t_layout.addWidget(self.codegen_btn)

        self.history_toggle_btn = QPushButton("History")
        self.history_toggle_btn.clicked.connect(self._toggle_history_drawer)
        t_layout.addWidget(self.history_toggle_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setToolTip("Settings")
        settings_btn.setFixedWidth(32)
        settings_btn.clicked.connect(self._open_settings_dialog)
        t_layout.addWidget(settings_btn)

        parent_layout.addWidget(toolbar)

    def _init_shortcuts(self) -> None:
        """Configures application hotkeys."""
        # Ctrl+I: Import
        import_act = QAction(self)
        import_act.setShortcut(QKeySequence("Ctrl+I"))
        import_act.triggered.connect(self._open_import_dialog)
        self.addAction(import_act)

        # Ctrl+Shift+E: Export
        export_act = QAction(self)
        export_act.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_act.triggered.connect(self._open_export_dialog)
        self.addAction(export_act)

        # Ctrl+E: Environments
        env_act = QAction(self)
        env_act.setShortcut(QKeySequence("Ctrl+E"))
        env_act.triggered.connect(self._open_env_dialog)
        self.addAction(env_act)

    def _connect_signals(self) -> None:
        # App state events
        self.state.workspace_loaded.connect(self._on_workspace_loaded)
        self.state.active_request_changed.connect(self._on_request_changed)
        self.state.status_message_updated.connect(self.status_bar.showMessage)

        # Sidebar events
        self.sidebar.request_selected.connect(self.state.select_request)
        self.sidebar.workspace_changed.connect(self.state.load_workspace)
        self.sidebar.tree_modified.connect(self.state.save_current_workspace)

        # URL Bar & Request Tabs events
        self.url_bar.send_clicked.connect(self._execute_request)
        self.url_bar.request_modified.connect(self._on_request_edited)
        self.request_tabs.request_modified.connect(self._on_request_edited)

        # History events
        self.history_widget.history_item_selected.connect(self._on_history_item_selected)

    def _on_workspace_loaded(self, workspace: WorkspaceModel) -> None:
        # Refresh sidebar
        workspaces = self.state.workspace_store.list_workspaces()
        self.sidebar.set_workspaces_list(workspaces, workspace.id)
        self.sidebar.set_workspace(workspace)

        # Refresh Environment Combo
        self._refresh_environment_dropdown()

        # Refresh History
        self.history_widget.load_history(workspace.id)

        # Set active request
        if self.state.current_request:
            self._on_request_changed(self.state.current_request)

    def _on_request_changed(self, request: RequestModel) -> None:
        self.url_bar.set_request(request)
        self.request_tabs.set_request(request)
        self.response_viewer.set_response(None)

    def _on_request_edited(self) -> None:
        self.state.save_current_workspace()

    def _refresh_environment_dropdown(self) -> None:
        if not self.state.current_workspace:
            return

        self.env_combo.blockSignals(True)
        self.env_combo.clear()
        self.env_combo.addItem("No Sub-Environment", "")

        active_idx = 0
        for i, sub in enumerate(self.state.current_workspace.environments.sub_environments):
            self.env_combo.addItem(f"🌍 {sub.name}", sub.id)
            if sub.id == self.state.active_sub_env_id or sub.name == self.state.active_sub_env_id:
                active_idx = i + 1

        self.env_combo.setCurrentIndex(active_idx)
        self.env_combo.blockSignals(False)

    def _on_env_combo_changed(self, index: int) -> None:
        env_id = self.env_combo.currentData()
        self.state.set_active_environment(env_id)

    def _execute_request(self) -> None:
        if not self.state.current_request or not self.state.current_workspace:
            return

        self.url_bar.set_in_flight(True)
        self.status_bar.showMessage("Sending request...")

        # 1. Resolve Variables with Active Environment
        interpolator = VariableInterpolator.from_workspace_environments(
            self.state.current_workspace.environments,
            active_sub_env_id=self.state.active_sub_env_id
        )
        interpolated_req = interpolator.interpolate_request(self.state.current_request)

        # 2. Dispatch to QThreadPool Worker
        worker = HttpRequestWorker(
            engine=self.http_engine,
            request=interpolated_req,
            env_vars=interpolator.context
        )
        worker.signals.finished.connect(self._on_request_finished)
        worker.signals.error.connect(self._on_request_error)
        self.thread_pool.start(worker)

    def _on_request_finished(self, response: ResponseModel, mutated_env_vars: Dict[str, Any]) -> None:
        self.url_bar.set_in_flight(False)
        self.response_viewer.set_response(response)

        # If scripts mutated variables, update active workspace environment
        if mutated_env_vars and self.state.current_workspace:
            for k, v in mutated_env_vars.items():
                # Update or add to base variables
                found = False
                for b_var in self.state.current_workspace.environments.base_variables:
                    if b_var.key == k:
                        b_var.value = str(v)
                        found = True
                        break
                if not found:
                    from src.core.models.environment import EnvVariable
                    self.state.current_workspace.environments.base_variables.append(
                        EnvVariable(key=k, value=str(v))
                    )
            self.state.save_current_workspace()

        # Record History
        self.state.record_history(response)
        if self.state.current_workspace:
            self.history_widget.load_history(self.state.current_workspace.id)

        self.status_bar.showMessage(f"Response received: {response.status_code} {response.status_text} in {response.timings.total_ms:.1f}ms")

    def _on_request_error(self, err_msg: str) -> None:
        self.url_bar.set_in_flight(False)
        self.status_bar.showMessage(f"Request error: {err_msg}")
        QMessageBox.critical(self, "Network Error", f"Failed to execute request:\n{err_msg}")

    def _on_history_item_selected(self, entry) -> None:
        self.response_viewer.set_response(entry.response_snapshot)

    def _toggle_history_drawer(self) -> None:
        is_vis = self.history_widget.isVisible()
        self.history_widget.setVisible(not is_vis)
        if not is_vis and self.state.current_workspace:
            self.history_widget.load_history(self.state.current_workspace.id)

    def _open_env_dialog(self) -> None:
        if not self.state.current_workspace:
            return
        dlg = EnvironmentDialog(self.state.current_workspace, self)
        dlg.environments_updated.connect(lambda: (
            self.state.save_current_workspace(),
            self._refresh_environment_dropdown()
        ))
        dlg.exec()

    def _open_import_dialog(self) -> None:
        if not self.state.current_workspace:
            return
        dlg = ImportExportDialog(self.state.current_workspace, mode="import", parent=self)
        dlg.workspace_imported.connect(lambda ws: self.state.load_workspace(ws.id))
        dlg.exec()

    def _open_export_dialog(self) -> None:
        if not self.state.current_workspace:
            return
        dlg = ImportExportDialog(self.state.current_workspace, mode="export", parent=self)
        dlg.exec()

    def _open_codegen_dialog(self) -> None:
        if not self.state.current_request:
            QMessageBox.information(self, "Info", "Please select a request first.")
            return
        dlg = CodeGenDialog(self.state.current_request, self)
        dlg.exec()

    def _open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()
