from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from gdi_launcher.config import INSTANCES_DIR
from gdi_launcher.services.process_priority_service import ProcessPriorityService, get_priority_option
from gdi_launcher.services.save_service import SaveService
from gdi_launcher.services.settings_service import SettingsService


ProcessStartedCallback = Callable[[subprocess.Popen], None]


class LaunchService:
    def __init__(
        self,
        instances_dir: str | Path = INSTANCES_DIR,
        save_service: SaveService | None = None,
        settings_service: SettingsService | None = None,
        priority_service: ProcessPriorityService | None = None,
    ) -> None:
        self.instances_dir = Path(instances_dir)
        self.save_service = save_service or SaveService(self.instances_dir)
        self.settings_service = settings_service or SettingsService()
        self.priority_service = priority_service or ProcessPriorityService()

    def get_instance_path(self, instance_name: str) -> Path:
        return self.instances_dir / instance_name

    def get_executable_path(self, instance_name: str) -> Path:
        return self.get_instance_path(instance_name) / "GeometryDash.exe"

    def sync_and_run_instance(
        self,
        instance_name: str,
        on_process_start_callback: ProcessStartedCallback | None = None,
    ) -> None:
        target_dir = self.get_instance_path(instance_name)
        exe_path = self.get_executable_path(instance_name)

        if not exe_path.exists():
            print(f"[-] Ошибка: {exe_path} не найден.")
            return

        print(f"\n--- Подготовка сейвов для '{instance_name}' ---")
        self.save_service.prepare_instance_saves(instance_name)

        print(f"[+] Запускаем {instance_name}...")
        priority_key = self.get_configured_priority_key()
        creation_flags = self.priority_service.get_creation_flags(priority_key)

        try:
            process = subprocess.Popen(
                [str(exe_path)],
                cwd=str(target_dir),
                creationflags=creation_flags,
            )
            self.apply_configured_priority(process, priority_key)

            if on_process_start_callback:
                on_process_start_callback(process)

            process.wait()
        except Exception as error:
            print(f"[-] Ошибка запуска процесса: {error}")
            return

        print("\n--- Синхронизация после выхода из игры ---")
        try:
            self.save_service.store_instance_saves(instance_name)
            self.save_service.restore_original_saves()
        except Exception as error:
            print(f"[-] Ошибка синхронизации сейвов: {error}")

    def get_configured_priority_key(self) -> str | None:
        settings = self.settings_service.load().geometry_dash
        if not settings.auto_set_priority:
            return None

        return get_priority_option(settings.priority).key

    def apply_configured_priority(
        self,
        process: subprocess.Popen,
        priority_key: str | None = None,
    ) -> None:
        priority_key = priority_key or self.get_configured_priority_key()
        if not priority_key:
            return

        priority_option = get_priority_option(priority_key)
        if self.priority_service.ensure_priority(process, priority_option.key):
            print(f"[+] Priority class applied: {priority_option.key}.")
            return

        print(
            "[-] Не удалось задать приоритет Geometry Dash"
            f" (Windows error: {self.priority_service.last_error})."
        )


def sync_and_run_instance(
    instance_name: str,
    on_process_start_callback: ProcessStartedCallback | None = None,
) -> None:
    LaunchService().sync_and_run_instance(instance_name, on_process_start_callback)
