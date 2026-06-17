from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QLabel, QPushButton, QVBoxLayout

from gdi_launcher.services.translation_service import DEFAULT_LANGUAGE, TranslationService


class LanguageSelectionDialog(QDialog):
    def __init__(self, translation_service: TranslationService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.translation_service = translation_service or TranslationService()

        self.setWindowTitle("Выбор языка / Language selection")
        self.setFixedWidth(360)
        self.setModal(True)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        label = QLabel("Выберите язык интерфейса / Select the interface language")
        label.setWordWrap(True)
        layout.addWidget(label)

        self.language_combo = QComboBox()
        for language in self.translation_service.available_languages():
            self.language_combo.addItem(language.name, language.code)

        default_index = self.language_combo.findData(DEFAULT_LANGUAGE)
        if default_index >= 0:
            self.language_combo.setCurrentIndex(default_index)

        layout.addWidget(self.language_combo)

        btn_continue = QPushButton("Продолжить / Continue")
        btn_continue.clicked.connect(self.accept)
        layout.addWidget(btn_continue)

    def selected_language(self) -> str:
        language = self.language_combo.currentData()
        return str(language or DEFAULT_LANGUAGE)

