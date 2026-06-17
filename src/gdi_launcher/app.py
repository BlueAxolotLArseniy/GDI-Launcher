from __future__ import annotations

import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from gdi_launcher.config import APP_ICON, APP_ID, DARK_STYLE_PATH
from gdi_launcher.services.settings_service import SettingsService
from gdi_launcher.services.translation_service import DEFAULT_LANGUAGE, TranslationService
from gdi_launcher.ui.dialogs.language_selection_dialog import LanguageSelectionDialog
from gdi_launcher.ui.main_window import GDIMainWindow


def configure_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)


def create_app() -> QApplication:
    configure_windows_app_id()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(APP_ICON))

    if DARK_STYLE_PATH.exists():
        app.setStyleSheet(DARK_STYLE_PATH.read_text(encoding="utf-8"))

    return app


def run_app() -> int:
    app = create_app()
    ensure_language_selected()
    window = GDIMainWindow()
    window.show()
    return app.exec()


def main() -> int:
    return run_app()


def ensure_language_selected() -> None:
    settings_service = SettingsService()
    settings = settings_service.load()
    translation_service = TranslationService(settings_service)

    if translation_service.has_language(settings.launcher.language):
        return

    dialog = LanguageSelectionDialog(translation_service)
    if dialog.exec():
        settings.launcher.language = dialog.selected_language()
    else:
        settings.launcher.language = DEFAULT_LANGUAGE

    settings_service.save(settings)
