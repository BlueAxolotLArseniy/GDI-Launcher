from __future__ import annotations

import zipfile

from gdi_launcher.services.settings_service import SettingsService
from gdi_launcher.services.translation_service import TranslationService
from scripts.build_installer import InstallerWorker


def test_installer_language_is_used_by_launcher_settings(tmp_path) -> None:
    payload_path = tmp_path / "launcher.zip"
    with zipfile.ZipFile(payload_path, "w") as payload:
        payload.writestr("GDI_App.exe", "")

    install_dir = tmp_path / "GDI-Launcher"
    worker = InstallerWorker(
        payload_path,
        install_dir,
        create_shortcut=False,
        language="en",
    )

    worker.write_launcher_settings()

    settings_service = SettingsService(install_dir / "settings.json")
    translation_service = TranslationService(settings_service)

    assert settings_service.load().launcher.language == "en"
    assert translation_service.has_language(settings_service.load().launcher.language)
    assert translation_service.t("main.run") == "Launch"


def test_standalone_launcher_without_settings_still_needs_language_choice(tmp_path) -> None:
    settings_service = SettingsService(tmp_path / "settings.json")
    translation_service = TranslationService(settings_service)

    assert settings_service.load().launcher.language is None
    assert not translation_service.has_language(settings_service.load().launcher.language)

