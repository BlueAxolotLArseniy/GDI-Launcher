import os
import sys

# Автоматически определяем правильные базовые директории
if hasattr(sys, '_MEIPASS'):
    # РЕЖИМ .EXE: Ассеты зашиты внутрь экзешника и лежат во временной памяти
    BASE_ASSETS_DIR = os.path.join(sys._MEIPASS, "assets")
    # Папка инстансов создается рядом с самим экзешником
    BASE_RUN_DIR = os.path.dirname(sys.executable)
else:
    # РЕЖИМ КОДА: Запуск из IDE (выходим на уровень выше к main.py)
    BASE_RUN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_ASSETS_DIR = os.path.join(BASE_RUN_DIR, "assets")

# Размеры элементов интерфейса
ICON_WIDTH: int = 48
ICON_HEIGHT: int = 48
MAX_COLUMNS: int = 6

# Дефолтные пути к ассетам (теперь они АБСОЛЮТНЫЕ и никогда не потеряются)
GD_ICON_DEFAULT: str = os.path.normpath(os.path.join(BASE_ASSETS_DIR, "gd_icon.png"))
GEODE_ICON_DEFAULT: str = os.path.normpath(os.path.join(BASE_ASSETS_DIR, "geode_icon.png"))

# Репозиторий с манифестом версий
GITHUB_MANIFEST_URL: str = "https://raw.githubusercontent.com/BlueAxolotLArseniy/GDI-Launcher/refs/heads/main/versions.json"

# Основная папка для хранения инстансов (всегда создается рядом с лаунчером)
INSTANCES_DIR: str = os.path.normpath(os.path.join(BASE_RUN_DIR, "instances"))