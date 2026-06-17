from __future__ import annotations

import sys
from pathlib import Path


def is_frozen_app() -> bool:
    return hasattr(sys, "_MEIPASS")


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_run_dir() -> Path:
    if is_frozen_app():
        return Path(sys.executable).resolve().parent

    return get_project_root()


def get_assets_dir() -> Path:
    if is_frozen_app():
        return Path(sys._MEIPASS).resolve() / "assets"  # type: ignore[attr-defined]

    return get_project_root() / "assets"


PACKAGE_ROOT: Path = Path(__file__).resolve().parents[1]
BASE_RUN_DIR: Path = get_run_dir()
BASE_ASSETS_DIR: Path = get_assets_dir()
INSTANCES_DIR: Path = BASE_RUN_DIR / "instances"
VERSIONS_FILE: Path = BASE_RUN_DIR / "versions.json"
SETTINGS_FILE: Path = BASE_RUN_DIR / "settings.json"
DARK_STYLE_PATH: Path = PACKAGE_ROOT / "ui" / "styles" / "dark.qss"
TRANSLATIONS_FILE: Path = PACKAGE_ROOT / "i18n" / "translations.json"
