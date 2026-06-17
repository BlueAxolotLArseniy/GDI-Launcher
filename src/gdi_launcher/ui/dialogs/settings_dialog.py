from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gdi_launcher.services.process_priority_service import PRIORITY_OPTIONS, get_priority_option
from gdi_launcher.services.settings_service import SettingsService
from gdi_launcher.services.translation_service import TranslationService


SIDEBAR_WIDTH = 150
SIDEBAR_ITEM_HEIGHT = 38


class SettingsDialog(QDialog):
    def __init__(self, settings_service: SettingsService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.settings_service = settings_service or SettingsService()
        self.translation_service = TranslationService(self.settings_service)
        self.settings = self.settings_service.load()
        self.section_title_keys = [
            "settings.section.launcher",
            "settings.section.geometry_dash",
        ]

        self.setWindowTitle(self.tr("settings.title"))
        self.resize(720, 420)

        self._build_ui()
        self._apply_prism_style()
        self._load_values()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(2, 2, 2, 2)
        root_layout.setSpacing(6)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        self.section_list = QListWidget()
        self.section_list.setObjectName("SettingsSidebar")
        self.section_list.setFixedWidth(SIDEBAR_WIDTH)
        self.section_list.setSpacing(3)
        for title_key in self.section_title_keys:
            item = QListWidgetItem(self.tr(title_key))
            item.setSizeHint(QSize(SIDEBAR_WIDTH - 18, SIDEBAR_ITEM_HEIGHT))
            self.section_list.addItem(item)
        self.section_list.currentRowChanged.connect(self._select_section)

        content_layout.addWidget(self.section_list)
        content_layout.addWidget(self._build_settings_content(), 1)
        root_layout.addLayout(content_layout, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_save = QPushButton(self.tr("common.save"))
        btn_save.clicked.connect(self._save_and_accept)
        button_layout.addWidget(btn_save)

        btn_cancel = QPushButton(self.tr("common.cancel"))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        root_layout.addLayout(button_layout)
        self.section_list.setCurrentRow(0)

    def _build_settings_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("SettingsContent")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 8, 8, 0)
        layout.setSpacing(8)

        self.title_label = QLabel(self.tr("settings.section.launcher"))
        self.title_label.setObjectName("SettingsTitle")
        layout.addWidget(self.title_label)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_launcher_page())
        self.pages.addWidget(self._build_geometry_dash_page())
        layout.addWidget(self.pages, 1)

        return content

    def _build_launcher_page(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setObjectName("SettingsTabs")
        tabs.addTab(self._build_system_tab(), self.tr("settings.tab.system"))
        return tabs

    def _build_system_tab(self) -> QWidget:
        page = QWidget()
        page.setObjectName("TabPage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(10)

        language_group = QGroupBox(self.tr("settings.group.language"))
        group_layout = QGridLayout(language_group)
        group_layout.setContentsMargins(8, 10, 8, 8)
        group_layout.setHorizontalSpacing(10)
        group_layout.setVerticalSpacing(8)

        self.language_label = QLabel(self.tr("settings.language_label"))
        self.language_combo = QComboBox()
        for language in self.translation_service.available_languages():
            self.language_combo.addItem(language.name, language.code)

        group_layout.addWidget(self.language_label, 0, 0)
        group_layout.addWidget(self.language_combo, 0, 1)
        group_layout.setColumnStretch(1, 1)

        layout.addWidget(language_group)

        hint = QLabel(self.tr("settings.language_hint"))
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def _build_geometry_dash_page(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setObjectName("SettingsTabs")
        tabs.addTab(self._build_geometry_dash_main_tab(), self.tr("settings.tab.main"))
        return tabs

    def _build_geometry_dash_main_tab(self) -> QWidget:
        page = QWidget()
        page.setObjectName("TabPage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(10)

        priority_group = QGroupBox(self.tr("settings.group.priority"))
        group_layout = QGridLayout(priority_group)
        group_layout.setContentsMargins(8, 10, 8, 8)
        group_layout.setHorizontalSpacing(10)
        group_layout.setVerticalSpacing(8)

        self.auto_priority_check = QCheckBox(self.tr("settings.auto_priority"))
        self.auto_priority_check.toggled.connect(self._sync_priority_controls)
        group_layout.addWidget(self.auto_priority_check, 0, 0, 1, 2)

        self.priority_label = QLabel(self.tr("settings.priority_label"))
        self.priority_combo = QComboBox()
        for option in PRIORITY_OPTIONS:
            self.priority_combo.addItem(self.tr(option.label_key), option.key)

        group_layout.addWidget(self.priority_label, 1, 0)
        group_layout.addWidget(self.priority_combo, 1, 1)
        group_layout.setColumnStretch(1, 1)

        layout.addWidget(priority_group)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #3e3e3e;")
        layout.addWidget(divider)

        hint = QLabel(self.tr("settings.priority_hint"))
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def _load_values(self) -> None:
        launcher = self.settings.launcher
        language_index = self.language_combo.findData(launcher.language)
        if language_index < 0:
            language_index = self.language_combo.findData("ru")
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)

        geometry_dash = self.settings.geometry_dash
        priority_option = get_priority_option(geometry_dash.priority)
        self.auto_priority_check.setChecked(geometry_dash.auto_set_priority)

        priority_index = self.priority_combo.findData(priority_option.key)
        if priority_index >= 0:
            self.priority_combo.setCurrentIndex(priority_index)

        self._sync_priority_controls(geometry_dash.auto_set_priority)

    def _select_section(self, index: int) -> None:
        if index < 0:
            return

        self.pages.setCurrentIndex(index)
        self.title_label.setText(self.tr(self.section_title_keys[index]))

    def _sync_priority_controls(self, enabled: bool) -> None:
        self.priority_label.setEnabled(enabled)
        self.priority_combo.setEnabled(enabled)

    def _save_and_accept(self) -> None:
        settings = self.settings
        settings.launcher.language = str(self.language_combo.currentData())
        settings.geometry_dash.auto_set_priority = self.auto_priority_check.isChecked()
        settings.geometry_dash.priority = str(self.priority_combo.currentData())

        self.settings_service.save(settings)
        self.accept()

    def _apply_prism_style(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1f1f1f;
                color: #ffffff;
                font-family: "Segoe UI";
                font-size: 12px;
            }

            QWidget#SettingsContent,
            QWidget#TabPage {
                background-color: #1f1f1f;
            }

            QListWidget#SettingsSidebar {
                background-color: #303030;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                outline: none;
            }

            QListWidget#SettingsSidebar::item {
                border-radius: 3px;
                color: #ffffff;
                padding: 5px 8px;
            }

            QListWidget#SettingsSidebar::item:selected {
                background-color: #3d3d3d;
            }

            QListWidget#SettingsSidebar::item:hover {
                background-color: #383838;
            }

            QLabel {
                color: #ffffff;
                background: transparent;
            }

            QLabel#SettingsTitle {
                font-size: 14px;
                font-weight: 700;
                color: #ffffff;
            }

            QLabel#MutedLabel {
                color: #c8c8c8;
            }

            QTabWidget::pane {
                background-color: #2b2b2b;
                border: 1px solid #3f3f3f;
                border-radius: 3px;
                top: -1px;
            }

            QTabBar::tab {
                background-color: #252525;
                border: 1px solid #3f3f3f;
                border-bottom: none;
                color: #ffffff;
                min-width: 62px;
                padding: 4px 10px;
            }

            QTabBar::tab:selected {
                background-color: #303030;
            }

            QTabBar::tab:hover {
                background-color: #363636;
            }

            QGroupBox {
                background-color: #2b2b2b;
                border: 1px solid #747474;
                border-radius: 4px;
                color: #ffffff;
                margin-top: 10px;
                padding-top: 8px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 3px;
                background-color: #2b2b2b;
            }

            QPushButton {
                background-color: #333333;
                border: 1px solid #4d4d4d;
                border-radius: 4px;
                color: #ffffff;
                min-height: 20px;
                padding: 3px 10px;
            }

            QPushButton:hover {
                background-color: #3f3f3f;
                border-color: #686868;
            }

            QPushButton:pressed {
                background-color: #282828;
                border-color: #777777;
            }

            QComboBox {
                background-color: #2c2c2c;
                border: 1px solid #5d5d5d;
                border-radius: 3px;
                color: #ffffff;
                min-height: 20px;
                padding: 1px 6px;
            }

            QComboBox:focus {
                border-color: #808080;
            }

            QComboBox::drop-down {
                border: none;
                width: 22px;
            }

            QCheckBox {
                color: #ffffff;
                spacing: 6px;
            }

            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #8b8b8b;
                border-radius: 4px;
                background-color: #2b2b2b;
                image: none;
            }

            QCheckBox::indicator:checked {
                background-color: #5a5a5a;
                border-color: #b0b0b0;
                image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png);
            }
            """
        )
