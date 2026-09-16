import subprocess
import sys


def test_scan_controls_forward_options_and_reset(tmp_path):
    script = """
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import patch
from app.config import Settings
from app.main import MainView
root = tk.Tk()
root.geometry("1440x960")
view = MainView(root, Settings(Path(sys.argv[1]), {}))
view.pack(fill="both", expand=True)
root.update()
for values, expected in [
    ({}, (1, None, False, None, 1)),
    ({"batch": 8, "precision": "FP16", "compile": True, "imgsz": "320", "vid_stride": 3}, (8, 16, True, 320, 3)),
    ({"precision": "FP32"}, (8, 32, True, 320, 3)),
]:
    for name, value in values.items():
        getattr(view, name).set(value)
    with patch.object(view.executor, "submit") as submit, patch.object(view, "after"):
        view.start_scan()
    options = submit.call_args.args[1]
    assert (options.batch, options.quantize, options.compile, options.imgsz, options.vid_stride) == expected
    view.set_busy(False)
view.reset_config_button.invoke()
assert (view.batch.get(), view.precision.get(), view.compile.get(), view.imgsz.get(), view.vid_stride.get()) == (
    1, "Default", False, "Default", 1,
)
root.update()
for variable in (view.batch, view.precision, view.compile, view.imgsz, view.vid_stride):
    widget = next(w for w in view.inputs if str(w.cget("variable" if w.winfo_class() == "TCheckbutton" else "textvariable")) == str(variable))
    assert widget.winfo_ismapped()
    assert widget.winfo_rooty() < view.label_canvas.master.winfo_rooty()
view.close()
"""
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
