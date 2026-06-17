from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)

from gdi_launcher.services.translation_service import TranslationService


class AddInstanceDialog(QDialog):
    def __init__(self, versions_data: list[dict[str, Any]], parent=None) -> None:
        super().__init__(parent)
        self.versions_data = versions_data
        self.translation_service = TranslationService()

        self.setWindowTitle(self.tr("add.title"))
        self.setFixedWidth(340)

        self._build_ui()
        self._connect_signals()
        self.sync_geode_checkbox_state()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def _build_ui(self) -> None:
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.version_combo = QComboBox()
        self.geode_check = QCheckBox(self.tr("add.install_geode"))

        for version in self.versions_data:
            display_name = version.get("display_name", self.tr("add.unnamed_version"))
            self.version_combo.addItem(display_name, version)

        layout.addRow(self.tr("add.name"), self.name_input)
        layout.addRow(self.tr("add.version"), self.version_combo)
        layout.addRow(self.geode_check)

        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton(self.tr("common.ok"))
        self.btn_cancel = QPushButton(self.tr("common.cancel"))

        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addRow(button_layout)

    def _connect_signals(self) -> None:
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.version_combo.currentIndexChanged.connect(self.sync_geode_checkbox_state)

    def sync_geode_checkbox_state(self) -> None:
        index = self.version_combo.currentIndex()
        if index < 0:
            self.geode_check.setEnabled(False)
            self.geode_check.setChecked(False)
            return

        version_info = self.version_combo.itemData(index)
        is_supported = version_info.get("geode", {}).get("supported", False)

        self.geode_check.setEnabled(is_supported)
        if not is_supported:
            self.geode_check.setChecked(False)

    def get_data(self) -> tuple[str, dict[str, Any], bool]:
        index = self.version_combo.currentIndex()
        version_info = self.version_combo.itemData(index) if index >= 0 else {}

        instance_name = self.name_input.text().strip()
        install_geode = self.geode_check.isChecked()

        return instance_name, version_info, install_geode
