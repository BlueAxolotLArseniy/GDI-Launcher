from __future__ import annotations

import os
import shutil
from pathlib import Path

from gdi_launcher.config import BASE_ASSETS_DIR, GD_ICON_DEFAULT, GEODE_ICON_DEFAULT


class FileService:
    def __init__(self, assets_dir: str | Path = BASE_ASSETS_DIR) -> None:
        self.assets_dir = Path(assets_dir)

    def resolve_asset_path(self, asset_name: str, configured_path: str | Path) -> Path:
        configured_path = Path(configured_path)

        candidates = [
            configured_path,
            self.assets_dir / asset_name,
        ]
        seen: set[Path] = set()

        for candidate in candidates:
            normalized = candidate.resolve(strict=False)
            if normalized in seen:
                continue

            seen.add(normalized)
            if normalized.exists():
                return normalized

        return configured_path

    def get_instance_icon_path(self, has_geode: bool) -> Path:
        if has_geode:
            return self.resolve_asset_path("geode_icon.png", GEODE_ICON_DEFAULT)

        return self.resolve_asset_path("gd_icon.png", GD_ICON_DEFAULT)


def get_appdata_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "GeometryDash"

    return Path.home() / "AppData" / "Local" / "GeometryDash"


def copy_directory_contents(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        return

    dst_path.mkdir(parents=True, exist_ok=True)

    for item in src_path.iterdir():
        target = dst_path / item.name

        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def clear_directory_contents(path: str | Path) -> None:
    path = Path(path)

    if not path.exists():
        return

    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(missing_ok=True)

