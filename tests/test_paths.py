from __future__ import annotations

from pathlib import Path

from gdi_launcher.config.paths import (
    BASE_ASSETS_DIR,
    INSTANCES_DIR,
    VERSIONS_FILE,
    get_project_root,
)


def test_project_root_points_to_repository_root() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert get_project_root() == project_root


def test_runtime_paths_are_inside_project_in_source_mode() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert BASE_ASSETS_DIR == project_root / "assets"
    assert INSTANCES_DIR == project_root / "instances"
    assert VERSIONS_FILE == project_root / "versions.json"

