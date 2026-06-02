import os
import zipfile
import urllib.request
from PySide6.QtCore import QThread, Signal
from typing import List

class DownloadExtractWorker(QThread):
    """ Фоновый поток скачивания и распаковки игры и Geode """
    status_changed = Signal(str)
    progress_changed = Signal(int)
    # Старый сигнал finished удален, чтобы избежать конфликтов с QThread
    installation_finished = Signal(bool, list)

    def __init__(self, version_info: dict, target_dir: str, install_geode: bool) -> None:
        super().__init__()
        self.version_info = version_info
        self.target_dir = target_dir
        self.install_geode = install_geode
        self.log_entries: List[str] = []

    def run(self) -> None:
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            
            # 1. Скачивание игры
            game_url = self.version_info["game_url"]
            game_zip = os.path.join(self.target_dir, "game_temp.zip")
            self.status_changed.emit("Скачивание файлов Geometry Dash...")
            self.log_entries.append(f"[*] Скачивание игры из релиза: {game_url}")
            
            def download_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = int((block_num * block_size / total_size) * 100)
                    self.progress_changed.emit(min(percent, 100))

            urllib.request.urlretrieve(game_url, game_zip, reporthook=download_hook)
            
            # 2. Распаковка игры
            self.log_entries.append("[*] Распаковка чистой сборки Geometry Dash...")
            self.progress_changed.emit(0)
            
            with zipfile.ZipFile(game_zip, 'r') as zip_ref:
                files = zip_ref.namelist()
                total_files = len(files)
                for idx, file in enumerate(files):
                    zip_ref.extract(file, self.target_dir)
                    if total_files > 0:
                        percent = int(((idx + 1) / total_files) * 100)
                        self.progress_changed.emit(percent)
                        short_name = os.path.basename(file) if os.path.basename(file) else file
                        self.status_changed.emit(f"Распаковка [{idx + 1}/{total_files}]: {short_name}")
            
            os.remove(game_zip)
            self.log_entries.append("[OK] Файлы игры успешно извлечены.")
            
            # 3. Работа с Geode
            if self.install_geode and self.version_info.get("geode", {}).get("supported", False):
                geode_url = self.version_info["geode"]["url"]
                geode_zip = os.path.join(self.target_dir, "geode_temp.zip")
                
                self.status_changed.emit("Скачивание совместимой версии Geode...")
                self.log_entries.append(f"[*] Скачивание Geode: {geode_url}")
                self.progress_changed.emit(0)
                
                urllib.request.urlretrieve(geode_url, geode_zip, reporthook=download_hook)
                self.log_entries.append("[*] Инъекция DLL и распаковка компонентов Geode...")
                self.progress_changed.emit(0)
                
                with zipfile.ZipFile(geode_zip, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    total_files = len(files)
                    for idx, file in enumerate(files):
                        zip_ref.extract(file, self.target_dir)
                        if total_files > 0:
                            percent = int(((idx + 1) / total_files) * 100)
                            self.progress_changed.emit(percent)
                            short_name = os.path.basename(file) if os.path.basename(file) else file
                            self.status_changed.emit(f"Внедрение Geode [{idx + 1}/{total_files}]: {short_name}")
                            
                os.remove(geode_zip)
                self.log_entries.append("[OK] Модификатор Geode успешно интегрирован.")
            
            # 4. Инициализация окружения инстанса
            saves_path = os.path.join(self.target_dir, "saves")
            os.makedirs(saves_path, exist_ok=True)
            
            # Создаем структуру steam_appid.txt
            with open(os.path.join(self.target_dir, "steam_appid.txt"), "w") as f:
                f.write("322170")

            # Создаем пустые файлы сейвов, если их нет
            empty_files = ["CCGameManager.dat", "CCLocalLevels.dat", "CCGameManager2.dat", "CCLocalLevels2.dat"]
            for file_name in empty_files:
                file_path = os.path.join(saves_path, file_name)
                if not os.path.exists(file_path):
                    with open(file_path, "wb") as f:
                        f.write(b"") # Создаем пустой файл

            # ИСПРАВЛЕНО: Добавлен обязательный триггер успешного финиша!
            self.installation_finished.emit(True, self.log_entries)

        except Exception as e:
            self.log_entries.append(f"[-] КРИТИЧЕСКАЯ ОШИБКА СЕТИ ИЛИ АРХИВА: {str(e)}")
            # ИСПРАВЛЕНО: Передаем False, так как произошла ошибка установки
            self.installation_finished.emit(False, self.log_entries)


class DeleteWorker(QThread):
    """ Фоновый поток для чистого пофайлового удаления инстанса """
    status_changed = Signal(str)
    progress_changed = Signal(int)
    # Старый сигнал finished удален
    deletion_finished = Signal(bool, str)

    def __init__(self, target_dir: str, instance_name: str) -> None:
        super().__init__()
        self.target_dir = target_dir
        self.instance_name = instance_name

    def run(self) -> None:
        try:
            if os.path.exists(self.target_dir):
                self.status_changed.emit("Сканирование директории...")
                files_to_delete = []
                dirs_to_delete = []
                
                for root, dirs, files in os.walk(self.target_dir, topdown=False):
                    for name in files:
                        files_to_delete.append(os.path.join(root, name))
                    for name in dirs:
                        dirs_to_delete.append(os.path.join(root, name))
                
                total_items = len(files_to_delete) + len(dirs_to_delete) + 1
                current_item = 0

                for f in files_to_delete:
                    os.remove(f)
                    current_item += 1
                    if total_items > 0:
                        self.progress_changed.emit(int((current_item / total_items) * 100))
                        if current_item % 5 == 0:
                            self.status_changed.emit(f"Удаление: {os.path.basename(f)}")
                
                for d in dirs_to_delete:
                    os.rmdir(d)
                    current_item += 1
                    if total_items > 0:
                        self.progress_changed.emit(int((current_item / total_items) * 100))
                
                if os.path.exists(self.target_dir):
                    os.rmdir(self.target_dir)
                
                self.progress_changed.emit(100)
                self.deletion_finished.emit(True, f"[+] Сборка '{self.instance_name}' успешно удалена.")
            else:
                # ИСПРАВЛЕНО: Заменен старый сигнал на deletion_finished
                self.deletion_finished.emit(False, "[-] Папка не найдена.")
        except Exception as e:
            # ИСПРАВЛЕНО: Заменен старый сигнал на deletion_finished
            self.deletion_finished.emit(False, f"[-] Ошибка удаления: {str(e)}")