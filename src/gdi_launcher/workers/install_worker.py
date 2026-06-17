from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

from gdi_launcher.services.install_service import InstallService
from gdi_launcher.services.translation_service import TranslationService


class InstallWorker(QThread):
    status_changed = Signal(str)
    progress_changed = Signal(int)
    installation_finished = Signal(bool, list)

    def __init__(
        self,
        version_info: dict[str, Any],
        target_dir: str | Path,
        install_geode: bool,
        install_service: InstallService | None = None,
    ) -> None:
        super().__init__()
        self.version_info = version_info
        self.target_dir = Path(target_dir)
        self.install_geode = install_geode
        self.install_service = install_service or InstallService()
        self.translation_service = TranslationService()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def run(self) -> None:
        try:
            log_entries = self.install_service.install_version(
                self.version_info,
                self.target_dir,
                self.install_geode,
                self.status_changed.emit,
                self.progress_changed.emit,
            )
            self.installation_finished.emit(True, log_entries)
        except Exception as error:
            self.installation_finished.emit(False, [self.tr("install.worker.error", error=error)])


DownloadExtractWorker = InstallWorker
