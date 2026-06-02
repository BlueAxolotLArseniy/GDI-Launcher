from PySide6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox, 
                             QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout, 
                             QLabel, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt
from typing import Tuple, List, Optional
# Импортируем воркеры
from .workers import DownloadExtractWorker, DeleteWorker

class AddInstanceDialog(QDialog):
    """ Диалог создания новой сборки """
    def __init__(self, versions_data: list) -> None:
        super().__init__()
        self.setWindowTitle("Создать инстанс")
        self.setFixedWidth(340)
        self.versions_data = versions_data
        
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.version_combo = QComboBox()
        
        for v in self.versions_data:
            self.version_combo.addItem(v["display_name"], v)
            
        self.geode_check = QCheckBox("Привязать Geode")
        
        layout.addRow("Название:", self.name_input)
        layout.addRow("Версия:", self.version_combo)
        layout.addRow(self.geode_check)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("ОК")
        btn_ok.clicked.connect(self.accept) 
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject) 
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

        self.version_combo.currentIndexChanged.connect(self.sync_geode_checkbox_state)
        self.sync_geode_checkbox_state()

    def sync_geode_checkbox_state(self) -> None:
        idx = self.version_combo.currentIndex()
        if idx >= 0:
            version_info = self.version_combo.itemData(idx)
            is_supported = version_info.get("geode", {}).get("supported", False)
            self.geode_check.setEnabled(is_supported)
            if not is_supported:
                self.geode_check.setChecked(False)

    def get_data(self) -> Tuple[str, dict, bool]:
        idx = self.version_combo.currentIndex()
        version_info = self.version_combo.itemData(idx) if idx >= 0 else {}
        return self.name_input.text().strip(), version_info, self.geode_check.isChecked()


class InstallProgressDialog(QDialog):
    """ Супер-компактное окно установки без логов, с автозакрытием и защитой """
    def __init__(self, version_info: dict, target_dir: str, install_geode: bool, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Установка сборки...")
        self.setFixedSize(420, 110)
        
        self.is_finished = False
        self.worker_args = (version_info, target_dir, install_geode)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        self.lbl_status = QLabel("Подготовка к установке...")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #bbbbbb;")
        self.lbl_status.setWordWrap(True) 
        layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.start_worker()

    def start_worker(self) -> None:
        version_info, target_dir, install_geode = self.worker_args
        self.worker = DownloadExtractWorker(version_info, target_dir, install_geode)
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        
        # ВАЖНО: Подключаемся к новому уникальному сигналу воркера!
        self.worker.installation_finished.connect(self.on_process_finished)
        self.worker.start()

    def on_process_finished(self, success: bool, log_entries: list) -> None:
        self.is_finished = True
        
        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText("Готово!")
            # Теперь этот метод гарантированно вызовется без внутренних TypeError!
            self.done(QDialog.Accepted) 
        else:
            reply = QMessageBox.critical(
                self,
                "Ошибка установки",
                "Не удалось скачать или распаковать файлы сборки.\nХотите попробовать еще раз?",
                QMessageBox.Retry | QMessageBox.Cancel,
                QMessageBox.Retry
            )
            
            if reply == QMessageBox.Retry:
                self.is_finished = False
                self.progress_bar.setValue(0)
                self.lbl_status.setText("Повторная попытка...")
                self.start_worker()
            else:
                self.done(QDialog.Rejected)

    def closeEvent(self, event) -> None:
        """ Защита от случайного прерывания загрузки по клику на крестик """
        if not self.is_finished:
            reply = QMessageBox.question(
                self, 
                "Прерывание установки",
                "Вы уверены, что хотите остановить установку? Файлы этой сборки будут повреждены.",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class DeleteProgressDialog(QDialog):
    """ Окно визуализации процесса удаления """
    def __init__(self, target_dir: str, instance_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Удаление сборки...")
        self.setFixedSize(400, 110)
        
        layout = QVBoxLayout(self)
        self.lbl_status = QLabel(f"Подготовка к удалению '{instance_name}'...")
        layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        self.worker = DeleteWorker(target_dir, instance_name)
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        
        # ВАЖНО: Подключаемся к новому уникальному сигналу удаления!
        self.worker.deletion_finished.connect(self.accept)
        self.worker.start()