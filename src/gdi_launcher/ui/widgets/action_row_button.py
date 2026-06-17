from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStyle, QStyleOption


class ActionRowButton(QFrame):
    """
    Compact clickable row used in the right action panel.

    This widget behaves like a small menu item:
    - icon column on the left;
    - text label on the right;
    - hover / pressed states;
    - optional danger styling.
    """

    clicked = Signal()

    def __init__(
        self,
        icon_text: str,
        text: str,
        danger: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._danger = danger
        self._alert = False

        self.setObjectName("ActionRowButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(24)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._build_ui(icon_text, text)
        self._apply_style()

    def set_alert_state(self, active: bool) -> None:
        if self._alert == active:
            return

        self._alert = active
        self._apply_style()
        self.update()

    def set_text(self, text: str) -> None:
        self.text_label.setText(text)

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
        if self._alert:
            background_color = "#7f1d1d"
            border = "1px solid #ef4444"
            hover_color = "#991b1b"
            pressed_color = "#5f1515"
            label_color = "#ffffff"
        else:
            background_color = "transparent"
            border = "none"
            hover_color = "#4a2626" if self._danger else "#343434"
            pressed_color = "#5a2b2b" if self._danger else "#404040"
            label_color = "#f4f4f4"

        self.setStyleSheet(
            f"""
            #ActionRowButton {{
                background-color: {background_color};
                border: {border};
                border-radius: 3px;
            }}

            #ActionRowButton:hover {{
                background-color: {hover_color};
            }}

            #ActionRowButton:pressed {{
                background-color: {pressed_color};
            }}

            #ActionRowButton:disabled {{
                background-color: transparent;
            }}

            #ActionRowButton QLabel {{
                background-color: transparent;
                color: {label_color};
                font-size: 12px;
                font-weight: 600;
            }}

            #ActionRowButton:disabled QLabel {{
                color: #777777;
            }}
            """
        )

    def paintEvent(self, event) -> None:
        """
        Required for correct stylesheet background rendering on custom Qt widgets.
        """
        option = QStyleOption()
        option.initFrom(self)

        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

        super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.isEnabled() and event.button() == Qt.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)
