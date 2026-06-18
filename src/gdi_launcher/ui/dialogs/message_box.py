from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget


def ask_yes_no(
    parent: QWidget | None,
    title: str,
    text: str,
    yes_text: str,
    no_text: str,
) -> bool:
    message_box = QMessageBox(QMessageBox.Question, title, text, QMessageBox.NoButton, parent)
    yes_button = message_box.addButton(yes_text, QMessageBox.YesRole)
    no_button = message_box.addButton(no_text, QMessageBox.NoRole)

    if isinstance(no_button, QPushButton):
        message_box.setDefaultButton(no_button)
        message_box.setEscapeButton(no_button)

    message_box.exec()
    return message_box.clickedButton() == yes_button
