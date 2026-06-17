from __future__ import annotations

import shutil
from pathlib import Path

from gdi_launcher.config import INSTANCES_DIR
from gdi_launcher.services.file_service import (
    clear_directory_contents,
    copy_directory_contents,
    get_appdata_path,
)


class SaveService:
    def __init__(
        self,
        instances_dir: str | Path = INSTANCES_DIR,
        appdata_path: str | Path | None = None,
    ) -> None:
        self.instances_dir = Path(instances_dir)
        self.appdata_path = Path(appdata_path) if appdata_path is not None else get_appdata_path()

    @property
    def backup_dir(self) -> Path:
        return self.instances_dir / "backup_saves"

    def get_instance_saves_dir(self, instance_name: str) -> Path:
        return self.instances_dir / instance_name / "saves"

    def prepare_instance_saves(self, instance_name: str) -> None:
        self._backup_original_saves()
        self.appdata_path.mkdir(parents=True, exist_ok=True)

        instance_saves = self.get_instance_saves_dir(instance_name)
        if instance_saves.exists() and any(instance_saves.iterdir()):
            copy_directory_contents(instance_saves, self.appdata_path)

    def store_instance_saves(self, instance_name: str) -> None:
        instance_saves = self.get_instance_saves_dir(instance_name)
        instance_saves.mkdir(parents=True, exist_ok=True)

        if not self.appdata_path.exists():
            return

        clear_directory_contents(instance_saves)
        copy_directory_contents(self.appdata_path, instance_saves)
        shutil.rmtree(self.appdata_path)

    def restore_original_saves(self) -> None:
        if not self.backup_dir.exists() or not any(self.backup_dir.iterdir()):
            return

        self.appdata_path.mkdir(parents=True, exist_ok=True)
        copy_directory_contents(self.backup_dir, self.appdata_path)
        shutil.rmtree(self.backup_dir)

    def _backup_original_saves(self) -> None:
        if not self.appdata_path.exists() or not any(self.appdata_path.iterdir()):
            return

        if self.backup_dir.exists() and any(self.backup_dir.iterdir()):
            shutil.rmtree(self.appdata_path)
            return

        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)

        shutil.copytree(self.appdata_path, self.backup_dir)
        shutil.rmtree(self.appdata_path)

