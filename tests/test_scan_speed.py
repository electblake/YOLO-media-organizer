import subprocess
import sys


def test_scan_speed_and_remaining_time(tmp_path):
    script = '''
import sys
import tkinter as tk
from concurrent.futures import Future
from pathlib import Path
from app.config import Settings
from app.main import MainView
tmp_path = Path(sys.argv[1])
root = tk.Tk()
root.geometry("1100x760")
view = MainView(root, Settings(tmp_path / "settings", {}))
view.pack(fill="both", expand=True)
view.operation = "scan"
view.future = Future()
view.emit("scan_progress", (100, 10000, "photo.jpeg", 2.5))
view.poll()
root.update_idletasks()
assert view.status.get() == "Scanning (100/10000) photo.jpeg"
assert view.scan_speed.get() == "2.50 item/s · ~1h 06m 00s"
footer = view.progress.master
status_label = footer.grid_slaves(row=0, column=0)[0]
speed_label = footer.grid_slaves(row=0, column=1)[0]
assert speed_label.winfo_x() > status_label.winfo_x() + status_label.winfo_width()
assert speed_label.winfo_y() == status_label.winfo_y()
view.emit("scan_progress", (101, 10000, "next.jpeg", 5.0))
view.poll()
assert view.scan_speed.get() == "5.00 item/s · ~0h 33m 00s"
view.future.set_result([])
view.poll()
assert view.scan_speed.get() == ""
view.close()
'''
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
