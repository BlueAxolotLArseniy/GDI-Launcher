import os
import shutil
import subprocess
from .config import INSTANCES_DIR

def get_appdata_path() -> str:
    """ Вычисляет и возвращает абсолютный путь к папке сейвов Geometry Dash в AppData """
    return os.path.join(os.environ['LOCALAPPDATA'], "GeometryDash")

def copy_directory_contents(src: str, dst: str) -> None:
    """ Безопасно копирует всё содержимое одной папки в другую (файлы и подпапки) """
    if not os.path.exists(src):
        return
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s_path = os.path.join(src, item)
        d_path = os.path.join(dst, item)
        if os.path.isdir(s_path):
            if os.path.exists(d_path):
                shutil.rmtree(d_path)
            shutil.copytree(s_path, d_path)
        else:
            shutil.copy2(s_path, d_path)

def sync_and_run_instance(instance_name: str, on_process_start_callback=None) -> None:
    target_dir = os.path.join(INSTANCES_DIR, instance_name)
    instance_saves = os.path.join(target_dir, "saves")
    appdata_gd = get_appdata_path()
    backup_dir = os.path.join(INSTANCES_DIR, "backup_saves")
    exe_path = os.path.join(target_dir, "GeometryDash.exe")

    if not os.path.exists(exe_path):
        print(f"[-] Ошибка: {exe_path} не найден!")
        return

    print(f"\n--- ПОДГОТОВКА СЕЙВОВ ДЛЯ '{instance_name}' ---")
    
    # 1. Безопасное резервирование оригинальной игры
    try:
        if os.path.exists(appdata_gd) and os.listdir(appdata_gd):
            # ЗАЩИТА: Если папка бэкапа уже существует и НЕ пуста, значит прошлый запуск 
            # завершился аварийно, и там лежат наши ОРИГИНАЛЬНЫЕ сейвы. Не затираем их!
            if not (os.path.exists(backup_dir) and os.listdir(backup_dir)):
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
                shutil.copytree(appdata_gd, backup_dir)
                print("[+] Оригинальные сейвы успешно временно перемещены в backup_saves.")
            else:
                print("[!] В backup_saves обнаружен старый бэкап. Защита активирована, не перезаписываем.")
            
            # В любом случае очищаем AppData, чтобы накатать сейвы инстанса
            shutil.rmtree(appdata_gd)
    except Exception as e:
        print(f"[-] Ошибка при создании бекапа оригинальной игры: {e}.")

    os.makedirs(appdata_gd, exist_ok=True)

    # 2. Накатываем сейвы инстанса (если они есть)
    if os.path.exists(instance_saves) and os.listdir(instance_saves):
        copy_directory_contents(instance_saves, appdata_gd)
        print(f"[+] Сейвы инстанса '{instance_name}' успешно загружены в AppData.")

    # Запуск игры
    print(f"[+] Запускаем {instance_name}...")
    try:
        process = subprocess.Popen(exe_path, cwd=target_dir)
        if on_process_start_callback:
            on_process_start_callback(process)
        process.wait()
    except Exception as e:
        print(f"[-] Ошибка запуска процесса: {e}")
        return
    
    print(f"\n--- СИНХРОНИЗАЦИЯ ПОСЛЕ ВЫХОДА ИЗ ИГРЫ ---")
    
    # 3. Сохраняем прогресс инстанса обратно в его личную папку
    try:
        os.makedirs(instance_saves, exist_ok=True)
        if os.path.exists(appdata_gd):
            # Очищаем старые файлы в папке инстанса перед записью свежих
            for item in os.listdir(instance_saves):
                i_path = os.path.join(instance_saves, item)
                try:
                    if os.path.isdir(i_path): shutil.rmtree(i_path)
                    else: os.remove(i_path)
                except OSError:
                    continue
                    
            copy_directory_contents(appdata_gd, instance_saves)
            shutil.rmtree(appdata_gd)
            print(f"[+] Прогресс инстанса '{instance_name}' успешно сохранен в его папку.")
    except Exception as e:
        print(f"[-] Ошибка при сохранении прогресса инстанса: {e}")

    # 4. КРИТИЧЕСКИЙ ШАГ: Возвращаем оригинальные сейвы основной ГД на их законное место
    try:
        if os.path.exists(backup_dir) and os.listdir(backup_dir):
            os.makedirs(appdata_gd, exist_ok=True)
            copy_directory_contents(backup_dir, appdata_gd)
            shutil.rmtree(backup_dir)
            print("[ВЕЛИКОЛЕПНО] Оригинальные сейвы основной GD успешно возвращены в AppData!")
        else:
            print("[?] Папка бэкапа пуста. Возврат оригинальных сейвов не требуется.")
    except Exception as e:
        print(f"[-] КРИТИЧЕСКАЯ ОШИБКА при восстановлении оригинальных сейвов: {e}")