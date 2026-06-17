from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from gdi_launcher.services.translation_service import TranslationService


class DeleteWorker(QThread):
    status_changed = Signal(str)
    progress_changed = Signal(int)
    deletion_finished = Signal(bool, str)

    def __init__(self, target_dir: str | Path, instance_name: str) -> None:
        super().__init__()
        self.target_dir = Path(target_dir)
        self.instance_name = instance_name
        self.translation_service = TranslationService()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def run(self) -> None:
        try:
            if not self.target_dir.exists():
                self.deletion_finished.emit(False, self.tr("delete.folder_missing"))
                return

            self.status_changed.emit(self.tr("delete.scanning"))
            files_to_delete: list[Path] = []
            dirs_to_delete: list[Path] = []

            for root, dirs, files in os.walk(self.target_dir, topdown=False):
                root_path = Path(root)
                files_to_delete.extend(root_path / name for name in files)
                dirs_to_delete.extend(root_path / name for name in dirs)

            total_items = len(files_to_delete) + len(dirs_to_delete) + 1
            current_item = 0

            for file_path in files_to_delete:
                file_path.unlink(missing_ok=True)
                current_item += 1
                self._emit_progress(current_item, total_items)

                if current_item % 5 == 0:
                    self.status_changed.emit(self.tr("delete.deleting", name=file_path.name))

            for dir_path in dirs_to_delete:
                if dir_path.exists():
                    dir_path.rmdir()

                current_item += 1
                self._emit_progress(current_item, total_items)

            if self.target_dir.exists():
                self.target_dir.rmdir()

            self.progress_changed.emit(100)
            self.deletion_finished.emit(
                True,
                self.tr("delete.success", name=self.instance_name),
            )
        except Exception as error:
            self.deletion_finished.emit(False, self.tr("delete.error", error=error))

    def _emit_progress(self, current_item: int, total_items: int) -> None:
        if total_items <= 0:
            self.progress_changed.emit(100)
            return

        self.progress_changed.emit(int((current_item / total_items) * 100))
