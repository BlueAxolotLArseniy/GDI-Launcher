import os
import sys
import zipfile
import subprocess
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QWidget, QLabel, QLineEdit, 
                             QPushButton, QProgressBar, QFileDialog, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.normpath(os.path.join(sys._MEIPASS, relative_path))
    return os.path.normpath(os.path.join(os.path.abspath("."), relative_path))

class InstallWorker(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, zip_path: str, target_dir: str, create_desktop_shortcut: bool) -> None:
        super().__init__()
        self.zip_path = os.path.normpath(zip_path)
        self.target_dir = os.path.normpath(target_dir)
        self.create_desktop_shortcut = create_desktop_shortcut

    def run(self) -> None:
        try:
            self.status_changed.emit("Создание директории...")
            os.makedirs(self.target_dir, exist_ok=True)

            if not os.path.exists(self.zip_path):
                self.finished.emit(False, "Критическая ошибка: Архив лаунчера не найден внутри установщика.")
                return

            self.status_changed.emit("Распаковка файлов лаунчера...")
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                total_files = len(files)
                for idx, file in enumerate(files):
                    zip_ref.extract(file, self.target_dir)
                    if total_files > 0:
                        percent = int(((idx + 1) / total_files) * 100)
                        self.progress_changed.emit(percent)
                        if idx % 10 == 0:
                            self.status_changed.emit(f"Извлечение: {os.path.basename(file)}")

            # --- ВАЖНО: СОЗДАЕМ ПАПКИ ДЛЯ СЕЙВОВ ---
            self.status_changed.emit("Настройка структуры папок...")
            backup_dir = os.path.join(self.target_dir, "instances", "backup_saves")
            os.makedirs(backup_dir, exist_ok=True)

            exe_path = os.path.normpath(os.path.join(self.target_dir, "GDI_App.exe"))
            
            if self.create_desktop_shortcut:
                self.status_changed.emit("Создание ярлыка на Рабочем столе...")
                desktop = os.path.normpath(os.path.join(os.environ["USERPROFILE"], "Desktop"))
                shortcut_path = os.path.normpath(os.path.join(desktop, "GDI Launcher.lnk"))
                
                ps_cmd = (
                    f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{shortcut_path}');"
                    f"$s.TargetPath='{exe_path}';"
                    f"$s.WorkingDirectory='{self.target_dir}';"
                    f"$s.IconLocation='{exe_path},0';"  # <--- ВОТ ЭТА СТРОКА
                    f"$s.Save()"
                )
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)

            self.progress_changed.emit(100)
            self.finished.emit(True, "Установка успешно завершена!")
        except Exception as e:
            self.finished.emit(False, f"Ошибка при установке: {str(e)}")

class GDIInstaller(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Установка GDI Launcher")
        self.setFixedSize(500, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        raw_path = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "GDI-Launcher")
        self.default_path = os.path.normpath(raw_path)

        self.init_ui()
        self.apply_styles()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        self.page_welcome = self.create_welcome_page()
        self.page_path = self.create_path_page()
        self.page_progress = self.create_progress_page()

        self.pages.addWidget(self.page_welcome)
        self.pages.addWidget(self.page_path)
        self.pages.addWidget(self.page_progress)

        self.bottom_bar = QWidget()
        self.bottom_bar.setObjectName("BottomBar")
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(20, 15, 20, 15)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_back = QPushButton("Назад")
        self.btn_next = QPushButton("Далее >")

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_back.clicked.connect(self.go_back)
        self.btn_next.clicked.connect(self.go_next)

        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_back)
        bottom_layout.addWidget(self.btn_next)

        main_layout.addWidget(self.bottom_bar)
        self.update_buttons()

    def create_welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Установка GDI Launcher")
        title.setObjectName("Title")
        desc = QLabel(
            "Программа установит GDI Launcher на ваш компьютер.\n\n"
            "Рекомендуется закрыть Geometry Dash перед продолжением.\n"
            "Нажмите «Далее», чтобы выбрать папку установки."
        )
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addSpacing(15)
        layout.addWidget(desc)
        layout.addStretch()
        return page

    def create_path_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        title = QLabel("Выбор папки установки")
        title.setObjectName("SubTitle")
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(QLabel("Папка назначения:"))
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.default_path)
        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.btn_browse)
        layout.addLayout(path_layout)
        
        layout.addSpacing(20)
        self.chk_shortcut = QCheckBox("Создать ярлык на Рабочем столе")
        self.chk_shortcut.setChecked(True)
        layout.addWidget(self.chk_shortcut)
        layout.addStretch()
        return page

    def create_progress_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        self.lbl_status = QLabel("Подготовка к копированию...")
        self.lbl_status.setObjectName("SubTitle")
        self.progress_bar = QProgressBar()
        layout.addWidget(self.lbl_status)
        layout.addSpacing(20)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        return page

    def browse_folder(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите папку для установки", self.path_input.text())
        if dir_path:
            full_path = os.path.join(dir_path, "GDI-Launcher")
            self.path_input.setText(os.path.normpath(full_path))

    def update_buttons(self) -> None:
        idx = self.pages.currentIndex()
        self.btn_back.setVisible(idx == 1)
        self.btn_next.setText("Установить" if idx == 1 else ("Готово" if idx == 2 and self.progress_bar.value() == 100 else "Далее >"))

    def go_back(self) -> None:
        if self.pages.currentIndex() > 0:
            self.pages.setCurrentIndex(self.pages.currentIndex() - 1)
            self.update_buttons()

    def go_next(self) -> None:
        idx = self.pages.currentIndex()
        if idx == 0:
            self.pages.setCurrentIndex(1)
            self.update_buttons()
        elif idx == 1:
            self.pages.setCurrentIndex(2)
            self.update_buttons()
            self.btn_next.setEnabled(False)
            self.btn_back.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            
            zip_resource = get_resource_path("launcher.zip") 
            target_directory = os.path.normpath(self.path_input.text().strip())
            
            self.worker = InstallWorker(zip_resource, target_directory, self.chk_shortcut.isChecked())
            self.worker.status_changed.connect(self.lbl_status.setText)
            self.worker.progress_changed.connect(self.progress_bar.setValue)
            self.worker.finished.connect(self.on_install_finished)
            self.worker.start()

    def on_install_finished(self, success: bool, message: str) -> None:
        self.lbl_status.setText(message)
        self.btn_next.setEnabled(True)
        self.btn_next.setText("Завершить")
        self.btn_next.clicked.disconnect()
        if success:
            self.lbl_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.btn_next.clicked.connect(self.accept)
        else:
            self.lbl_status.setStyleSheet("color: #f44336; font-weight: bold;")
            self.btn_next.clicked.connect(self.reject)

    def apply_styles(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; }
            QLabel { color: #dcdcdc; }
            #Title { font-size: 22px; font-weight: bold; color: #4CAF50; }
            #SubTitle { font-size: 16px; font-weight: bold; color: #ffffff; }
            QLineEdit { background-color: #2b2b2b; border: 1px solid #3b3b3b; border-radius: 4px; padding: 5px; color: white; }
            #BottomBar { background-color: #111111; border-top: 1px solid #2b2b2b; }
            QPushButton { background-color: #333333; border: 1px solid #444444; border-radius: 4px; padding: 6px 15px; color: white; min-width: 75px; }
            QPushButton:hover { background-color: #444444; }
            QPushButton:pressed { background-color: #222222; }
            QPushButton[text*="Далее"], QPushButton[text="Установить"], QPushButton[text="Завершить"] { background-color: #4CAF50; border: 1px solid #45a049; font-weight: bold; }
            QPushButton[text*="Далее"]:hover, QPushButton[text="Установить"]:hover, QPushButton[text="Завершить"]:hover { background-color: #45a049; }
            QProgressBar { border: 1px solid #333; border-radius: 4px; background-color: #2b2b2b; text-align: center; color: white; font-weight: bold; height: 20px; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
            QCheckBox { color: #dcdcdc; spacing: 5px; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    installer = GDIInstaller()
    installer.show()
    sys.exit(app.exec())