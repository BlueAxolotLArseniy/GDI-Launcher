from __future__ import annotations

from gdi_launcher.services.settings_service import AppSettings, SettingsService
from gdi_launcher.services.translation_service import TranslationService


def test_loads_available_languages() -> None:
    service = TranslationService()

    languages = {language.code: language.name for language in service.available_languages()}

    assert languages["ru"] == "Русский"
    assert languages["en"] == "English"


def test_uses_language_from_settings(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_service = SettingsService(settings_path)
    settings = AppSettings.defaults()
    settings.launcher.language = "en"
    settings_service.save(settings)

    service = TranslationService(settings_service)

    assert service.t("main.run") == "Launch"
    assert service.t("message.name_taken.body", name="GD") == "Instance 'GD' already exists."

