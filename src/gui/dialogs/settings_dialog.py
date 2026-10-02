"""
PyRestForge - Application Settings Dialog
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.core.storage.config_store import ConfigStore, UserConfig


class SettingsDialog(QDialog):
    """Application preferences configuration modal."""

    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_store = ConfigStore()
        self.config: UserConfig = self.config_store.get_config()

        self.setWindowTitle("Preferences & Settings")
        self.resize(480, 320)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()

        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(int(self.config.default_timeout))
        form.addRow("Default Timeout (seconds):", self.timeout_spin)

        # SSL Verify
        self.ssl_cb = QCheckBox("Validate SSL / TLS Certificates")
        self.ssl_cb.setChecked(self.config.validate_ssl)
        form.addRow("SSL Verification:", self.ssl_cb)

        # Redirects
        self.redirects_cb = QCheckBox("Automatically follow HTTP redirects")
        self.redirects_cb.setChecked(self.config.follow_redirects)
        form.addRow("Redirects:", self.redirects_cb)

        # Proxy
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080 or socks5://...")
        self.proxy_input.setText(self.config.proxy_url or "")
        form.addRow("HTTP / SOCKS Proxy:", self.proxy_input)

        # Font Size
        self.font_spin = QSpinBox()
        self.font_spin.setRange(9, 24)
        self.font_spin.setValue(self.config.font_size)
        form.addRow("Editor Font Size:", self.font_spin)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _save_settings(self) -> None:
        self.config.default_timeout = float(self.timeout_spin.value())
        self.config.validate_ssl = self.ssl_cb.isChecked()
        self.config.follow_redirects = self.redirects_cb.isChecked()
        self.config.proxy_url = self.proxy_input.text().strip() or None
        self.config.font_size = self.font_spin.value()

        self.config_store.save(self.config)
        self.settings_saved.emit()
        self.accept()
