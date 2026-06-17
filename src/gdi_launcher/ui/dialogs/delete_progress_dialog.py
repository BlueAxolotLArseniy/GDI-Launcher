from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout

from gdi_launcher.services.translation_service import TranslationService
from gdi_launcher.workers.delete_worker import DeleteWorker


class DeleteProgressDialog(QDialog):
    def __init__(self, target_dir: str, instance_name: str, parent=None) -> None:
        super().__init__(parent)

        self.target_dir = target_dir
        self.instance_name = instance_name
        self.translation_service = TranslationService()

        self.setWindowTitle(self.tr("delete.window_title"))
        self.setFixedSize(400, 110)

        self._build_ui()
        self.start_worker()

    def tr(self, key: str, **kwargs: object) -> str:
        return self.translation_service.t(key, **kwargs)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.lbl_status = QLabel(self.tr("delete.preparing", name=self.instance_name))
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

    def start_worker(self) -> None:
        self.worker = DeleteWorker(self.target_dir, self.instance_name)
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.deletion_finished.connect(self.on_deletion_finished)
        self.worker.start()

    def on_deletion_finished(self, success: bool, message: str) -> None:
        if success:
            self.accept()
            return

        self.reject()
