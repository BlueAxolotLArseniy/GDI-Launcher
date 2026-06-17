from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gdi_launcher.config import TRANSLATIONS_FILE
from gdi_launcher.services.settings_service import SettingsService


DEFAULT_LANGUAGE = "ru"


@dataclass(frozen=True, slots=True)
class LanguageOption:
    code: str
    name: str


class TranslationService:
    def __init__(
        self,
        settings_service: SettingsService | None = None,
        translations_path: str | Path = TRANSLATIONS_FILE,
    ) -> None:
        self.settings_service = settings_service or SettingsService()
        self.translations_path = Path(translations_path)
        self._data = self._load_data()

    @property
    def language(self) -> str:
        language = self.settings_service.load().launcher.language
        if language in self._data["languages"]:
            return language

        return DEFAULT_LANGUAGE

    def t(self, key: str, **kwargs: object) -> str:
        phrase = self._data["phrases"].get(key, {})
        if not isinstance(phrase, dict):
            return key

        text = phrase.get(self.language) or phrase.get(DEFAULT_LANGUAGE) or key
        if kwargs:
            return str(text).format(**kwargs)

        return str(text)

    def available_languages(self) -> list[LanguageOption]:
        result: list[LanguageOption] = []

        for code, metadata in self._data["languages"].items():
            name = metadata.get("name", code) if isinstance(metadata, dict) else code
            result.append(LanguageOption(code=code, name=str(name)))

        return result

    def has_language(self, language: str | None) -> bool:
        return language in self._data["languages"]

    def _load_data(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.translations_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {}

        languages = raw.get("languages", {})
        phrases = raw.get("phrases", {})

        if not isinstance(languages, dict) or not languages:
            languages = {
                DEFAULT_LANGUAGE: {
                    "name": "Русский",
                }
            }

        if not isinstance(phrases, dict):
            phrases = {}

        return {
            "languages": languages,
            "phrases": phrases,
        }

