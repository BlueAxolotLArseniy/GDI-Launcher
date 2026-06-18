from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from gdi_launcher.config import INSTANCES_DIR
from gdi_launcher.domain import Instance


INVALID_INSTANCE_NAME_CHARS = frozenset('<>:"/\\|?*')
RESERVED_WINDOWS_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
)
Translator = Callable[..., str]

DEFAULT_VALIDATION_MESSAGES = {
    "validation.name_empty": "Название экземпляра не должно быть пустым.",
    "validation.dot_name": "Название экземпляра не может быть '.' или '..'.",
    "validation.absolute_path": "Название экземпляра не должно быть абсолютным путём.",
    "validation.trailing_space_dot": "Название экземпляра не должно заканчиваться пробелом или точкой.",
    "validation.invalid_chars": "Название экземпляра содержит запрещённые символы: {chars}",
    "validation.reserved_windows_name": "Это системное имя Windows. Его нельзя использовать как название папки.",
}


class InstanceService:
    def __init__(self, instances_dir: str | Path = INSTANCES_DIR) -> None:
        self.instances_dir = Path(instances_dir)

    def ensure_instances_dir_exists(self) -> None:
        self.instances_dir.mkdir(parents=True, exist_ok=True)

    def get_instance_path(self, instance_name: str) -> Path:
        return self.instances_dir / instance_name

    def list_instance_names(self) -> list[str]:
        if not self.instances_dir.exists():
            return []

        names: list[str] = []
        for item in self.instances_dir.iterdir():
            if item.is_dir() and item.name != "backup_saves":
                names.append(item.name)

        return sorted(names, key=str.lower)

    def list_instances(self) -> list[Instance]:
        return [
            Instance(
                name=name,
                path=self.get_instance_path(name),
                has_geode=self.instance_has_geode(name),
            )
            for name in self.list_instance_names()
        ]

    def instance_exists(self, instance_name: str) -> bool:
        return self.get_instance_path(instance_name).exists()

    def instance_has_geode(self, instance_name: str) -> bool:
        instance_path = self.get_instance_path(instance_name)
        return (instance_path / "geode").exists() or (instance_path / "Geode.dll").exists()

    def rename_instance(self, old_name: str, new_name: str) -> None:
        self.get_instance_path(old_name).rename(self.get_instance_path(new_name))


def is_valid_instance_name(name: str) -> bool:
    return get_instance_name_validation_error(name) == ""


def get_instance_name_validation_error(
    name: str,
    translator: Translator | None = None,
) -> str:
    def message(key: str, **kwargs: object) -> str:
        if translator is not None:
            return translator(key, **kwargs)

        return DEFAULT_VALIDATION_MESSAGES[key].format(**kwargs)

    clean_name = name.strip()

    if not clean_name:
        return message("validation.name_empty")

    if clean_name in {".", ".."}:
        return message("validation.dot_name")

    if os.path.isabs(clean_name):
        return message("validation.absolute_path")

    if clean_name.rstrip(" .") != clean_name:
        return message("validation.trailing_space_dot")

    invalid_chars = sorted(set(clean_name) & INVALID_INSTANCE_NAME_CHARS)
    if invalid_chars:
        chars = " ".join(invalid_chars)
        return message("validation.invalid_chars", chars=chars)

    device_name = clean_name.split(".", 1)[0].upper()
    if device_name in RESERVED_WINDOWS_NAMES:
        return message("validation.reserved_windows_name")

    return ""
