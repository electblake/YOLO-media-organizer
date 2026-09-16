import subprocess
import sys


def test_load_filter_sort_and_replace_classes(tmp_path):
    script = """
import sys
import threading
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from app.config import Settings
from app.main import MainView
from app.scanner import MODEL_PRESETS
root = tk.Tk()
root.geometry("1100x760")
view = MainView(root, Settings(Path(sys.argv[1]), {"active_tab": "Models"}))
view.pack(fill="both", expand=True)
root.update()
release = threading.Event()
started = threading.Event()
references = []
def loader(reference, emit):
    assert threading.current_thread() is not threading.main_thread()
    references.append(reference)
    emit("status", "Checking Hugging Face cache / requesting model")
    started.set()
    release.wait(10)
    return SimpleNamespace(names={10: "Zebra", 2: "cat", 1: "Catfish", 3: "cat"})
with patch("app.main.load_model", loader):
    view.load_classes_button.invoke()
    assert view.load_classes_button.instate(["disabled"])
    assert view.scan_button.instate(["disabled"])
    assert view.stop_button.instate(["disabled"])
    assert view.status.get().startswith("Preparing to load classes:")
    assert str(view.progress["mode"]) == "indeterminate"
    root.update()
    assert started.wait(10)
    view.poll_classes()
    assert view.status.get() == "Checking Hugging Face cache / requesting model"
    view.emit("download_progress", ("model.pt", 1048576, 4194304))
    view.poll_classes()
    assert str(view.progress["mode"]) == "determinate"
    assert view.progress["value"] == 1048576
    assert view.progress["maximum"] == 4194304
    assert view.status.get() == "model.pt: 1.0 / 4.0 MiB (25%)"
    view.emit("status", "Reading model classes")
    view.poll_classes()
    assert view.status.get() == "Reading model classes"
    assert str(view.progress["mode"]) == "indeterminate"
    release.set()
    view.classes_future.result(timeout=10)
    view.poll_classes()
assert references == [MODEL_PRESETS[view.model.get()]]
assert view.load_classes_button.instate(["!disabled"])
assert view.progress["value"] == 100
assert view.status.get().startswith("Loaded 4 classes:")
assert view.class_tree.get_children() == ("10", "2", "1", "3")
def click(column):
    root.tk.call(view.class_tree.heading(column, "command"))
click("id")
assert view.class_tree.get_children() == ("1", "2", "3", "10")
click("id")
assert view.class_tree.get_children() == ("10", "3", "2", "1")
click("id")
assert view.class_tree.get_children() == ("10", "2", "1", "3")
click("label")
click("id")
assert view.class_tree.get_children() == ("2", "3", "1", "10")
assert view.class_tree.heading("id", "text").endswith(chr(9650) + "2")
view.class_filter.set("CAT")
assert view.class_tree.get_children() == ("2", "3", "1")
view.class_filter.set("no match")
assert view.class_tree.get_children() == ()
view.class_filter.set("")
assert len(view.class_tree.get_children()) == 4
view.model.set("custom.pt")
assert view.class_tree.get_children() == ()
with patch("app.main.load_model", return_value=SimpleNamespace(names={5: "person"})) as load:
    view.load_classes_button.invoke()
    view.classes_future.result(timeout=10)
    view.poll_classes()
    load.assert_called_once_with("custom.pt", view.emit)
assert view.class_tree.get_children() == ("5",)
assert view.class_tree.set("5", "label") == "person"
view.close()
"""
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
