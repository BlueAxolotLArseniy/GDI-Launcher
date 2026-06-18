from __future__ import annotations

import subprocess
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gdi_launcher.services.file_service import FileService
from gdi_launcher.services.instance_service import (
    InstanceService,
    get_instance_name_validation_error,
)
from gdi_launcher.services.manifest_service import ManifestService
from gdi_launcher.services.translation_service import TranslationService
from gdi_launcher.ui.dialogs.add_instance_dialog import AddInstanceDialog
from gdi_launcher.ui.dialogs.delete_progress_dialog import DeleteProgressDialog
from gdi_launcher.ui.dialogs.install_progress_dialog import InstallProgressDialog
from gdi_launcher.ui.dialogs.message_box import ask_yes_no
from gdi_launcher.ui.dialogs.settings_dialog import SettingsDialog
from gdi_launcher.ui.widgets.action_row_button import ActionRowButton
from gdi_launcher.ui.widgets.instance_card import InstanceCard
from gdi_launcher.workers.launch_worker import LaunchWorker


class GDIMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.current_process: Optional[subprocess.Popen] = None
        self.selected_card: Optional[InstanceCard] = None
        self.cards: list[InstanceCard] = []
        self.launch_worker: LaunchWorker | None = None

        self.instance_service = InstanceService()
        self.file_service = FileService()
        self.manifest_service = ManifestService()
        self.translation_service = TranslationService()

        self.instance_service.ensure_instances_dir_exists()

        self.resize(900, 600)
        self.init_ui()
        self.retranslate_ui()
        self.refresh_instances()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def init_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setStyleSheet(
            """
            QFrame#TopBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3e3e3e;
            }

            QPushButton#AddInstanceButton,
            QPushButton#SettingsButton {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 4px;
                color: white;
                font-weight: 600;
                padding: 6px 12px;
            }

            QPushButton#AddInstanceButton:hover,
            QPushButton#SettingsButton:hover {
                background-color: #454545;
                border-color: #777777;
            }

            QPushButton#AddInstanceButton:pressed,
            QPushButton#SettingsButton:pressed {
                background-color: #242424;
                border-color: #888888;
            }
            """
        )
        top_bar.setFixedHeight(50)

        top_layout = QHBoxLayout(top_bar)
        self.btn_add = QPushButton()
        self.btn_add.setObjectName("AddInstanceButton")
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self.open_add_dialog)
        top_layout.addWidget(self.btn_add)

        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("SettingsButton")
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        top_layout.addWidget(self.btn_settings)

        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        body_layout = QHBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #1e1e1e;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.grid_container)
        body_layout.addWidget(self.scroll_area, stretch=3)

        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #252525;")
        right_panel.setFixedWidth(250)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 16, 12, 14)
        right_layout.setSpacing(8)

        self.lbl_selected_icon = QLabel()
        self.lbl_selected_icon.setFixedSize(96, 96)
        self.lbl_selected_icon.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_selected_icon, alignment=Qt.AlignHCenter)

        self.lbl_selected = QLabel()
        self.lbl_selected.setStyleSheet(
            "color: white; font-weight: bold; font-size: 16px; margin-bottom: 10px;"
        )
        self.lbl_selected.setAlignment(Qt.AlignCenter)
        self.lbl_selected.setWordWrap(True)
        right_layout.addWidget(self.lbl_selected)
        right_layout.addSpacing(8)

        action_menu = QWidget()
        action_layout = QVBoxLayout(action_menu)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(1)

        self.btn_run = ActionRowButton("▶", "")
        self.btn_run.clicked.connect(self.run_selected_instance)
        action_layout.addWidget(self.btn_run)

        self.btn_rename = ActionRowButton("⚙", "")
        self.btn_rename.clicked.connect(self.rename_selected_instance)
        action_layout.addWidget(self.btn_rename)

        self.btn_open_folder = ActionRowButton("▸", "")
        self.btn_open_folder.clicked.connect(self.open_selected_instance_folder)
        action_layout.addWidget(self.btn_open_folder)

        self.btn_delete = ActionRowButton("⌫", "", danger=True)
        self.btn_delete.clicked.connect(self.delete_selected_instance)
        action_layout.addWidget(self.btn_delete)

        right_layout.addWidget(action_menu)
        right_layout.addStretch()
        body_layout.addWidget(right_panel, stretch=1)

        main_layout.addLayout(body_layout)
        self.update_side_panel()

    def retranslate_ui(self) -> None:
        self.translation_service = TranslationService()
        self.setWindowTitle(self.tr("app.title"))
        self.btn_add.setText(self.tr("main.add_instance"))
        self.btn_settings.setText(self.tr("main.settings"))
        self.btn_run.set_text(self.tr("main.run"))
        self.btn_rename.set_text(self.tr("main.rename"))
        self.btn_open_folder.set_text(self.tr("main.folder"))
        self.btn_delete.set_text(self.tr("main.delete"))

        if not self.selected_card:
            self.lbl_selected.setText(self.tr("main.select_instance"))

    def handle_card_selection(self, clicked_card: InstanceCard) -> None:
        if self.selected_card:
            self.selected_card.set_selected_state(False)

        self.selected_card = clicked_card
        self.selected_card.set_selected_state(True)
        self.update_side_panel()

    def update_side_panel(self) -> None:
        has_selection = self.selected_card is not None
        launch_blocked = self.is_launch_blocked()

        self.btn_run.setEnabled(has_selection or launch_blocked)
        self.btn_run.set_alert_state(launch_blocked)

        for button in (self.btn_rename, self.btn_open_folder, self.btn_delete):
            button.setEnabled(has_selection)

        if not has_selection:
            self.lbl_selected_icon.hide()
            self.lbl_selected.setText(self.tr("main.select_instance"))
            return

        self.lbl_selected_icon.show()
        instance_name = self.selected_card.instance_name
        has_geode = self.instance_service.instance_has_geode(instance_name)
        chosen_icon = self.file_service.get_instance_icon_path(has_geode)

        self.lbl_selected.setText(instance_name)

        if chosen_icon.exists():
            pixmap = QPixmap(str(chosen_icon))
            if not pixmap.isNull():
                self.lbl_selected_icon.setPixmap(
                    pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.lbl_selected_icon.setText("")
                self.lbl_selected_icon.setStyleSheet("border: none;")
                return

        text_label = "GEODE" if has_geode else "GD"
        color = "#a855f7" if has_geode else "#4CAF50"
        self.lbl_selected_icon.setPixmap(QPixmap())
        self.lbl_selected_icon.setText(text_label)
        self.lbl_selected_icon.setStyleSheet(
            f"color: {color}; font-weight: bold; border: 1px dashed {color}; border-radius: 8px;"
        )

    def is_game_running(self) -> bool:
        return self.current_process is not None and self.current_process.poll() is None

    def is_launch_blocked(self) -> bool:
        return self.is_game_running() or (
            self.launch_worker is not None and self.launch_worker.isRunning()
        )

    def open_add_dialog(self) -> None:
        versions_list = self.manifest_service.load_versions_or_fallback()

        dialog = AddInstanceDialog(versions_list, self)
        if not dialog.exec():
            return

        name, version_info, install_geode = dialog.get_data()
        if not name or not version_info or not version_info.get("game_url"):
            QMessageBox.warning(self, self.tr("common.error"), self.tr("message.invalid_instance_config"))
            return

        validation_error = get_instance_name_validation_error(name, self.tr)
        if validation_error:
            QMessageBox.warning(self, self.tr("message.invalid_name.title"), validation_error)
            return

        target_dir = self.instance_service.get_instance_path(name)
        if self.instance_service.instance_exists(name):
            QMessageBox.warning(
                self,
                self.tr("message.name_taken.title"),
                self.tr("message.name_taken.body", name=name),
            )
            return

        progress_dialog = InstallProgressDialog(version_info, str(target_dir), install_geode, self)
        progress_dialog.exec()
        self.refresh_instances()

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(parent=self)
        if dialog.exec():
            self.retranslate_ui()

    def refresh_instances(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        selected_name = self.selected_card.instance_name if self.selected_card else None
        self.selected_card = None
        self.cards = []

        for instance in self.instance_service.list_instances():
            card = InstanceCard(instance.name, instance.has_geode, self)
            self.cards.append(card)

            if selected_name and instance.name == selected_name:
                self.selected_card = card
                card.set_selected_state(True)

        self.update_side_panel()
        self.rearrange_grid()

    def set_active_process(self, process: subprocess.Popen) -> None:
        self.current_process = process
        self.update_side_panel()

    def clear_active_process(self) -> None:
        self.current_process = None
        self.launch_worker = None
        self.update_side_panel()

    def run_selected_instance(self) -> None:
        if self.is_launch_blocked():
            QMessageBox.information(
                self,
                self.tr("message.game_running.title"),
                self.tr("message.game_running.body"),
            )
            return

        if not self.selected_card:
            QMessageBox.warning(
                self,
                self.tr("message.instance_not_selected.title"),
                self.tr("message.instance_not_selected.launch"),
            )
            return

        self.launch_worker = LaunchWorker(self.selected_card.instance_name)
        self.launch_worker.process_started.connect(self.set_active_process)
        self.launch_worker.launch_finished.connect(self.clear_active_process)
        self.launch_worker.start()
        self.update_side_panel()

    def delete_selected_instance(self) -> None:
        if not self.selected_card:
            QMessageBox.warning(
                self,
                self.tr("message.instance_not_selected.title"),
                self.tr("message.instance_not_selected.delete"),
            )
            return

        if self.current_process and self.current_process.poll() is None:
            QMessageBox.warning(
                self,
                self.tr("message.game_running.title"),
                self.tr("message.game_running.body"),
            )
            return

        instance_name = self.selected_card.instance_name
        should_delete = ask_yes_no(
            self,
            self.tr("message.delete_confirm.title"),
            self.tr("message.delete_confirm.body", name=instance_name),
            self.tr("common.yes"),
            self.tr("common.no"),
        )
        if not should_delete:
            return

        target_dir = self.instance_service.get_instance_path(instance_name)
        progress_dialog = DeleteProgressDialog(str(target_dir), instance_name, self)
        progress_dialog.exec()
        self.refresh_instances()

    def rename_selected_instance(self) -> None:
        if not self.selected_card:
            QMessageBox.warning(
                self,
                self.tr("message.instance_not_selected.title"),
                self.tr("message.instance_not_selected.generic"),
            )
            return

        if self.current_process and self.current_process.poll() is None:
            QMessageBox.warning(
                self,
                self.tr("message.game_running.title"),
                self.tr("message.game_running.body"),
            )
            return

        old_name = self.selected_card.instance_name
        new_name, ok = QInputDialog.getText(
            self,
            self.tr("message.rename.title"),
            self.tr("message.rename.prompt"),
            QLineEdit.Normal,
            old_name,
        )
        if not ok:
            return

        new_name = new_name.strip()
        if new_name == old_name:
            return

        validation_error = get_instance_name_validation_error(new_name, self.tr)
        if validation_error:
            QMessageBox.warning(self, self.tr("message.invalid_name.title"), validation_error)
            return

        if self.instance_service.instance_exists(new_name):
            QMessageBox.warning(
                self,
                self.tr("message.name_taken.title"),
                self.tr("message.name_taken.body", name=new_name),
            )
            return

        try:
            self.instance_service.rename_instance(old_name, new_name)
            self.refresh_instances()
        except OSError as error:
            QMessageBox.critical(
                self,
                self.tr("message.rename_error.title"),
                self.tr("message.rename_error.body", error=error),
            )

    def open_selected_instance_folder(self) -> None:
        if not self.selected_card:
            QMessageBox.warning(
                self,
                self.tr("message.instance_not_selected.title"),
                self.tr("message.instance_not_selected.generic"),
            )
            return

        target_dir = self.instance_service.get_instance_path(self.selected_card.instance_name)
        if not target_dir.exists():
            QMessageBox.warning(
                self,
                self.tr("message.folder_missing.title"),
                self.tr("message.folder_missing.body"),
            )
            return

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(target_dir))):
            QMessageBox.warning(
                self,
                self.tr("message.folder_open_error.title"),
                self.tr("message.folder_open_error.body"),
            )

    def rearrange_grid(self) -> None:
        if not self.cards:
            return

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        card_width_with_spacing = 125
        scroll_area_width = self.scroll_area.viewport().width()
        available_width = scroll_area_width - 50
        columns = max(1, available_width // card_width_with_spacing)

        row = 0
        column = 0

        for card in self.cards:
            self.grid_layout.addWidget(card, row, column)
            column += 1

            if column >= columns:
                column = 0
                row += 1

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.rearrange_grid()
