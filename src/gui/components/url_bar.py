"""
PyRestForge - URL Bar & Method Selector Component
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from src.core.models.request import HttpMethod, RequestModel
from src.gui.theme import ThemeColors, get_method_color


class UrlBarWidget(QWidget):
    """Insomnia-style URL Bar with Method Picker and Send / Cancel controls."""

    send_clicked = Signal()
    cancel_clicked = Signal()
    request_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_request: Optional[RequestModel] = None
        self._is_sending = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. Method Selector
        self.method_combo = QComboBox()
        for m in HttpMethod:
            self.method_combo.addItem(m.value)
        self.method_combo.setFixedWidth(100)
        self.method_combo.currentTextChanged.connect(self._on_method_changed)
        layout.addWidget(self.method_combo)

        # 2. URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.example.com/v1/resource or {{baseUrl}}/endpoint")
        self.url_input.textChanged.connect(self._on_url_changed)
        self.url_input.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self.url_input, stretch=1)

        # 3. Send / Cancel Button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedWidth(100)
        self.send_btn.setShortcut(Qt.Key.Key_Return | Qt.KeyboardModifier.ControlModifier)
        self.send_btn.clicked.connect(self._on_button_clicked)
        layout.addWidget(self.send_btn)

        self._update_method_style("GET")

    def set_request(self, request: RequestModel) -> None:
        """Loads request details into URL Bar."""
        self._current_request = request
        self.method_combo.blockSignals(True)
        self.url_input.blockSignals(True)

        self.method_combo.setCurrentText(request.method.value)
        self.url_input.setText(request.url)
        self._update_method_style(request.method.value)

        self.method_combo.blockSignals(False)
        self.url_input.blockSignals(False)

    def set_in_flight(self, in_flight: bool) -> None:
        """Updates button to Cancel or Send during execution."""
        self._is_sending = in_flight
        if in_flight:
            self.send_btn.setText("Cancel")
            self.send_btn.setObjectName("cancelButton")
        else:
            self.send_btn.setText("Send")
            self.send_btn.setObjectName("sendButton")
        self.send_btn.style().unpolish(self.send_btn)
        self.send_btn.style().polish(self.send_btn)

    def _on_method_changed(self, method_text: str) -> None:
        self._update_method_style(method_text)
        if self._current_request:
            self._current_request.method = HttpMethod(method_text)
            self.request_modified.emit()

    def _on_url_changed(self, url_text: str) -> None:
        if self._current_request:
            self._current_request.url = url_text
            self.request_modified.emit()

    def _on_button_clicked(self) -> None:
        if self._is_sending:
            self.cancel_clicked.emit()
        else:
            self.send_clicked.emit()

    def _on_return_pressed(self) -> None:
        if not self._is_sending:
            self.send_clicked.emit()

    def _update_method_style(self, method: str) -> None:
        color = get_method_color(method)
        self.method_combo.setStyleSheet(f"""
            QComboBox {{
                color: {color};
                font-weight: bold;
                border: 1px solid {ThemeColors.BORDER_SUBTLE};
                padding: 6px 10px;
            }}
        """)
