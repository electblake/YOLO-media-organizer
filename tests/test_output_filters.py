import subprocess
import sys
import textwrap
import time
import tkinter as tk
from threading import Event
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image
from ultralytics.engine.results import Results

from app import scanner
from app.config import Settings
from app.main import MainView


def test_checked_labels_and_move_confidence_do_not_repeat_inference(tmp_path, monkeypatch):
    source = tmp_path / "media"
    source.mkdir()
    Image.new("RGB", (16, 16), "red").save(source / "a.png")
    Image.new("RGB", (16, 16), "blue").save(source / "b.png")
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"test")
    names = {0: "label-A", 1: "label-B"}
    calls = []
    continue_scan = Event()

    def predict(source, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            assert continue_scan.wait(10)
        scores = [0.6, 0.4] if source.getpixel((0, 0))[0] else [0.2, 0.8]
        return [Results(np.array(source), "image", names, probs=torch.tensor(scores))]

    monkeypatch.setattr(scanner, "load_model", lambda _: SimpleNamespace(
        names=names, ckpt_path=str(weights), predict=predict,
    ))
    root = tk.Tk()
    root.geometry("1100x760")
    view = MainView(root, Settings(tmp_path / "settings", {}))
    view.pack(fill="both", expand=True)
    view.data_dir = tmp_path / "data"
    view.source.set(str(source))

    def finish():
        for _ in range(1000):
            root.update()
            if not view.busy:
                break
            time.sleep(0.01)
        view.future.result()
        assert not view.busy

    view.start_scan()
    for _ in range(500):
        root.update()
        if view.label_checks:
            break
        time.sleep(0.01)
    assert view.busy
    assert view.media_stats.get() == "2 files · 1 matched (50%) · 0 to move"
    assert view.label_checks["label-A"].instate(["!disabled"])
    view.label_checks["label-A"].invoke()
    assert view.label_vars["label-A"].get()
    assert len(view.move_plan) == 1
    assert view.media_stats.get() == "2 files · 1 matched (50%) · 1 to move"
    assert view.move_button.instate(["disabled"])
    continue_scan.set()
    finish()
    assert view.move_button.instate(["!disabled"])
    view.label_checks["label-A"].invoke()
    assert len(calls) == 2
    assert all(kwargs["conf"] == 0.25 for kwargs in calls)
    assert set(view.label_vars) == {"label-A", "label-B"}
    assert not any(variable.get() for variable in view.label_vars.values())
    assert view.move_plan == []
    assert view.media_stats.get() == "2 files · 2 matched (100%) · 0 to move"
    assert view.min_predictions.get() == 1
    assert view.max_predictions.get() == -1
    assert float(view.min_count.cget("from")) == 1
    assert view.min_count.instate(["readonly"])
    assert view.move_button.instate(["!disabled"])
    assert all(view.tree.set(row, "destination") == "" for row in view.tree.get_children())

    view.move_confidence.set(0.3)
    view.label_checks["label-B"].invoke()
    assert len(view.move_plan) == 2
    assert all(result.label == "label-B" for result in view.move_plan)
    assert view.move_plan[0].destination == source / "label-B" / "a.png"
    assert view.move_button.instate(["!disabled"])
    view.label_checks["label-A"].invoke()
    assert view.move_plan[0].label == "label-A"
    view.min_predictions.set(2)
    assert [result.source.name for result in view.move_plan] == ["a.png"]
    view.max_predictions.set(2)
    assert [result.source.name for result in view.move_plan] == ["a.png"]
    view.max_predictions.set(1)
    assert view.move_plan == []
    view.min_predictions.set(1)
    assert [result.source.name for result in view.move_plan] == ["b.png"]
    view.max_predictions.set(-1)
    assert len(view.move_plan) == 2
    view.label_checks["label-A"].invoke()
    assert view.move_plan[0].label == "label-B"
    view.move_confidence.set(0.7)
    assert [result.source.name for result in view.move_plan] == ["b.png"]
    assert view.media_stats.get() == "2 files · 1 matched (50%) · 1 to move"
    assert len(view.tree.get_children(str(source / "a.png"))) == 0
    assert len(view.results[0].predictions) == 2
    view.move_confidence.set(0.3)
    assert len(view.tree.get_children(str(source / "a.png"))) == 2
    assert len(calls) == 2

    view.scan_confidence.set(0.15)
    assert view.move_button.instate(["!disabled"])

    view.start_scan()
    assert view.media_stats.get() == "0 files · 0 matched (0%) · 0 to move"
    finish()
    assert len(calls) == 4
    assert all(kwargs["conf"] == 0.15 for kwargs in calls[2:])
    assert view.label_vars["label-B"].get()
    assert not view.label_vars["label-A"].get()
    view.move_confidence.set(0.7)
    view.move_button.invoke()
    finish()
    assert (source / "a.png").exists()
    assert not (source / "b.png").exists()
    assert (source / "label-B" / "b.png").exists()
    assert view.media_stats.get() == "2 files · 1 matched (50%) · 0 to move"
    view.move_confidence.set(0.3)
    assert [result.source.name for result in view.move_plan] == ["a.png"]
    assert view.media_stats.get() == "2 files · 2 matched (100%) · 1 to move"
    assert view.result_paths[str(source / "b.png")] == source / "label-B" / "b.png"
    assert len(calls) == 4
    view.close()


def test_scan_reports_file_failures_and_finishes(tmp_path):
    script = """
    import sys
    import time
    import tkinter as tk
    from pathlib import Path
    from types import SimpleNamespace
    import numpy as np
    import pytest
    import torch
    from PIL import Image
    from ultralytics.engine.results import Results
    from app import scanner
    from app.config import Settings
    from app.main import MainView
    tmp_path = Path(sys.argv[1])
    monkeypatch = pytest.MonkeyPatch()
    source = tmp_path / "media"
    source.mkdir()
    Image.new("RGB", (16, 16), "red").save(source / "a.png")
    (source / "b.png").write_bytes(b"invalid image")
    Image.new("RGB", (16, 16), "blue").save(source / "c.png")
    Image.new("RGB", (16, 16), "red").save(source / "d.png")
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"test")
    names = {0: "person"}

    def predict(source, **kwargs):
        if source.getpixel((0, 0))[2]:
            raise RuntimeError("inference failed for this file")
        return [Results(np.array(source), "image", names, probs=torch.tensor([1.0]))]

    monkeypatch.setattr(scanner, "load_model", lambda _: SimpleNamespace(
        names=names, ckpt_path=str(weights), predict=predict,
    ))
    root = tk.Tk()
    view = MainView(root, Settings(tmp_path / "settings", {}))
    view.pack(fill="both", expand=True)
    view.source.set(str(source))
    for attempt in range(2):
        view.start_scan()
        assert view.failed_files == 0
        assert view.scan_error.get() == ""
        for _ in range(1000):
            root.update()
            if not view.busy:
                break
            time.sleep(0.01)
        view.future.result()
        assert not view.busy
        assert [result.source.name for result in view.results] == ["a.png", "d.png"]
        assert all(result.cached == bool(attempt) for result in view.results)
        assert view.failed_files == 2
        assert view.progress["value"] == view.progress["maximum"] == 4
        assert "RuntimeError: inference failed for this file" in view.scan_error.get()
        assert view.status.get() == "Preview ready · 2 media · 2 failed"
    assert sorted(path.name for path in source.iterdir()) == ["a.png", "b.png", "c.png", "d.png"]
    view.close()
    """
    output = subprocess.check_output([sys.executable, "-c", textwrap.dedent(script), str(tmp_path)], text=True)
    assert "b.png: UnidentifiedImageError:" in output
    assert "c.png: RuntimeError: inference failed for this file" in output
