import sys
import os
import threading
import json
import urllib.request
import subprocess
from typing import Optional

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QFrame, QLabel, 
                             QScrollArea, QGridLayout)
from PySide6.QtCore import Qt

# Импортируем наши модули
from gdi_launcher.config import MAX_COLUMNS, GITHUB_MANIFEST_URL, INSTANCES_DIR
from gdi_launcher.core import sync_and_run_instance
from gdi_launcher.widgets import InstanceCard
from gdi_launcher.dialogs import AddInstanceDialog, InstallProgressDialog, DeleteProgressDialog
from PySide6.QtGui import QIcon
from gdi_launcher.config import BASE_ASSETS_DIR

import ctypes
import sys

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
        
        self.lbl_selected = QLabel("Выберите сборку")
        self.lbl_selected.setStyleSheet("color: white; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        self.lbl_selected.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_selected)
        
        btn_run = QPushButton("Запустить")
        btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        btn_run.clicked.connect(self.run_selected_instance)
        right_layout.addWidget(btn_run)

        btn_delete = QPushButton("Удалить сборку")
        btn_delete.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 8px; margin-top: 5px;")
        btn_delete.clicked.connect(self.delete_selected_instance)
        right_layout.addWidget(btn_delete)
        
        right_layout.addStretch()
        body_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(body_layout)

    def handle_card_selection(self, clicked_card: InstanceCard) -> None:
        if self.selected_card:
            self.selected_card.set_selected_state(False)
        self.selected_card = clicked_card
        self.selected_card.set_selected_state(True)
        self.lbl_selected.setText(clicked_card.instance_name)

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
            
            target_dir = os.path.join(INSTANCES_DIR, name)
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
            self.lbl_selected.setText("Выберите сборку")
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

        if not self.selected_card:
            self.lbl_selected.setText("Выберите сборку")

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
        target_dir = os.path.join(INSTANCES_DIR, instance_name)

        progress_dialog = DeleteProgressDialog(target_dir, instance_name, self)
        progress_dialog.exec()
        self.refresh_instances()
    
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