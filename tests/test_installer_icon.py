from __future__ import annotations

from pathlib import Path

from scripts import build
from scripts.build_installer import INSTALLER_ICON_PATH, get_resource_path


def test_installer_icon_exists_in_source_mode() -> None:
    assert get_resource_path(INSTALLER_ICON_PATH).exists()


def test_installer_build_packages_window_icon(monkeypatch, tmp_path) -> None:
    captured_args: list[str] = []
    final_installer = tmp_path / "GDI_installer.exe"
    final_installer.write_bytes(b"")

    def fake_run_pyinstaller(args: list[str]) -> None:
        captured_args.extend(args)

    monkeypatch.setattr(build, "run_pyinstaller", fake_run_pyinstaller)
    monkeypatch.setattr(build, "FINAL_INSTALLER", final_installer)

    assert build.build_installer(tmp_path / "launcher.zip") == final_installer
    assert f"--icon={build.ICON_PATH}" in captured_args
    assert build.add_data_arg(build.ICON_PATH, "assets") in captured_args
