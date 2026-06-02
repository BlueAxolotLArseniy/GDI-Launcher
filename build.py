import os
import shutil
import zipfile
import subprocess
import sys

def main():
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
    ICON_PATH = os.path.join(ASSETS_DIR, "GDI.ico")

    if not os.path.exists(ASSETS_DIR):
        print("\n[КРИТИЧЕСКАЯ ОШИБКА] Папка 'assets' НЕ НАЙДЕНА!")
        sys.exit(1)

    if not os.path.exists(ICON_PATH):
        print("\n[КРИТИЧЕСКАЯ ОШИБКА] Файл 'GDI.ico' НЕ НАЙДЕН внутри assets!")
        sys.exit(1)

    print("\n[1/4] Очистка старых сборок и кэша...")
    for path in ["dist", "build", "launcher.zip", "GDI-Launcher.spec", "GDI_Launcher_Setup.spec"]:
        full_path = os.path.join(PROJECT_ROOT, path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

    python_exe = sys.executable

    print("[2/4] Компиляция лаунчера в ЕДИНЫЙ .exe файл...")
    launcher_cmd = [
        python_exe,
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=GDI_App",
        f"--icon={ICON_PATH}",
        f"--add-data={ASSETS_DIR};assets",
        os.path.join(PROJECT_ROOT, "main.py")
    ]
    
    result = subprocess.run(launcher_cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("[-] Ошибка при компиляции лаунчера:")
        print(result.stderr)
        sys.exit(1)

    print("[3/4] Упаковка одиночного лаунчера в launcher.zip...")
    launcher_exe_path = os.path.join(PROJECT_ROOT, "dist", "GDI_App.exe")
    
    with zipfile.ZipFile(os.path.join(PROJECT_ROOT, "launcher.zip"), "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(launcher_exe_path, "GDI_App.exe")

    print("[4/4] Компиляция финального установщика (Setup)...")
    installer_cmd = [
        python_exe,
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=GDI_Launcher_Setup",
        f"--icon={ICON_PATH}",
        f"--add-data={os.path.join(PROJECT_ROOT, 'launcher.zip')};.",
        os.path.join(PROJECT_ROOT, "setup.py")
    ]
    
    result = subprocess.run(installer_cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("[-] Ошибка при компиляции установщика:")
        print(result.stderr)
        sys.exit(1)
        
    print("\n" + "="*40)
    print("[ВЕЛИКОЛЕПНО] Сборка полностью завершена!")
    print(f"Финальный установщик: {os.path.join(PROJECT_ROOT, 'dist', 'GDI_Launcher_Setup.exe')}")
    print("="*40)

if __name__ == "__main__":
    main()