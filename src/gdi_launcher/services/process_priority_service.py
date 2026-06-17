from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PriorityOption:
    key: str
    label_key: str
    windows_class: int


PRIORITY_OPTIONS: tuple[PriorityOption, ...] = (
    PriorityOption("idle", "priority.idle", 0x00000040),
    PriorityOption("below_normal", "priority.below_normal", 0x00004000),
    PriorityOption("normal", "priority.normal", 0x00000020),
    PriorityOption("above_normal", "priority.above_normal", 0x00008000),
    PriorityOption("high", "priority.high", 0x00000080),
    PriorityOption("realtime", "priority.realtime", 0x00000100),
)

PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def get_priority_option(priority_key: str) -> PriorityOption:
    for option in PRIORITY_OPTIONS:
        if option.key == priority_key:
            return option

    return get_priority_option("normal")


class ProcessPriorityService:
    def __init__(self) -> None:
        self.last_error: int | None = None

    def set_priority(self, process: subprocess.Popen, priority_key: str) -> bool:
        if sys.platform != "win32":
            return False

        option = get_priority_option(priority_key)
        process_handle, should_close = self._get_process_handle(process)
        if process_handle is None:
            return False

        try:
            result = self._kernel32().SetPriorityClass(
                ctypes.c_void_p(process_handle),
                ctypes.c_uint(option.windows_class),
            )
            self.last_error = None if result else ctypes.get_last_error()
            return bool(result)
        finally:
            if should_close:
                self._kernel32().CloseHandle(ctypes.c_void_p(process_handle))

    def ensure_priority(
        self,
        process: subprocess.Popen,
        priority_key: str,
        attempts: int = 6,
        delay_seconds: float = 0.25,
    ) -> bool:
        expected = get_priority_option(priority_key)

        for attempt in range(attempts):
            if process.poll() is not None:
                return False

            self.set_priority(process, expected.key)
            current = self.get_priority(process)
            if current and current.key == expected.key:
                return True

            if attempt < attempts - 1:
                time.sleep(delay_seconds)

        return False

    def get_creation_flags(self, priority_key: str | None) -> int:
        if sys.platform != "win32" or not priority_key:
            return 0

        return get_priority_option(priority_key).windows_class

    def get_priority(self, process: subprocess.Popen) -> PriorityOption | None:
        if sys.platform != "win32":
            return None

        process_handle, should_close = self._get_process_handle(process)
        if process_handle is None:
            return None

        try:
            priority_class = self._kernel32().GetPriorityClass(ctypes.c_void_p(process_handle))
            if priority_class == 0:
                self.last_error = ctypes.get_last_error()
                return None

            for option in PRIORITY_OPTIONS:
                if option.windows_class == int(priority_class):
                    return option

            return None
        finally:
            if should_close:
                self._kernel32().CloseHandle(ctypes.c_void_p(process_handle))

    def _get_process_handle(self, process: subprocess.Popen) -> tuple[int | None, bool]:
        access = (
            PROCESS_SET_INFORMATION
            | PROCESS_QUERY_INFORMATION
            | PROCESS_QUERY_LIMITED_INFORMATION
        )
        opened_handle = self._kernel32().OpenProcess(
            ctypes.c_uint(access),
            ctypes.c_int(False),
            ctypes.c_uint(process.pid),
        )
        if opened_handle:
            return int(opened_handle), True

        process_handle = getattr(process, "_handle", None)
        if process_handle is None:
            self.last_error = ctypes.get_last_error()
            return None, False

        return int(process_handle), False

    def _kernel32(self):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        kernel32.SetPriorityClass.restype = ctypes.c_int
        kernel32.GetPriorityClass.argtypes = [ctypes.c_void_p]
        kernel32.GetPriorityClass.restype = ctypes.c_uint
        kernel32.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        return kernel32
