import subprocess
import sys


def test_scan_failure_is_visible_and_logged(tmp_path):
    script = '''
import sys
import tkinter as tk
from concurrent.futures import Future
from pathlib import Path
import pytest
from app.config import Settings
from app.main import MainView

root = tk.Tk()
view = MainView(root, Settings(Path(sys.argv[1]), {}))
view.pack(fill="both", expand=True)
view.operation = "scan"
view.log_path = Path(sys.argv[1]) / "scan.log"
view.log_path.write_text("frame 30/76\\n", encoding="utf-8")
view.set_busy(True)
view.progress.configure(mode="indeterminate")
view.progress.start()
view.scan_speed.set("1 item/s")
view.future = Future()
error = FileNotFoundError("Failed to open video broken.mp4")
view.future.set_exception(error)
with pytest.raises(FileNotFoundError) as raised:
    view.poll()
assert raised.value is error
root.update_idletasks()
text = view.log_console.get("1.0", "end-1c")
assert text == view.log_path.read_text(encoding="utf-8")
assert "frame 30/76" in text
assert "FileNotFoundError: Failed to open video broken.mp4" in text
assert view.status.get() == "Scan failed: Failed to open video broken.mp4"
assert view.scan_speed.get() == ""
assert not view.busy
assert not view.scan_button.instate(["disabled"])
assert view.stop_button.instate(["disabled"])
assert view.log_console.cget("state") == "disabled"
view.close()
'''
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
