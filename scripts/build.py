from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
ASSETS_DIR = PROJECT_ROOT / "assets"
STYLES_DIR = SRC_DIR / "gdi_launcher" / "ui" / "styles"
TRANSLATIONS_DIR = SRC_DIR / "gdi_launcher" / "i18n"
VERSIONS_FILE = PROJECT_ROOT / "versions.json"
ICON_PATH = ASSETS_DIR / "GDI.ico"
LAUNCHER_ENTRY = SRC_DIR / "__main__.py"
INSTALLER_ENTRY = PROJECT_ROOT / "scripts" / "build_installer.py"

BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_DIR = BUILD_DIR / "specs"
LAUNCHER_DIST_DIR = BUILD_DIR / "launcher_dist"
LAUNCHER_WORK_DIR = BUILD_DIR / "launcher_work"
INSTALLER_WORK_DIR = BUILD_DIR / "installer_work"
PAYLOAD_ZIP = BUILD_DIR / "launcher.zip"

LAUNCHER_EXE_NAME = "GDI_App"
INSTALLER_EXE_NAME = "GDI_installer"
FINAL_INSTALLER = DIST_DIR / f"{INSTALLER_EXE_NAME}.exe"


def add_data_arg(source: Path, destination: str) -> str:
    return f"--add-data={source}{os.pathsep}{destination}"


def remove_path(path: Path) -> None:
    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def clean_previous_builds() -> None:
    for path in [
        BUILD_DIR,
        DIST_DIR,
        PROJECT_ROOT / "launcher.zip",
        PROJECT_ROOT / "GDI_App.spec",
        PROJECT_ROOT / "GDI_Launcher_Setup.spec",
        PROJECT_ROOT / "GDI_installer.spec",
    ]:
        remove_path(path)


def validate_required_files() -> None:
    required_paths = [
        (ASSETS_DIR, "assets directory was not found."),
        (ICON_PATH, "assets/GDI.ico was not found."),
        (STYLES_DIR, "src/gdi_launcher/ui/styles directory was not found."),
        (TRANSLATIONS_DIR, "src/gdi_launcher/i18n directory was not found."),
        (LAUNCHER_ENTRY, "src/__main__.py was not found."),
        (INSTALLER_ENTRY, "scripts/build_installer.py was not found."),
    ]

    for path, message in required_paths:
        if not path.exists():
            raise SystemExit(message)


def run_pyinstaller(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True, cwd=PROJECT_ROOT)
    if result.returncode == 0:
        return

    print(result.stdout)
    print(result.stderr)
    raise SystemExit(result.returncode)


def build_launcher() -> Path:
    run_pyinstaller(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--onefile",
            "--noconsole",
            f"--name={LAUNCHER_EXE_NAME}",
            f"--icon={ICON_PATH}",
            f"--paths={SRC_DIR}",
            f"--distpath={LAUNCHER_DIST_DIR}",
            f"--workpath={LAUNCHER_WORK_DIR}",
            f"--specpath={SPEC_DIR}",
            add_data_arg(ASSETS_DIR, "assets"),
            add_data_arg(STYLES_DIR, "gdi_launcher/ui/styles"),
            add_data_arg(TRANSLATIONS_DIR, "gdi_launcher/i18n"),
            str(LAUNCHER_ENTRY),
        ]
    )

    launcher_exe = LAUNCHER_DIST_DIR / f"{LAUNCHER_EXE_NAME}.exe"
    if not launcher_exe.exists():
        raise SystemExit(f"Launcher executable was not created: {launcher_exe}")

    return launcher_exe


def package_launcher(launcher_exe: Path) -> Path:
    PAYLOAD_ZIP.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(PAYLOAD_ZIP, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(launcher_exe, "GDI_App.exe")

        if VERSIONS_FILE.exists():
            zip_file.write(VERSIONS_FILE, "versions.json")

    return PAYLOAD_ZIP


def build_installer(launcher_zip: Path) -> Path:
    run_pyinstaller(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--onefile",
            "--noconsole",
            f"--name={INSTALLER_EXE_NAME}",
            f"--icon={ICON_PATH}",
            f"--distpath={DIST_DIR}",
            f"--workpath={INSTALLER_WORK_DIR}",
            f"--specpath={SPEC_DIR}",
            add_data_arg(ICON_PATH, "assets"),
            add_data_arg(launcher_zip, "."),
            str(INSTALLER_ENTRY),
        ]
    )

    if not FINAL_INSTALLER.exists():
        raise SystemExit(f"Installer executable was not created: {FINAL_INSTALLER}")

    return FINAL_INSTALLER


def clean_intermediate_files() -> None:
    for item in DIST_DIR.iterdir():
        if item.resolve() != FINAL_INSTALLER.resolve():
            remove_path(item)

    remove_path(BUILD_DIR)


def main() -> None:
    print("[1/5] Cleaning previous builds...")
    clean_previous_builds()

    print("[2/5] Checking project files...")
    validate_required_files()

    print("[3/5] Building launcher payload...")
    launcher_exe = build_launcher()

    print("[4/5] Building GDI_installer.exe...")
    launcher_zip = package_launcher(launcher_exe)
    installer_exe = build_installer(launcher_zip)

    print("[5/5] Removing intermediate files...")
    clean_intermediate_files()

    print(f"Build complete: {installer_exe}")


if __name__ == "__main__":
    main()
