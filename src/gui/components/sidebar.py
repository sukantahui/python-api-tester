"""
PyRestForge - Sidebar Collections & Request Tree with Method Badges
"""

from typing import Dict, List, Optional
from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from src.core.models.folder import FolderModel
from src.core.models.request import HttpMethod, RequestModel
from src.core.models.workspace import WorkspaceModel
from src.gui.theme import ThemeColors, get_method_color


class SidebarTreeDelegate(QStyledItemDelegate):
    """Custom item delegate for rendering HTTP Method badges and folder indicators."""

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        item_type = index.data(Qt.ItemDataRole.UserRole)  # "folder" or "request"
        rect = option.rect

        # Selection & Hover background
        if option.state & QStyledItemDelegate.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(ThemeColors.BG_SELECTED))
        elif option.state & QStyledItemDelegate.StateFlag.State_MouseOver:
            painter.fillRect(rect, QColor(ThemeColors.BG_HOVER))

        if item_type == "request":
            method = index.data(Qt.ItemDataRole.UserRole + 1) or "GET"
            name = index.data(Qt.ItemDataRole.DisplayRole) or "Request"

            # 1. Method Badge
            badge_color = QColor(get_method_color(method))
            badge_rect = QRect(rect.left() + 6, rect.top() + (rect.height() - 20) // 2, 44, 20)

            painter.setBrush(badge_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 4, 4)

            # Badge Text
            painter.setPen(QColor("#FFFFFF"))
            badge_font = QFont("Inter", 9, QFont.Weight.Bold)
            painter.setFont(badge_font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, method)

            # 2. Request Name
            text_rect = QRect(badge_rect.right() + 8, rect.top(), rect.width() - 60, rect.height())
            painter.setPen(QColor(ThemeColors.TEXT_PRIMARY))
            name_font = QFont("Inter", 10)
            painter.setFont(name_font)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

        else:
            # Folder
            name = index.data(Qt.ItemDataRole.DisplayRole) or "Folder"
            painter.setPen(QColor(ThemeColors.ACCENT_PRIMARY))
            folder_icon_font = QFont("Segoe UI Symbol", 10)
            painter.setFont(folder_icon_font)
            painter.drawText(rect.left() + 4, rect.top() + (rect.height() + 8) // 2, "📁")

            text_rect = QRect(rect.left() + 24, rect.top(), rect.width() - 30, rect.height())
            painter.setPen(QColor(ThemeColors.TEXT_PRIMARY))
            name_font = QFont("Inter", 10, QFont.Weight.DemiBold)
            painter.setFont(name_font)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        return QSize(200, 32)


class SidebarWidget(QWidget):
    """Sidebar TreeView managing workspaces, nested folders, and requests."""

    request_selected = Signal(RequestModel)
    workspace_changed = Signal(str)
    tree_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_workspace: Optional[WorkspaceModel] = None
        self._item_map: Dict[str, Any] = {}  # maps item IDs to models

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. Top Workspace Selector
        ws_row = QHBoxLayout()
        self.workspace_combo = QComboBox()
        self.workspace_combo.currentIndexChanged.connect(self._on_workspace_combo_changed)
        ws_row.addWidget(self.workspace_combo, stretch=1)

        self.add_ws_btn = QPushButton("+")
        self.add_ws_btn.setToolTip("New Workspace")
        self.add_ws_btn.setFixedWidth(28)
        self.add_ws_btn.clicked.connect(self._create_new_workspace)
        ws_row.addWidget(self.add_ws_btn)
        layout.addLayout(ws_row)

        # 2. Filter Bar & Action Buttons
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter requests (Ctrl+F)...")
        self.search_input.textChanged.connect(self._filter_tree)
        search_row.addWidget(self.search_input, stretch=1)

        self.add_req_btn = QPushButton("+ Req")
        self.add_req_btn.setToolTip("New Request (Ctrl+N)")
        self.add_req_btn.clicked.connect(self._add_root_request)
        search_row.addWidget(self.add_req_btn)

        self.add_fld_btn = QPushButton("+ Fld")
        self.add_fld_btn.setToolTip("New Folder (Ctrl+Shift+N)")
        self.add_fld_btn.clicked.connect(self._add_root_folder)
        search_row.addWidget(self.add_fld_btn)
        layout.addLayout(search_row)

        # 3. Tree View
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setItemDelegate(SidebarTreeDelegate())
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)

        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree_view, stretch=1)

    def set_workspaces_list(self, workspaces: List[Dict[str, str]], active_id: str) -> None:
        """Populates the workspace dropdown."""
        self.workspace_combo.blockSignals(True)
        self.workspace_combo.clear()
        active_idx = 0
        for i, ws in enumerate(workspaces):
            self.workspace_combo.addItem(ws["name"], ws["id"])
            if ws["id"] == active_id:
                active_idx = i
        self.workspace_combo.setCurrentIndex(active_idx)
        self.workspace_combo.blockSignals(False)

    def set_workspace(self, workspace: WorkspaceModel) -> None:
        """Populates the hierarchical tree from the WorkspaceModel."""
        self._current_workspace = workspace
        self.model.clear()
        self._item_map.clear()

        # Build Folders
        for folder in workspace.folders:
            self._add_folder_node(folder, self.model.invisibleRootItem())

        # Build Root Requests
        for req in workspace.requests:
            self._add_request_node(req, self.model.invisibleRootItem())

        self.tree_view.expandAll()

    def _add_folder_node(self, folder: FolderModel, parent_item: QStandardItem) -> QStandardItem:
        fld_item = QStandardItem(folder.name)
        fld_item.setData("folder", Qt.ItemDataRole.UserRole)
        fld_item.setData(folder.id, Qt.ItemDataRole.UserRole + 2)
        self._item_map[folder.id] = folder

        parent_item.appendRow(fld_item)

        for sub_fld in folder.folders:
            self._add_folder_node(sub_fld, fld_item)

        for req in folder.requests:
            self._add_request_node(req, fld_item)

        return fld_item

    def _add_request_node(self, req: RequestModel, parent_item: QStandardItem) -> QStandardItem:
        req_item = QStandardItem(req.name)
        req_item.setData("request", Qt.ItemDataRole.UserRole)
        req_item.setData(req.method.value, Qt.ItemDataRole.UserRole + 1)
        req_item.setData(req.id, Qt.ItemDataRole.UserRole + 2)
        self._item_map[req.id] = req

        parent_item.appendRow(req_item)
        return req_item

    def _on_item_clicked(self, index) -> None:
        item_id = index.data(Qt.ItemDataRole.UserRole + 2)
        if item_id and item_id in self._item_map:
            target = self._item_map[item_id]
            if isinstance(target, RequestModel):
                self.request_selected.emit(target)

    def _on_workspace_combo_changed(self, index: int) -> None:
        ws_id = self.workspace_combo.currentData()
        if ws_id:
            self.workspace_changed.emit(ws_id)

    def _filter_tree(self, text: str) -> None:
        """Filters tree items matching search text."""
        query = text.lower().strip()

        def match_item(item: QStandardItem) -> bool:
            name = (item.text() or "").lower()
            method = (item.data(Qt.ItemDataRole.UserRole + 1) or "").lower()
            matched = query in name or query in method

            child_matched = False
            for r in range(item.rowCount()):
                if match_item(item.child(r)):
                    child_matched = True

            visible = matched or child_matched or not query
            self.tree_view.setRowHidden(item.row(), item.parent().index() if item.parent() else self.tree_view.rootIndex(), not visible)
            return visible

        root = self.model.invisibleRootItem()
        for r in range(root.rowCount()):
            match_item(root.child(r))

    def _add_root_request(self) -> None:
        name, ok = QInputDialog.getText(self, "New Request", "Request Name:", text="New Request")
        if ok and name and self._current_workspace:
            req = RequestModel(name=name, method=HttpMethod.GET, url="{{baseUrl}}/endpoint")
            self._current_workspace.requests.append(req)
            self._add_request_node(req, self.model.invisibleRootItem())
            self.request_selected.emit(req)
            self.tree_modified.emit()

    def _add_root_folder(self) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:", text="New Folder")
        if ok and name and self._current_workspace:
            folder = FolderModel(name=name)
            self._current_workspace.folders.append(folder)
            self._add_folder_node(folder, self.model.invisibleRootItem())
            self.tree_modified.emit()

    def _create_new_workspace(self) -> None:
        name, ok = QInputDialog.getText(self, "New Workspace", "Workspace Name:")
        if ok and name:
            import uuid
            ws = WorkspaceModel(id=f"ws_{uuid.uuid4().hex[:8]}", name=name)
            from src.core.storage.workspace_store import WorkspaceStore
            WorkspaceStore().save_workspace(ws)
            self.workspace_changed.emit(ws.id)

    def _show_context_menu(self, pos: QPoint) -> None:
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            return

        item_id = index.data(Qt.ItemDataRole.UserRole + 2)
        target = self._item_map.get(item_id)
        if not target:
            return

        menu = QMenu(self)

        if isinstance(target, FolderModel):
            add_req_act = menu.addAction("Add Request in Folder")
            add_fld_act = menu.addAction("Add Subfolder")
            menu.addSeparator()
            rename_act = menu.addAction("Rename Folder")
            delete_act = menu.addAction("Delete Folder")

            action = menu.exec(self.tree_view.viewport().mapToGlobal(pos))
            if action == add_req_act:
                req_name, ok = QInputDialog.getText(self, "New Request", "Request Name:")
                if ok and req_name:
                    req = RequestModel(name=req_name, parent_id=target.id)
                    target.requests.append(req)
                    self.set_workspace(self._current_workspace)
                    self.request_selected.emit(req)
                    self.tree_modified.emit()
            elif action == rename_act:
                new_name, ok = QInputDialog.getText(self, "Rename", "Name:", text=target.name)
                if ok and new_name:
                    target.name = new_name
                    self.set_workspace(self._current_workspace)
                    self.tree_modified.emit()
            elif action == delete_act:
                if self._current_workspace and target in self._current_workspace.folders:
                    self._current_workspace.folders.remove(target)
                    self.set_workspace(self._current_workspace)
                    self.tree_modified.emit()

        elif isinstance(target, RequestModel):
            duplicate_act = menu.addAction("Duplicate")
            copy_curl_act = menu.addAction("Copy as cURL")
            menu.addSeparator()
            rename_act = menu.addAction("Rename")
            delete_act = menu.addAction("Delete")

            action = menu.exec(self.tree_view.viewport().mapToGlobal(pos))
            if action == duplicate_act:
                cloned = RequestModel.model_validate(target.model_dump())
                cloned.id = f"req_{import_uuid()}"
                cloned.name = f"{target.name} (Copy)"
                if self._current_workspace:
                    self._current_workspace.requests.append(cloned)
                    self.set_workspace(self._current_workspace)
                    self.request_selected.emit(cloned)
                    self.tree_modified.emit()
            elif action == copy_curl_act:
                from src.core.serializers.curl_parser import CodeSnippetGenerator
                curl_cmd = CodeSnippetGenerator.to_curl(target)
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(curl_cmd)
            elif action == rename_act:
                new_name, ok = QInputDialog.getText(self, "Rename Request", "Name:", text=target.name)
                if ok and new_name:
                    target.name = new_name
                    self.set_workspace(self._current_workspace)
                    self.tree_modified.emit()
            elif action == delete_act:
                if self._current_workspace:
                    if target in self._current_workspace.requests:
                        self._current_workspace.requests.remove(target)
                    for f in self._current_workspace.folders:
                        if target in f.requests:
                            f.requests.remove(target)
                    self.set_workspace(self._current_workspace)
                    self.tree_modified.emit()


def import_uuid():
    import uuid
    return uuid.uuid4().hex[:8]
