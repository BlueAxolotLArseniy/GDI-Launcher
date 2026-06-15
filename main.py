import sys
import os
import threading
import json
import urllib.request
import subprocess
from typing import Optional

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QFrame, QLabel, 
                             QScrollArea, QGridLayout, QInputDialog, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt, QUrl, Signal

# Импортируем наши модули
from gdi_launcher.config import GITHUB_MANIFEST_URL, INSTANCES_DIR
from gdi_launcher.core import sync_and_run_instance
from gdi_launcher.widgets import InstanceCard
from gdi_launcher.dialogs import AddInstanceDialog, InstallProgressDialog, DeleteProgressDialog
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from gdi_launcher.config import BASE_ASSETS_DIR, GD_ICON_DEFAULT, GEODE_ICON_DEFAULT

import ctypes
import sys

INVALID_INSTANCE_NAME_CHARS = set('<>:"/\\|?*')
RESERVED_INSTANCE_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


class ActionRowButton(QFrame):
    """Компактная кликабельная строка меню с отдельной колонкой для иконки."""
    clicked = Signal()

    def __init__(self, icon_text: str, text: str, danger: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ActionRowButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(24)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._danger = danger
        self._build_ui(icon_text, text)
        self._apply_style()

    def _build_ui(self, icon_text: str, text: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 0, 7, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel(icon_text)
        self.icon_label.setFixedWidth(16)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label, 1)

    def _apply_style(self) -> None:
        # Немного оптимизировали код, чтобы не дублировать огромные блоки
        base_color = "#4a2626" if self._danger else "#343434"
        pressed_color = "#5a2b2b" if self._danger else "#404040"
        
        self.setStyleSheet(f"""
            #ActionRowButton {{
                background-color: transparent;
                border: none;
                border-radius: 3px;
            }}
            #ActionRowButton:hover {{
                background-color: {base_color};
            }}
            #ActionRowButton:pressed {{
                background-color: {pressed_color};
            }}
            #ActionRowButton:disabled {{
                background-color: transparent;
            }}
            
            /* Явно запрещаем лейблам иметь свой фон, чтобы они не ломали заливку */
            #ActionRowButton QLabel {{
                background-color: transparent; 
                color: #f4f4f4;
                font-size: 12px;
                font-weight: 600;
            }}
            #ActionRowButton:disabled QLabel {{
                color: #777777;
            }}
        """)

    # ДОБАВЬ ЭТОТ МЕТОД В КЛАСС ActionRowButton:
    def paintEvent(self, event) -> None:
        """Обязательный метод для корректной отрисовки background-color у кастомных виджетов в Qt"""
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QStyle, QStyleOption
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def mousePressEvent(self, event) -> None:
        if self.isEnabled() and event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

# Добавь это сразу после всех импортов
if sys.platform == "win32":
    myappid = 'mycompany.gdi.launcher.1.0' # произвольная уникальная строка
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class GDIMainWindow(QMainWindow):
    """ Главное окно лаунчера """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GDI Launcher")
        self.resize(900, 600)
        
        self.current_process: Optional[subprocess.Popen] = None 
        self.selected_card: Optional[InstanceCard] = None 
        
        os.makedirs(INSTANCES_DIR, exist_ok=True)
        self.init_ui()
        self.refresh_instances()

    def init_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar Panel
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3e3e3e;")
        top_bar.setFixedHeight(50)
        top_layout = QHBoxLayout(top_bar)
        
        btn_add = QPushButton("Добавить...")
        btn_add.clicked.connect(self.open_add_dialog)
        top_layout.addWidget(btn_add)
        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # Body Layout
        body_layout = QHBoxLayout()
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Жестко отключаем горизонтальный скроллбар, чтобы он не мерцал при переносе
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e; border: none;")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #1e1e1e;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_container)
        body_layout.addWidget(self.scroll_area, stretch=3)

        # Right Action Panel
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #252525;")
        right_panel.setFixedWidth(250)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 16, 12, 14)
        right_layout.setSpacing(8)

        self.lbl_selected_icon = QLabel()
        self.lbl_selected_icon.setFixedSize(96, 96)
        self.lbl_selected_icon.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_selected_icon, alignment=Qt.AlignHCenter)
        
        self.lbl_selected = QLabel("Выберите сборку")
        self.lbl_selected.setStyleSheet("color: white; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        self.lbl_selected.setAlignment(Qt.AlignCenter)
        self.lbl_selected.setWordWrap(True)
        right_layout.addWidget(self.lbl_selected)
        right_layout.addSpacing(8)

        action_menu = QWidget()
        action_layout = QVBoxLayout(action_menu)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(1)
        
        self.btn_run = ActionRowButton("▶", "Запустить")
        self.btn_run.clicked.connect(self.run_selected_instance)
        action_layout.addWidget(self.btn_run)

        self.btn_rename = ActionRowButton("⚙", "Переименовать...")
        self.btn_rename.clicked.connect(self.rename_selected_instance)
        action_layout.addWidget(self.btn_rename)

        self.btn_open_folder = ActionRowButton("▸", "Папка")
        self.btn_open_folder.clicked.connect(self.open_selected_instance_folder)
        action_layout.addWidget(self.btn_open_folder)

        self.btn_delete = ActionRowButton("⌫", "Удалить", danger=True)
        self.btn_delete.clicked.connect(self.delete_selected_instance)
        action_layout.addWidget(self.btn_delete)
        right_layout.addWidget(action_menu)
        
        right_layout.addStretch()
        body_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(body_layout)
        self.update_side_panel()

    def handle_card_selection(self, clicked_card: InstanceCard) -> None:
        if self.selected_card:
            self.selected_card.set_selected_state(False)
        self.selected_card = clicked_card
        self.selected_card.set_selected_state(True)
        self.update_side_panel()

    def is_valid_instance_name(self, name: str) -> bool:
        if not name or name in {".", ".."} or os.path.isabs(name):
            return False
        if name.rstrip(" .") != name:
            return False
        if any(char in INVALID_INSTANCE_NAME_CHARS for char in name):
            return False
        if name.upper() in RESERVED_INSTANCE_NAMES:
            return False
        return True

    def get_instance_path(self, instance_name: str) -> str:
        return os.path.normpath(os.path.join(INSTANCES_DIR, instance_name))

    def instance_has_geode(self, instance_name: str) -> bool:
        instance_path = self.get_instance_path(instance_name)
        return (
            os.path.exists(os.path.join(instance_path, "geode")) or
            os.path.exists(os.path.join(instance_path, "Geode.dll"))
        )

    def get_icon_asset_path(self, asset_name: str, configured_path: str) -> str:
        candidates = [
            configured_path,
            os.path.join(BASE_ASSETS_DIR, asset_name),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", asset_name),
        ]
        seen = set()
        for path in candidates:
            normalized = os.path.normpath(path)
            if normalized in seen:
                continue
            seen.add(normalized)
            if os.path.exists(normalized):
                return normalized
        return configured_path

    def update_side_panel(self) -> None:
        has_selection = self.selected_card is not None
        for button in (self.btn_run, self.btn_rename, self.btn_open_folder, self.btn_delete):
            button.setEnabled(has_selection)

        if not has_selection:
            self.lbl_selected_icon.hide() # Полностью скрываем элемент
            self.lbl_selected.setText("Выберите сборку")
            return

        self.lbl_selected_icon.show() # Возвращаем элемент, если инстанс выбран

        instance_name = self.selected_card.instance_name
        has_geode = self.instance_has_geode(instance_name)
        asset_name = "geode_icon.png" if has_geode else "gd_icon.png"
        configured_icon = GEODE_ICON_DEFAULT if has_geode else GD_ICON_DEFAULT
        chosen_icon = self.get_icon_asset_path(asset_name, configured_icon)

        self.lbl_selected.setText(instance_name)
        if os.path.exists(chosen_icon):
            pix = QPixmap(chosen_icon)
            if not pix.isNull():
                self.lbl_selected_icon.setPixmap(pix.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.lbl_selected_icon.setText("")
                self.lbl_selected_icon.setStyleSheet("border: none;")
                return

        else:
            print(f"[-] Иконка сборки не найдена: {chosen_icon}")

        text_label = "GEODE" if has_geode else "GD"
        color = "#a855f7" if has_geode else "#4CAF50"
        self.lbl_selected_icon.setPixmap(QPixmap())
        self.lbl_selected_icon.setText(text_label)
        self.lbl_selected_icon.setStyleSheet(
            f"color: {color}; font-weight: bold; border: 1px dashed {color}; border-radius: 8px;"
        )

    def open_add_dialog(self) -> None:
        versions_list = []
        try:
            print("[*] Получение актуального списка версий с GitHub...")
            with urllib.request.urlopen(GITHUB_MANIFEST_URL, timeout=5) as response:
                raw_json = response.read().decode('utf-8')
                data = json.loads(raw_json)
                versions_list = data.get("versions", [])
        except Exception as e:
            print(f"[-] Не удалось загрузить манифест с GitHub ({e}). Использование резерва.")
            versions_list = [{
                "id": "offline_fallback",
                "display_name": "Нет подключения к сети (Проверьте интернет)",
                "game_url": "",
                "geode": {"supported": False, "url": None}
            }]

        dialog = AddInstanceDialog(versions_list)
        if dialog.exec():
            name, version_info, geode = dialog.get_data()
            if not name or not version_info or not version_info.get("game_url"):
                print("[-] Ошибка: Название инстанса или конфигурация некорректны.")
                return
            if not self.is_valid_instance_name(name):
                QMessageBox.warning(
                    self,
                    "Некорректное название",
                    "Название сборки не должно содержать символы пути или системные имена Windows."
                )
                return
            
            target_dir = self.get_instance_path(name)
            if os.path.exists(target_dir):
                print(f"[-] Ошибка: инстанс '{name}' уже создан!")
                return

            # Вызываем переписанное компактное окно
            progress_dialog = InstallProgressDialog(version_info, target_dir, geode, self)
            progress_dialog.exec()
            self.refresh_instances()

    def refresh_instances(self) -> None:
        # Полностью уничтожаем старые виджеты
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.cards = [] # Инициализируем массив для хранения живых объектов карточек
        
        selected_name = self.selected_card.instance_name if self.selected_card else None
        self.selected_card = None

        if not os.path.exists(INSTANCES_DIR):
            self.update_side_panel()
            return

        folders = [f for f in os.listdir(INSTANCES_DIR) 
                   if os.path.isdir(os.path.join(INSTANCES_DIR, f)) and f != "backup_saves"]

        # Создаем объекты один раз
        for folder in folders:
            card = InstanceCard(folder, self)
            self.cards.append(card)
            if selected_name and folder == selected_name:
                self.selected_card = card
                card.set_selected_state(True)

        self.update_side_panel()

        # Позиционируем их на экране
        self.rearrange_grid()
    
    def resizeEvent(self, event) -> None:
        """Перехватывает изменение размеров окна и перестраивает сетку инстансов"""
        super().resizeEvent(event)
        # Вызываем перерасчет колонок при каждом ресайзе окна
        self.refresh_instances()

    def set_active_process(self, process: subprocess.Popen) -> None:
        self.current_process = process

    def run_selected_instance(self) -> None:
        if self.current_process and self.current_process.poll() is None:
            print("[-] Внимание: Игра уже запущена!")
            return

        if not self.selected_card:
            print("[-] Ошибка: Выберите инстанс!")
            return

        instance_name = self.selected_card.instance_name
        
        # Запускаем изоляцию и синхронизацию в отдельном системном потоке, передавая callback для сохранения дескриптора процесса
        thread = threading.Thread(
            target=sync_and_run_instance, 
            args=(instance_name, self.set_active_process)
        )
        thread.start()

    def delete_selected_instance(self) -> None:
        if not self.selected_card:
            print("[-] Ошибка: Сначала выберите сборку для удаления!")
            return

        if self.current_process and self.current_process.poll() is None:
            print("[-] Ошибка: Нельзя удалить сборку, пока игра запущена!")
            return

        instance_name = self.selected_card.instance_name
        reply = QMessageBox.question(
            self,
            "Удалить сборку?",
            f"Удалить сборку '{instance_name}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        target_dir = self.get_instance_path(instance_name)

        progress_dialog = DeleteProgressDialog(target_dir, instance_name, self)
        progress_dialog.exec()
        self.refresh_instances()

    def rename_selected_instance(self) -> None:
        if not self.selected_card:
            print("[-] Ошибка: Сначала выберите сборку для переименования!")
            return

        if self.current_process and self.current_process.poll() is None:
            QMessageBox.warning(self, "Игра запущена", "Нельзя переименовать сборку, пока игра запущена.")
            return

        old_name = self.selected_card.instance_name
        new_name, ok = QInputDialog.getText(
            self,
            "Переименовать сборку",
            "Новое название:",
            QLineEdit.Normal,
            old_name
        )
        if not ok:
            return

        new_name = new_name.strip()
        if new_name == old_name:
            return
        if not self.is_valid_instance_name(new_name):
            QMessageBox.warning(
                self,
                "Некорректное название",
                "Название сборки не должно содержать символы пути или системные имена Windows."
            )
            return

        old_dir = self.get_instance_path(old_name)
        new_dir = self.get_instance_path(new_name)
        if os.path.exists(new_dir):
            QMessageBox.warning(self, "Название занято", f"Сборка '{new_name}' уже существует.")
            return

        try:
            os.rename(old_dir, new_dir)
            self.selected_card.instance_name = new_name
            self.refresh_instances()
        except OSError as e:
            QMessageBox.critical(self, "Ошибка переименования", f"Не удалось переименовать сборку:\n{e}")

    def open_selected_instance_folder(self) -> None:
        if not self.selected_card:
            print("[-] Ошибка: Сначала выберите сборку!")
            return

        target_dir = self.get_instance_path(self.selected_card.instance_name)
        if not os.path.exists(target_dir):
            QMessageBox.warning(self, "Папка не найдена", "Папка выбранной сборки не найдена.")
            return

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(target_dir)):
            QMessageBox.warning(self, "Ошибка открытия", "Не удалось открыть папку сборки.")
    
    def rearrange_grid(self) -> None:
        if not hasattr(self, 'cards') or not self.cards:
            return

        # Отвязываем виджеты от структуры сетки, но НЕ удаляем их физически!
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        # Вычисляем колонки на основе ширины scroll_area
        card_width_with_spacing = 110 + 15
        scroll_area_width = self.scroll_area.viewport().width()
        available_width = scroll_area_width - 30 - 20 # Минус маргины и ширина скроллбара
        
        columns = max(1, available_width // card_width_with_spacing)

        # Быстро раскидываем существующие карточки по новым местам
        row, col = 0, 0
        for card in self.cards:
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
    def resizeEvent(self, event) -> None:
        """Срабатывает при растягивании окна пользователем"""
        super().resizeEvent(event)
        self.rearrange_grid() # Перестраиваем координаты без уничтожения объектов

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    icon_path = os.path.join(BASE_ASSETS_DIR, "GDI.ico")
    app.setWindowIcon(QIcon(icon_path))
    
    window = GDIMainWindow()
    window.show()
    sys.exit(app.exec())
