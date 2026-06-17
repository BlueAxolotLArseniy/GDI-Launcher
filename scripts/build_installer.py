from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_APP_ID = "com.gdi.launcher.installer"
INSTALLER_ICON_PATH = "assets/GDI.ico"

LANGUAGES = {
    "ru": "Русский",
    "en": "English",
}

TRANSLATIONS = {
    "ru": {
        "window.title": "Установка GDI Launcher",
        "language.title": "Выбор языка",
        "language.prompt": "Выберите язык установщика",
        "welcome.title": "Установка GDI Launcher",
        "welcome.description": (
            "Программа установит GDI Launcher на ваш компьютер.\n\n"
            "Перед продолжением рекомендуется закрыть Geometry Dash."
        ),
        "path.title": "Выбор папки установки",
        "path.destination": "Папка назначения:",
        "path.browse": "Обзор...",
        "path.browse_dialog": "Выберите папку для установки",
        "path.shortcut": "Создать ярлык на рабочем столе",
        "progress.preparing": "Подготовка к копированию...",
        "button.cancel": "Отмена",
        "button.back": "Назад",
        "button.next": "Далее >",
        "button.install": "Установить",
        "button.finish": "Завершить",
        "status.create_dir": "Создание директории...",
        "status.archive_missing": "Архив launcher.zip не найден внутри установщика.",
        "status.extract": "Распаковка лаунчера...",
        "status.create_shortcut": "Создание ярлыка...",
        "status.save_settings": "Сохранение настроек...",
        "status.success": "Установка успешно завершена.",
        "status.error": "Ошибка установки: {error}",
    },
    "en": {
        "window.title": "GDI Launcher Setup",
        "language.title": "Language selection",
        "language.prompt": "Select the installer language",
        "welcome.title": "GDI Launcher Setup",
        "welcome.description": (
            "This wizard will install GDI Launcher on your computer.\n\n"
            "It is recommended to close Geometry Dash before continuing."
        ),
        "path.title": "Installation folder",
        "path.destination": "Destination folder:",
        "path.browse": "Browse...",
        "path.browse_dialog": "Select installation folder",
        "path.shortcut": "Create a desktop shortcut",
        "progress.preparing": "Preparing to copy files...",
        "button.cancel": "Cancel",
        "button.back": "Back",
        "button.next": "Next >",
        "button.install": "Install",
        "button.finish": "Finish",
        "status.create_dir": "Creating directory...",
        "status.archive_missing": "launcher.zip was not found inside the installer.",
        "status.extract": "Extracting launcher...",
        "status.create_shortcut": "Creating shortcut...",
        "status.save_settings": "Saving settings...",
        "status.success": "Installation completed successfully.",
        "status.error": "Installation error: {error}",
    },
}


def get_resource_path(relative_path: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path  # type: ignore[attr-defined]

    return PROJECT_ROOT / relative_path


def get_installer_icon() -> QIcon:
    return QIcon(str(get_resource_path(INSTALLER_ICON_PATH)))


def configure_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(INSTALLER_APP_ID)
    except (AttributeError, OSError):
        return


def tr(language: str, key: str, **kwargs: object) -> str:
    text = TRANSLATIONS.get(language, TRANSLATIONS["ru"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)

    return text


class InstallerWorker(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    install_finished = Signal(bool, str)

    def __init__(
        self,
        zip_path: str | Path,
        target_dir: str | Path,
        create_shortcut: bool,
        language: str,
    ) -> None:
        super().__init__()
        self.zip_path = Path(zip_path)
        self.target_dir = Path(target_dir)
        self.create_shortcut = create_shortcut
        self.language = language

    def tr(self, key: str, **kwargs: object) -> str:
        return tr(self.language, key, **kwargs)

    def run(self) -> None:
        try:
            self.status_changed.emit(self.tr("status.create_dir"))
            self.target_dir.mkdir(parents=True, exist_ok=True)

            if not self.zip_path.exists():
                self.install_finished.emit(False, self.tr("status.archive_missing"))
                return

            self.status_changed.emit(self.tr("status.extract"))
            with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
                files = zip_ref.namelist()
                total_files = len(files)

                for index, file_name in enumerate(files):
                    zip_ref.extract(file_name, self.target_dir)
                    if total_files > 0:
                        self.progress_changed.emit(int(((index + 1) / total_files) * 85))

            (self.target_dir / "instances" / "backup_saves").mkdir(parents=True, exist_ok=True)

            self.status_changed.emit(self.tr("status.save_settings"))
            self.write_launcher_settings()

            if self.create_shortcut:
                self.status_changed.emit(self.tr("status.create_shortcut"))
                self.create_desktop_shortcut()

            self.progress_changed.emit(100)
            self.install_finished.emit(True, self.tr("status.success"))
        except Exception as error:
            self.install_finished.emit(False, self.tr("status.error", error=error))

    def write_launcher_settings(self) -> None:
        self.target_dir.mkdir(parents=True, exist_ok=True)
        settings_path = self.target_dir / "settings.json"
        settings: dict[str, Any] = {}

        if settings_path.exists():
            try:
                loaded = json.loads(settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    settings = loaded
            except (OSError, json.JSONDecodeError):
                settings = {}

        launcher_settings = settings.get("launcher", {})
        if not isinstance(launcher_settings, dict):
            launcher_settings = {}
        launcher_settings["language"] = self.language
        settings["launcher"] = launcher_settings

        geometry_dash_settings = settings.get("geometry_dash", {})
        if not isinstance(geometry_dash_settings, dict):
            geometry_dash_settings = {}
        geometry_dash_settings.setdefault("auto_set_priority", False)
        geometry_dash_settings.setdefault("priority", "normal")
        settings["geometry_dash"] = geometry_dash_settings

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create_desktop_shortcut(self) -> None:
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        shortcut_path = desktop / "GDI Launcher.lnk"
        exe_path = self.target_dir / "GDI_App.exe"

        ps_command = (
            "$s=(New-Object -COM WScript.Shell).CreateShortcut('{shortcut}');"
            "$s.TargetPath='{target}';"
            "$s.WorkingDirectory='{workdir}';"
            "$s.IconLocation='{target},0';"
            "$s.Save()"
        ).format(
            shortcut=str(shortcut_path),
            target=str(exe_path),
            workdir=str(self.target_dir),
        )

        subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True)


class GDIInstaller(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.language = "ru"
        self.install_finished = False
        self.install_success = False
        self.worker: InstallerWorker | None = None

        local_app_data = os.environ.get("LOCALAPPDATA")
        base_path = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        self.default_path = base_path / "Programs" / "GDI-Launcher"

        self.setFixedSize(520, 370)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(get_installer_icon())

        self.init_ui()
        self.apply_styles()
        self.retranslate_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_language_page())
        self.pages.addWidget(self.create_welcome_page())
        self.pages.addWidget(self.create_path_page())
        self.pages.addWidget(self.create_progress_page())
        main_layout.addWidget(self.pages)

        self.bottom_bar = QWidget()
        self.bottom_bar.setObjectName("BottomBar")
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(20, 15, 20, 15)

        self.btn_cancel = QPushButton()
        self.btn_back = QPushButton()
        self.btn_next = QPushButton()

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_back.clicked.connect(self.go_back)
        self.btn_next.clicked.connect(self.go_next)

        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_back)
        bottom_layout.addWidget(self.btn_next)
        main_layout.addWidget(self.bottom_bar)

        self.update_buttons()

    def create_language_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)

        self.language_title = QLabel()
        self.language_title.setObjectName("Title")

        self.language_prompt = QLabel()
        self.language_prompt.setWordWrap(True)

        self.language_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.currentIndexChanged.connect(self.change_language)

        layout.addWidget(self.language_title)
        layout.addWidget(self.language_prompt)
        layout.addWidget(self.language_combo)
        layout.addStretch()
        return page

    def create_welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        self.welcome_title = QLabel()
        self.welcome_title.setObjectName("Title")
        self.welcome_description = QLabel()
        self.welcome_description.setWordWrap(True)

        layout.addWidget(self.welcome_title)
        layout.addSpacing(15)
        layout.addWidget(self.welcome_description)
        layout.addStretch()
        return page

    def create_path_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)

        self.path_title = QLabel()
        self.path_title.setObjectName("SubTitle")
        self.destination_label = QLabel()

        layout.addWidget(self.path_title)
        layout.addSpacing(20)
        layout.addWidget(self.destination_label)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(str(self.default_path))
        self.btn_browse = QPushButton()
        self.btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.btn_browse)
        layout.addLayout(path_layout)

        layout.addSpacing(20)
        self.chk_shortcut = QCheckBox()
        self.chk_shortcut.setChecked(True)
        layout.addWidget(self.chk_shortcut)
        layout.addStretch()
        return page

    def create_progress_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        self.lbl_status = QLabel()
        self.lbl_status.setObjectName("SubTitle")
        self.progress_bar = QProgressBar()

        layout.addWidget(self.lbl_status)
        layout.addSpacing(20)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        return page

    def change_language(self, _index: int = -1) -> None:
        language = self.language_combo.currentData()
        self.language = str(language or "ru")
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self.tr("window.title"))
        self.language_title.setText(self.tr("language.title"))
        self.language_prompt.setText(self.tr("language.prompt"))
        self.welcome_title.setText(self.tr("welcome.title"))
        self.welcome_description.setText(self.tr("welcome.description"))
        self.path_title.setText(self.tr("path.title"))
        self.destination_label.setText(self.tr("path.destination"))
        self.btn_browse.setText(self.tr("path.browse"))
        self.chk_shortcut.setText(self.tr("path.shortcut"))
        if not self.install_finished:
            self.lbl_status.setText(self.tr("progress.preparing"))
        self.btn_cancel.setText(self.tr("button.cancel"))
        self.btn_back.setText(self.tr("button.back"))
        self.update_buttons()

    def tr(self, key: str, **kwargs: object) -> str:
        return tr(self.language, key, **kwargs)

    def browse_folder(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("path.browse_dialog"),
            self.path_input.text(),
        )
        if dir_path:
            self.path_input.setText(str(Path(dir_path) / "GDI-Launcher"))

    def update_buttons(self) -> None:
        index = self.pages.currentIndex()
        self.btn_back.setVisible(index in {1, 2})

        if index == 2:
            self.btn_next.setText(self.tr("button.install"))
        elif index == 3 and self.install_finished:
            self.btn_next.setText(self.tr("button.finish"))
        else:
            self.btn_next.setText(self.tr("button.next"))

    def go_back(self) -> None:
        if self.pages.currentIndex() in {1, 2}:
            self.pages.setCurrentIndex(self.pages.currentIndex() - 1)
            self.update_buttons()

    def go_next(self) -> None:
        index = self.pages.currentIndex()

        if index in {0, 1}:
            self.pages.setCurrentIndex(index + 1)
            self.update_buttons()
            return

        if index == 2:
            self.start_install()
            return

        if index == 3 and self.install_finished:
            if self.install_success:
                self.accept()
            else:
                self.reject()

    def start_install(self) -> None:
        self.install_finished = False
        self.install_success = False
        self.progress_bar.setValue(0)
        self.lbl_status.setStyleSheet("")
        self.lbl_status.setText(self.tr("progress.preparing"))

        self.pages.setCurrentIndex(3)
        self.update_buttons()
        self.btn_next.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        self.worker = InstallerWorker(
            get_resource_path("launcher.zip"),
            self.path_input.text().strip(),
            self.chk_shortcut.isChecked(),
            self.language,
        )
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.install_finished.connect(self.on_install_finished)
        self.worker.start()

    def on_install_finished(self, success: bool, message: str) -> None:
        self.install_finished = True
        self.install_success = success
        self.lbl_status.setText(message)
        self.btn_next.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.update_buttons()

        if success:
            self.lbl_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: #f44336; font-weight: bold;")

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog { background-color: #1a1a1a; color: #ffffff; font-family: "Segoe UI"; font-size: 13px; }
            QLabel { color: #dcdcdc; }
            #Title { font-size: 22px; font-weight: bold; color: #4CAF50; }
            #SubTitle { font-size: 16px; font-weight: bold; color: #ffffff; }
            QLineEdit, QComboBox { background-color: #2b2b2b; border: 1px solid #3b3b3b; border-radius: 4px; padding: 5px; color: white; }
            #BottomBar { background-color: #111111; border-top: 1px solid #2b2b2b; }
            QPushButton { background-color: #333333; border: 1px solid #444444; border-radius: 4px; padding: 6px 15px; color: white; min-width: 75px; }
            QPushButton:hover { background-color: #444444; }
            QPushButton:pressed { background-color: #222222; }
            QPushButton:disabled { color: #777777; background-color: #252525; }
            QProgressBar { border: 1px solid #333; border-radius: 4px; background-color: #2b2b2b; text-align: center; color: white; font-weight: bold; height: 20px; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
            QCheckBox { color: #dcdcdc; spacing: 6px; }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #8b8b8b;
                border-radius: 4px;
                background-color: #2b2b2b;
                image: none;
            }
            QCheckBox::indicator:hover {
                border-color: #b0b0b0;
                background-color: #333333;
            }
            QCheckBox::indicator:checked {
                background-color: #5a5a5a;
                border-color: #b0b0b0;
                image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png);
            }
            """
        )


def main() -> int:
    configure_windows_app_id()
    app = QApplication(sys.argv)
    app.setWindowIcon(get_installer_icon())
    installer = GDIInstaller()
    installer.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
