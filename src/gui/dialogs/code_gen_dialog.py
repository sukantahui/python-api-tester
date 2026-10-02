"""
PyRestForge - Multi-Language Code Snippet Generator Modal
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.core.models.request import RequestModel
from src.core.serializers.curl_parser import CodeSnippetGenerator
from src.gui.components.code_editor import CodeEditor


class CodeGenDialog(QDialog):
    """Modal displaying ready-to-use code snippets in multiple programming languages."""

    def __init__(self, request: RequestModel, parent=None):
        super().__init__(parent)
        self.request = request

        self.setWindowTitle(f"Generate Code — {request.name}")
        self.resize(680, 480)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Language Selector Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Target Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            "Python (httpx)",
            "Python (requests)",
            "cURL Command",
            "JavaScript (Fetch API)",
            "Go (net/http)",
        ])
        self.lang_combo.currentIndexChanged.connect(self._update_snippet)
        top_bar.addWidget(self.lang_combo)
        top_bar.addStretch()

        copy_btn = QPushButton("Copy Code")
        copy_btn.setObjectName("primaryButton")
        copy_btn.clicked.connect(self._copy_code)
        top_bar.addWidget(copy_btn)

        layout.addLayout(top_bar)

        # Code Editor
        self.editor = CodeEditor(language="python")
        self.editor.setReadOnly(True)
        layout.addWidget(self.editor, stretch=1)

        self._update_snippet(0)

    def _update_snippet(self, index: int) -> None:
        if index == 0:
            self.editor.set_language("python")
            self.editor.setPlainText(CodeSnippetGenerator.to_python_httpx(self.request))
        elif index == 1:
            self.editor.set_language("python")
            self.editor.setPlainText(CodeSnippetGenerator.to_python_requests(self.request))
        elif index == 2:
            self.editor.set_language("text")
            self.editor.setPlainText(CodeSnippetGenerator.to_curl(self.request))
        elif index == 3:
            self.editor.set_language("javascript")
            self.editor.setPlainText(CodeSnippetGenerator.to_javascript_fetch(self.request))
        elif index == 4:
            self.editor.set_language("go")
            self.editor.setPlainText(CodeSnippetGenerator.to_go(self.request))

    def _copy_code(self) -> None:
        QApplication.clipboard().setText(self.editor.toPlainText())
