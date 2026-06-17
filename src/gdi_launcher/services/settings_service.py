from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gdi_launcher.config import SETTINGS_FILE


@dataclass(slots=True)
class LauncherSettings:
    language: str | None = None


@dataclass(slots=True)
class GeometryDashSettings:
    auto_set_priority: bool = False
    priority: str = "normal"


@dataclass(slots=True)
class AppSettings:
    launcher: LauncherSettings
    geometry_dash: GeometryDashSettings

    @classmethod
    def defaults(cls) -> "AppSettings":
        return cls(
            launcher=LauncherSettings(),
            geometry_dash=GeometryDashSettings(),
        )


class SettingsService:
    def __init__(self, settings_path: str | Path = SETTINGS_FILE) -> None:
        self.settings_path = Path(settings_path)

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            return AppSettings.defaults()

        try:
            raw = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppSettings.defaults()

        return self._from_dict(raw)

    def save(self, settings: AppSettings) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps(asdict(settings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _from_dict(self, raw: dict[str, Any]) -> AppSettings:
        launcher_raw = raw.get("launcher", {})
        if not isinstance(launcher_raw, dict):
            launcher_raw = {}

        gd_raw = raw.get("geometry_dash", {})
        if not isinstance(gd_raw, dict):
            gd_raw = {}

        return AppSettings(
            launcher=LauncherSettings(
                language=launcher_raw.get("language"),
            ),
            geometry_dash=GeometryDashSettings(
                auto_set_priority=bool(gd_raw.get("auto_set_priority", False)),
                priority=str(gd_raw.get("priority", "normal")),
            ),
        )
