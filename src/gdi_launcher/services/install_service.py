from __future__ import annotations

import os
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gdi_launcher.services.translation_service import TranslationService


ProgressCallback = Callable[[int], None]
StatusCallback = Callable[[str], None]


class InstallService:
    def __init__(self, translation_service: TranslationService | None = None) -> None:
        self.translation_service = translation_service or TranslationService()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def install_version(
        self,
        version_info: dict[str, Any],
        target_dir: str | Path,
        install_geode: bool,
        status_callback: StatusCallback | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> list[str]:
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        log_entries: list[str] = []

        game_url = version_info["game_url"]
        game_zip = target_path / "game_temp.zip"

        self._emit_status(status_callback, self.tr("install.status.download_game"))
        log_entries.append(self.tr("install.log.download_game", url=game_url))
        self._download_file(game_url, game_zip, progress_callback)

        log_entries.append(self.tr("install.log.extract_game"))
        self._emit_progress(progress_callback, 0)
        self._extract_zip(
            game_zip,
            target_path,
            self.tr("install.status.extract_game"),
            status_callback,
            progress_callback,
        )
        game_zip.unlink(missing_ok=True)
        log_entries.append(self.tr("install.log.game_extracted"))

        geode_info = version_info.get("geode", {})
        if install_geode and geode_info.get("supported", False):
            geode_url = geode_info["url"]
            geode_zip = target_path / "geode_temp.zip"

            self._emit_status(status_callback, self.tr("install.status.download_geode"))
            log_entries.append(self.tr("install.log.download_geode", url=geode_url))
            self._emit_progress(progress_callback, 0)
            self._download_file(geode_url, geode_zip, progress_callback)

            log_entries.append(self.tr("install.log.extract_geode"))
            self._emit_progress(progress_callback, 0)
            self._extract_zip(
                geode_zip,
                target_path,
                self.tr("install.status.inject_geode"),
                status_callback,
                progress_callback,
            )
            geode_zip.unlink(missing_ok=True)
            log_entries.append(self.tr("install.log.geode_installed"))

        self._initialize_instance(target_path)
        return log_entries

    def _download_file(
        self,
        url: str,
        target_path: Path,
        progress_callback: ProgressCallback | None,
    ) -> None:
        def download_hook(block_num: int, block_size: int, total_size: int) -> None:
            if total_size <= 0:
                return

            percent = int((block_num * block_size / total_size) * 100)
            self._emit_progress(progress_callback, min(percent, 100))

        urllib.request.urlretrieve(url, target_path, reporthook=download_hook)

    def _extract_zip(
        self,
        zip_path: Path,
        target_dir: Path,
        status_prefix: str,
        status_callback: StatusCallback | None,
        progress_callback: ProgressCallback | None,
    ) -> None:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            files = zip_ref.namelist()
            total_files = len(files)

            for index, file_name in enumerate(files):
                zip_ref.extract(file_name, target_dir)

                if total_files <= 0:
                    continue

                percent = int(((index + 1) / total_files) * 100)
                short_name = os.path.basename(file_name) or file_name

                self._emit_progress(progress_callback, percent)
                self._emit_status(
                    status_callback,
                    f"{status_prefix} [{index + 1}/{total_files}]: {short_name}",
                )

    def _initialize_instance(self, target_dir: Path) -> None:
        saves_path = target_dir / "saves"
        saves_path.mkdir(parents=True, exist_ok=True)

        (target_dir / "steam_appid.txt").write_text("322170", encoding="utf-8")

        empty_files = [
            "CCGameManager.dat",
            "CCLocalLevels.dat",
            "CCGameManager2.dat",
            "CCLocalLevels2.dat",
        ]

        for file_name in empty_files:
            file_path = saves_path / file_name
            if not file_path.exists():
                file_path.write_bytes(b"")

    def _emit_status(self, callback: StatusCallback | None, message: str) -> None:
        if callback:
            callback(message)

    def _emit_progress(self, callback: ProgressCallback | None, value: int) -> None:
        if callback:
            callback(value)
