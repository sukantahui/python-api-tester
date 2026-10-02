"""
PyRestForge - Import & Export Wizard Dialog
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.models.workspace import WorkspaceModel
from src.core.serializers.curl_parser import CurlParser
from src.core.serializers.insomnia_parser import InsomniaParser
from src.core.serializers.json_serializer import JsonSerializer
from src.core.serializers.openapi_parser import OpenAPIParser
from src.core.serializers.postman_parser import PostmanParser
from src.core.serializers.yaml_serializer import YamlSerializer
from src.core.storage.workspace_store import WorkspaceStore
from src.utils.logger import logger


class ImportExportDialog(QDialog):
    """Wizard for importing and exporting YAML, JSON, OpenAPI, Insomnia, Postman, and cURL."""

    workspace_imported = Signal(WorkspaceModel)

    def __init__(self, current_workspace: WorkspaceModel, mode: str = "import", parent=None):
        super().__init__(parent)
        self.workspace = current_workspace
        self.initial_mode = mode

        self.setWindowTitle("Import / Export API Collections")
        self.resize(600, 420)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        # 1. Import Tab
        import_page = QWidget()
        imp_layout = QVBoxLayout(import_page)
        imp_layout.setSpacing(10)

        imp_layout.addWidget(QLabel("Select source format to import:"))
        self.import_format_combo = QComboBox()
        self.import_format_combo.addItems([
            "Auto-Detect Format",
            "PyRestForge YAML Collection (.yaml, .yml)",
            "PyRestForge JSON Collection (.json)",
            "OpenAPI 3.0 / 3.1 & Swagger 2.0 (YAML/JSON)",
            "Insomnia v4 Export (.json, .yaml)",
            "Postman Collection v2.1 (.json)",
            "Raw cURL Command String",
        ])
        imp_layout.addWidget(self.import_format_combo)

        imp_layout.addWidget(QLabel("Paste raw YAML / JSON / cURL content below, or choose a file:"))
        self.import_text = QPlainTextEdit()
        self.import_text.setPlaceholderText("Paste raw YAML, JSON, or curl command here...")
        imp_layout.addWidget(self.import_text, stretch=1)

        imp_btn_row = QHBoxLayout()
        browse_file_btn = QPushButton("Import from File...")
        browse_file_btn.clicked.connect(self._import_from_file)
        imp_btn_row.addWidget(browse_file_btn)

        imp_btn_row.addStretch()

        process_imp_btn = QPushButton("Import Content")
        process_imp_btn.setObjectName("primaryButton")
        process_imp_btn.clicked.connect(self._import_from_text)
        imp_btn_row.addWidget(process_imp_btn)
        imp_layout.addLayout(imp_btn_row)

        self.tabs.addTab(import_page, "Import Collections")

        # 2. Export Tab
        export_page = QWidget()
        exp_layout = QVBoxLayout(export_page)
        exp_layout.setSpacing(12)

        exp_layout.addWidget(QLabel(f"Export active workspace: <b>{self.workspace.name}</b>"))

        exp_layout.addWidget(QLabel("Export Format:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems([
            "PyRestForge Native YAML (.yaml)",
            "PyRestForge Native JSON (.json)",
            "OpenAPI 3.1 Specification (.yaml)",
            "Insomnia v4 Export (.json)",
            "Postman Collection v2.1 (.json)",
        ])
        exp_layout.addWidget(self.export_format_combo)

        self.strip_secrets_cb = QCheckBox("Mask / Exclude sensitive environment secrets")
        self.strip_secrets_cb.setChecked(True)
        exp_layout.addWidget(self.strip_secrets_cb)

        exp_layout.addStretch()

        exp_btn_row = QHBoxLayout()
        exp_btn_row.addStretch()
        export_btn = QPushButton("Export to File...")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self._export_to_file)
        exp_btn_row.addWidget(export_btn)
        exp_layout.addLayout(exp_btn_row)

        self.tabs.addTab(export_page, "Export Collection")

        layout.addWidget(self.tabs)

        if self.initial_mode == "export":
            self.tabs.setCurrentIndex(1)

    def _import_from_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select API Collection File",
            filter="API Collections (*.yaml *.yml *.json);;All Files (*.*)"
        )
        if not file_path:
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8")
            self._parse_and_load_content(content)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to read file: {e}")

    def _import_from_text(self) -> None:
        text = self.import_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please paste content to import or select a file.")
            return

        self._parse_and_load_content(text)

    def _parse_and_load_content(self, content: str) -> None:
        fmt_idx = self.import_format_combo.currentIndex()
        imported_ws: Optional[WorkspaceModel] = None

        try:
            # cURL command
            if content.startswith("curl ") or fmt_idx == 6:
                req = CurlParser.parse_curl(content)
                self.workspace.requests.append(req)
                WorkspaceStore().save_workspace(self.workspace)
                self.workspace_imported.emit(self.workspace)
                QMessageBox.information(self, "Success", "cURL request successfully imported!")
                self.accept()
                return

            # Auto detect or explicit format
            if fmt_idx == 1 or ("schema_version" in content and "workspace:" in content):
                imported_ws = YamlSerializer().deserialize_workspace(content)
            elif fmt_idx == 2 or ("schema_version" in content and '"workspace"' in content):
                imported_ws = JsonSerializer().deserialize_workspace(content)
            elif fmt_idx == 3 or ("openapi:" in content or '"openapi"' in content or "swagger:" in content):
                imported_ws = OpenAPIParser.import_spec(content)
            elif fmt_idx == 4 or ('"_type": "export"' in content or "_type: export" in content):
                imported_ws = InsomniaParser.import_insomnia(content)
            elif fmt_idx == 5 or ('schema.getpostman.com' in content or '"item"' in content):
                imported_ws = PostmanParser.import_postman(content)
            else:
                # Fallback trial
                try:
                    imported_ws = YamlSerializer().deserialize_workspace(content)
                except Exception:
                    imported_ws = OpenAPIParser.import_spec(content)

            if imported_ws:
                WorkspaceStore().save_workspace(imported_ws)
                self.workspace_imported.emit(imported_ws)
                QMessageBox.information(self, "Success", f"Successfully imported workspace: '{imported_ws.name}'!")
                self.accept()

        except Exception as e:
            logger.error(f"Import parsing failed: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to parse collection format: {e}")

    def _export_to_file(self) -> None:
        idx = self.export_format_combo.currentIndex()
        strip_secrets = self.strip_secrets_cb.isChecked()

        ext_map = {
            0: ("PyRestForge YAML (*.yaml)", ".yaml"),
            1: ("PyRestForge JSON (*.json)", ".json"),
            2: ("OpenAPI 3.1 YAML (*.yaml)", ".yaml"),
            3: ("Insomnia Export (*.json)", ".json"),
            4: ("Postman Collection (*.json)", ".json"),
        }

        flt, default_ext = ext_map.get(idx, ("YAML (*.yaml)", ".yaml"))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Exported Collection",
            f"{self.workspace.name.lower().replace(' ', '_')}{default_ext}",
            flt
        )
        if not file_path:
            return

        try:
            content = ""
            if idx == 0:
                content = YamlSerializer().serialize_workspace(self.workspace, strip_secrets=strip_secrets)
            elif idx == 1:
                content = JsonSerializer().serialize_workspace(self.workspace, pretty=True, strip_secrets=strip_secrets)
            elif idx == 2:
                content = OpenAPIParser.export_spec(self.workspace, as_yaml=True)
            elif idx == 3:
                content = InsomniaParser.export_insomnia(self.workspace)
            elif idx == 4:
                content = PostmanParser.export_postman(self.workspace)

            Path(file_path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Collection successfully saved to:\n{file_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export collection: {e}")
