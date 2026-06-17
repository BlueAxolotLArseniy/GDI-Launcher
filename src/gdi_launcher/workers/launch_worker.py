from __future__ import annotations

import subprocess

from PySide6.QtCore import QThread, Signal

from gdi_launcher.services.launch_service import LaunchService


class LaunchWorker(QThread):
    process_started = Signal(object)
    launch_finished = Signal()

    def __init__(
        self,
        instance_name: str,
        launch_service: LaunchService | None = None,
    ) -> None:
        super().__init__()
        self.instance_name = instance_name
        self.launch_service = launch_service or LaunchService()

    def run(self) -> None:
        self.launch_service.sync_and_run_instance(
            self.instance_name,
            self._emit_process_started,
        )
        self.launch_finished.emit()

    def _emit_process_started(self, process: subprocess.Popen) -> None:
        self.process_started.emit(process)

