from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
)

from gdi_launcher.services.translation_service import TranslationService
from gdi_launcher.ui.dialogs.message_box import ask_yes_no
from gdi_launcher.workers.install_worker import InstallWorker


class InstallProgressDialog(QDialog):
    def __init__(
        self,
        version_info: dict[str, Any],
        target_dir: str,
        install_geode: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.version_info = version_info
        self.target_dir = target_dir
        self.install_geode = install_geode
        self.worker: InstallWorker | None = None
        self.is_finished = False
        self.translation_service = TranslationService()

        self.setWindowTitle(self.tr("install.window_title"))
        self.setFixedSize(420, 110)

        self._build_ui()
        self.start_worker()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        self.lbl_status = QLabel(self.tr("install.preparing"))
        self.lbl_status.setStyleSheet("font-size: 11px; color: #bbbbbb;")
        self.lbl_status.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        layout.addWidget(self.lbl_status)
        layout.addWidget(self.progress_bar)

    def start_worker(self) -> None:
        self.worker = InstallWorker(self.version_info, self.target_dir, self.install_geode)
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.installation_finished.connect(self.on_installation_finished)
        self.worker.start()

    def on_installation_finished(self, success: bool, log_entries: list[str]) -> None:
        self.is_finished = True

        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText(self.tr("install.done"))
            self.done(QDialog.Accepted)
            return

        reply = QMessageBox.critical(
            self,
            self.tr("install.error.title"),
            self.tr("install.error.body"),
            QMessageBox.Retry | QMessageBox.Cancel,
            QMessageBox.Retry,
        )

        if reply == QMessageBox.Retry:
            self.is_finished = False
            self.progress_bar.setValue(0)
            self.lbl_status.setText(self.tr("install.retrying"))
            self.start_worker()
            return

        self.done(QDialog.Rejected)

    def closeEvent(self, event) -> None:
        if self.is_finished:
            event.accept()
            return

        should_cancel = ask_yes_no(
            self,
            self.tr("install.cancel.title"),
            self.tr("install.cancel.body"),
            self.tr("common.yes"),
            self.tr("common.no"),
        )

        if not should_cancel:
            event.ignore()
            return

        if self.worker is not None:
            self.worker.terminate()
            self.worker.wait()

        event.accept()
