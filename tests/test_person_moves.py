import subprocess
import sys


def test_single_class_move_changes_files_and_disables_empty_plan(tmp_path):
    script = """
import sys
import tkinter as tk
from concurrent.futures import Future
from pathlib import Path
from app.config import Settings
from app.main import MainView
from app.scanner import MediaResult, ScanOptions
root = tk.Tk()
root.withdraw()
directory = Path(sys.argv[1])
source = directory / "text"
source.mkdir()
original = source / "person.jpg"
original.write_bytes(b"original file contents")
view = MainView(root, Settings(directory / "settings", {}))
view.options = ScanOptions(source)
view.results = [MediaResult(original, None, None, [{"label": "person", "confidence": .9}], None, False, None)]
view.refresh_results()
assert view.move_button.instate(["disabled"])
view.label_checks["person"].invoke()
assert view.move_button.instate(["!disabled"])
assert view.move_plan[0].destination == source / "person" / original.name
view.move_button.invoke()
assert view.move_button.instate(["disabled"])
view.refresh_results()
assert view.move_button.instate(["disabled"])
view.future.result(timeout=10)
view.poll()
assert not original.exists()
assert (source / "person" / original.name).read_bytes() == b"original file contents"
assert view.status.get() == "1 files moved"
assert view.move_button.instate(["disabled"])
view.future = Future()
view.future.set_result(0)
view.poll()
assert view.status.get() == "No files moved."
view.close()
"""
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
