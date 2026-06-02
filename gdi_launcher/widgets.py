import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtCore import Qt
from .config import ICON_WIDTH, ICON_HEIGHT, GD_ICON_DEFAULT, GEODE_ICON_DEFAULT, INSTANCES_DIR

class InstanceCard(QFrame):
    """ Виджет плитки инстанса """
    def __init__(self, instance_name: str, main_window) -> None:
        super().__init__()
        self.instance_name = instance_name
        self.main_window = main_window
        self.is_selected = False
        
        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedSize(110, 95)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(4, 4, 4, 4)
        card_layout.setSpacing(6)
        card_layout.setAlignment(Qt.AlignCenter)

        self.lbl_gd_icon = QLabel()
        self.lbl_gd_icon.setFixedSize(ICON_WIDTH, ICON_HEIGHT)
        self.lbl_gd_icon.setAlignment(Qt.AlignCenter)
        
        # 1. Автоматически проверяем, установлен ли Geode в этой конкретной папке
        instance_path = os.path.join(INSTANCES_DIR, self.instance_name)
        has_geode = os.path.exists(os.path.join(instance_path, "geode")) or os.path.exists(os.path.join(instance_path, "Geode.dll"))
        
        # 2. Выбираем нужный путь к иконке
        chosen_icon = GEODE_ICON_DEFAULT if has_geode else GD_ICON_DEFAULT
        
        # 3. Отрисовываем выбранную иконку (или текстовую заглушку, если файла картинки нет)
        if os.path.exists(chosen_icon):
            pix = QPixmap(chosen_icon).scaled(ICON_WIDTH, ICON_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_gd_icon.setPixmap(pix)
        else:
            # Красивая заглушка: фиолетовая для Geode, зеленая для обычной GD
            text_label = "GEODE" if has_geode else "GD"
            color = "#a855f7" if has_geode else "#4CAF50" 
            self.lbl_gd_icon.setText(text_label)
            self.lbl_gd_icon.setStyleSheet(f"color: {color}; font-weight: bold; border: 1px dashed {color}; border-radius: 4px;")

        card_layout.addWidget(self.lbl_gd_icon, alignment=Qt.AlignCenter)

        self.lbl_name = QLabel(self.instance_name)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setWordWrap(True) 
        self.set_selected_state(False)
        card_layout.addWidget(self.lbl_name, alignment=Qt.AlignCenter)

    def set_selected_state(self, selected: bool) -> None:
        self.is_selected = selected
        if self.is_selected:
            self.lbl_name.setStyleSheet("QLabel { color: white; background-color: #4a4a4a; border-radius: 3px; padding: 2px 6px; font-size: 12px; }")
        else:
            self.lbl_name.setStyleSheet("QLabel { color: white; background-color: transparent; border-radius: 3px; padding: 2px 6px; font-size: 12px; }")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.main_window.handle_card_selection(self)