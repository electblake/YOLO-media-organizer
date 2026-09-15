"""Verify the frozen window opens without the development environment."""

import ctypes
import os
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab

executable = Path(sys.argv[1]).resolve()
screenshot = Path(sys.argv[2]).resolve()
user32 = ctypes.windll.user32
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
environment = {key: value for key, value in os.environ.items()
               if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "TCL_LIBRARY", "TK_LIBRARY"}}
environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
windows = []


@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def find_window(handle, _):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(handle, title, len(title))
    if pid.value == process.pid and title.value == "YOLO Media Sorter":
        windows.append(handle)
    return True


with tempfile.TemporaryDirectory() as working_directory:
    process = subprocess.Popen([str(executable)], cwd=working_directory, env=environment)
    for _ in range(90):
        user32.EnumWindows(find_window, 0)
        if windows or process.poll() is not None:
            break
        time.sleep(0.5)
    assert windows, "Frozen application did not open its main window"
    time.sleep(1)
    ImageGrab.grab(window=windows[0]).save(screenshot)
    user32.PostMessageW(windows[0], 0x0010, 0, 0)
    assert process.wait(timeout=15) == 0
print(f"Verified {executable.name}: main window opened and closed successfully")
