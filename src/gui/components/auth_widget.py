"""
PyRestForge - Authentication Configuration Widget
"""

from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.models.auth import ApiKeyLocation, AuthConfig, AuthType, OAuth2GrantType
from src.core.models.request import RequestModel


class AuthWidget(QWidget):
    """Configuration panel for request authentication."""

    auth_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_request: Optional[RequestModel] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Top Auth Type selector
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Auth Type:"))
        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItems([
            "No Auth",
            "Bearer Token",
            "Basic Auth",
            "API Key",
            "OAuth 2.0",
        ])
        self.auth_type_combo.currentIndexChanged.connect(self._on_type_changed)
        top_row.addWidget(self.auth_type_combo)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.stack = QStackedWidget()

        # 0. No Auth
        no_auth_page = QWidget()
        no_auth_layout = QVBoxLayout(no_auth_page)
        lbl = QLabel("No authentication will be attached to this request.")
        lbl.setStyleSheet("color: #94A3B8;")
        no_auth_layout.addWidget(lbl)
        no_auth_layout.addStretch()
        self.stack.addWidget(no_auth_page)

        # 1. Bearer Token
        bearer_page = QWidget()
        bearer_layout = QFormLayout(bearer_page)
        self.bearer_token_input = QLineEdit()
        self.bearer_token_input.setPlaceholderText("eyJhbGciOi... or {{jwt_token}}")
        self.bearer_token_input.textChanged.connect(self._on_field_changed)
        self.bearer_prefix_input = QLineEdit("Bearer")
        self.bearer_prefix_input.textChanged.connect(self._on_field_changed)
        bearer_layout.addRow("Token:", self.bearer_token_input)
        bearer_layout.addRow("Prefix:", self.bearer_prefix_input)
        self.stack.addWidget(bearer_page)

        # 2. Basic Auth
        basic_page = QWidget()
        basic_layout = QFormLayout(basic_page)
        self.basic_user_input = QLineEdit()
        self.basic_user_input.setPlaceholderText("username or {{user}}")
        self.basic_user_input.textChanged.connect(self._on_field_changed)
        self.basic_pwd_input = QLineEdit()
        self.basic_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.basic_pwd_input.setPlaceholderText("password")
        self.basic_pwd_input.textChanged.connect(self._on_field_changed)
        basic_layout.addRow("Username:", self.basic_user_input)
        basic_layout.addRow("Password:", self.basic_pwd_input)
        self.stack.addWidget(basic_page)

        # 3. API Key
        apikey_page = QWidget()
        apikey_layout = QFormLayout(apikey_page)
        self.apikey_name_input = QLineEdit("X-Api-Key")
        self.apikey_name_input.textChanged.connect(self._on_field_changed)
        self.apikey_val_input = QLineEdit()
        self.apikey_val_input.setPlaceholderText("value or {{api_key}}")
        self.apikey_val_input.textChanged.connect(self._on_field_changed)
        self.apikey_loc_combo = QComboBox()
        self.apikey_loc_combo.addItems(["Header", "Query Params"])
        self.apikey_loc_combo.currentIndexChanged.connect(self._on_field_changed)
        apikey_layout.addRow("Key Name:", self.apikey_name_input)
        apikey_layout.addRow("Key Value:", self.apikey_val_input)
        apikey_layout.addRow("Add To:", self.apikey_loc_combo)
        self.stack.addWidget(apikey_page)

        # 4. OAuth 2.0
        oauth_page = QWidget()
        oauth_layout = QFormLayout(oauth_page)
        self.oauth_url_input = QLineEdit()
        self.oauth_url_input.setPlaceholderText("https://auth.example.com/oauth/token")
        self.oauth_url_input.textChanged.connect(self._on_field_changed)
        self.oauth_client_id = QLineEdit()
        self.oauth_client_id.textChanged.connect(self._on_field_changed)
        self.oauth_client_secret = QLineEdit()
        self.oauth_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.oauth_client_secret.textChanged.connect(self._on_field_changed)
        self.oauth_token_input = QLineEdit()
        self.oauth_token_input.setPlaceholderText("Access token or click Fetch Token")
        self.oauth_token_input.textChanged.connect(self._on_field_changed)
        oauth_layout.addRow("Access Token URL:", self.oauth_url_input)
        oauth_layout.addRow("Client ID:", self.oauth_client_id)
        oauth_layout.addRow("Client Secret:", self.oauth_client_secret)
        oauth_layout.addRow("Current Token:", self.oauth_token_input)
        self.stack.addWidget(oauth_page)

        layout.addWidget(self.stack, stretch=1)

    def set_request(self, request: RequestModel) -> None:
        self._current_request = request
        auth = request.auth

        self.auth_type_combo.blockSignals(True)
        if auth.type == AuthType.BEARER:
            self.auth_type_combo.setCurrentIndex(1)
            self.stack.setCurrentIndex(1)
            self.bearer_token_input.setText(auth.bearer_token or "")
            self.bearer_prefix_input.setText(auth.bearer_prefix or "Bearer")
        elif auth.type == AuthType.BASIC:
            self.auth_type_combo.setCurrentIndex(2)
            self.stack.setCurrentIndex(2)
            self.basic_user_input.setText(auth.basic_username or "")
            self.basic_pwd_input.setText(auth.basic_password or "")
        elif auth.type == AuthType.API_KEY:
            self.auth_type_combo.setCurrentIndex(3)
            self.stack.setCurrentIndex(3)
            self.apikey_name_input.setText(auth.api_key_name or "X-Api-Key")
            self.apikey_val_input.setText(auth.api_key_value or "")
            self.apikey_loc_combo.setCurrentIndex(0 if auth.api_key_location == ApiKeyLocation.HEADER else 1)
        elif auth.type == AuthType.OAUTH2:
            self.auth_type_combo.setCurrentIndex(4)
            self.stack.setCurrentIndex(4)
            self.oauth_url_input.setText(auth.oauth2_access_token_url or "")
            self.oauth_client_id.setText(auth.oauth2_client_id or "")
            self.oauth_client_secret.setText(auth.oauth2_client_secret or "")
            self.oauth_token_input.setText(auth.oauth2_access_token or "")
        else:
            self.auth_type_combo.setCurrentIndex(0)
            self.stack.setCurrentIndex(0)
        self.auth_type_combo.blockSignals(False)

    def _on_type_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if not self._current_request:
            return

        type_map = [AuthType.NONE, AuthType.BEARER, AuthType.BASIC, AuthType.API_KEY, AuthType.OAUTH2]
        self._current_request.auth.type = type_map[index]
        self.auth_changed.emit()

    def _on_field_changed(self) -> None:
        if not self._current_request:
            return

        auth = self._current_request.auth
        idx = self.stack.currentIndex()

        if idx == 1:
            auth.bearer_token = self.bearer_token_input.text()
            auth.bearer_prefix = self.bearer_prefix_input.text()
        elif idx == 2:
            auth.basic_username = self.basic_user_input.text()
            auth.basic_password = self.basic_pwd_input.text()
        elif idx == 3:
            auth.api_key_name = self.apikey_name_input.text()
            auth.api_key_value = self.apikey_val_input.text()
            auth.api_key_location = ApiKeyLocation.HEADER if self.apikey_loc_combo.currentIndex() == 0 else ApiKeyLocation.QUERY
        elif idx == 4:
            auth.oauth2_access_token_url = self.oauth_url_input.text()
            auth.oauth2_client_id = self.oauth_client_id.text()
            auth.oauth2_client_secret = self.oauth_client_secret.text()
            auth.oauth2_access_token = self.oauth_token_input.text()

        self.auth_changed.emit()
