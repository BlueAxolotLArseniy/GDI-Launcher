from __future__ import annotations

import json
from pathlib import Path

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
    assert service.t("common.yes") == "Yes"
    assert service.t("common.no") == "No"
    assert service.t("message.name_taken.body", name="GD") == "Instance 'GD' already exists."


def test_russian_translations_use_instance_terminology() -> None:
    translations_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "gdi_launcher"
        / "i18n"
        / "translations.json"
    )
    data = json.loads(translations_path.read_text(encoding="utf-8"))

    russian_phrases = [
        phrase["ru"]
        for phrase in data["phrases"].values()
        if isinstance(phrase, dict) and "ru" in phrase
    ]

    assert not any("сборк" in phrase.lower() for phrase in russian_phrases)
