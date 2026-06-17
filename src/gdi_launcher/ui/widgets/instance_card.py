from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from gdi_launcher.config import GD_ICON_DEFAULT, GEODE_ICON_DEFAULT, ICON_HEIGHT, ICON_WIDTH


class InstanceCard(QFrame):
    def __init__(
        self,
        instance_name: str,
        has_geode: bool,
        main_window,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.instance_name = instance_name
        self.has_geode = has_geode
        self.main_window = main_window
        self.is_selected = False

        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedSize(110, 95)

        self._build_ui()
        self.set_selected_state(False)

    def _build_ui(self) -> None:
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(4, 4, 4, 4)
        card_layout.setSpacing(6)
        card_layout.setAlignment(Qt.AlignCenter)

        self.lbl_gd_icon = QLabel()
        self.lbl_gd_icon.setFixedSize(ICON_WIDTH, ICON_HEIGHT)
        self.lbl_gd_icon.setAlignment(Qt.AlignCenter)

        self._setup_icon()

        card_layout.addWidget(self.lbl_gd_icon, alignment=Qt.AlignCenter)

        self.lbl_name = QLabel(self.instance_name)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setWordWrap(True)

        card_layout.addWidget(self.lbl_name, alignment=Qt.AlignCenter)

    def _setup_icon(self) -> None:
        icon_path = GEODE_ICON_DEFAULT if self.has_geode else GD_ICON_DEFAULT

        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            self.lbl_gd_icon.setPixmap(
                pixmap.scaled(
                    ICON_WIDTH,
                    ICON_HEIGHT,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
            return

        text_label = "GEODE" if self.has_geode else "GD"
        color = "#a855f7" if self.has_geode else "#4CAF50"

        self.lbl_gd_icon.setText(text_label)
        self.lbl_gd_icon.setStyleSheet(
            f"""
            color: {color};
            font-weight: bold;
            border: 1px dashed {color};
            border-radius: 4px;
            """
        )

    def set_selected_state(self, selected: bool) -> None:
        self.is_selected = selected

        background = "#4a4a4a" if selected else "transparent"

        self.lbl_name.setStyleSheet(
            f"""
            QLabel {{
                color: white;
                background-color: {background};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 12px;
            }}
            """
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.main_window.handle_card_selection(self)

        super().mousePressEvent(event)

