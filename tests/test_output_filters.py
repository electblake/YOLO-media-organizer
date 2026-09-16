import subprocess
import sys
import textwrap
import time
import tkinter as tk
from pathlib import Path
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
        scanner.LOGGER.info("native scan output")
        if len(calls) == 1:
            assert continue_scan.wait(10)
        results = []
        for path in sorted(Path(source).iterdir()):
            if path.suffix != ".png":
                continue
            image = Image.open(path)
            scores = [0.6, 0.4] if image.getpixel((0, 0))[0] else [0.2, 0.8]
            results.append(Results(np.array(image), str(path), names, probs=torch.tensor(scores)))
        return results

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
        if calls and view.status.get() == "Scanning (0/2)":
            break
        time.sleep(0.01)
    assert view.busy
    assert view.media_stats.get() == "2 files · 0 labels · 0 to move (0%)"
    assert str(view.progress["mode"]) == "determinate"
    assert view.progress["maximum"] == 2
    assert view.progress["value"] == 0
    assert view.status.get() == "Scanning (0/2)"
    assert view.label_checks == {}
    continue_scan.set()
    finish()
    assert "native scan output" in view.log_console.get("1.0", "end")
    assert view.inference_device.get() == "Device: cpu"
    assert str(view.log_path.parent) in view.console_frame.cget("text")
    assert view.move_button.instate(["!disabled"])
    assert len(calls) == 1
    assert calls[0]["conf"] == 0.25
    assert set(view.label_vars) == {"label-A", "label-B"}
    assert view.label_checks["label-A"].instate(["!disabled"])
    view.label_checks["label-A"].invoke()
    assert view.label_vars["label-A"].get()
    assert len(view.move_plan) == 1
    assert view.media_stats.get() == "2 files · 2 labels · 1 to move (50%)"
    assert view.move_button.instate(["!disabled"])
    view.label_checks["label-A"].invoke()
    assert not any(variable.get() for variable in view.label_vars.values())
    assert view.move_plan == []
    assert view.media_stats.get() == "2 files · 2 labels · 0 to move (0%)"
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
    assert view.media_stats.get() == "2 files · 2 labels · 1 to move (50%)"
    assert len(view.tree.get_children(str(source / "a.png"))) == 0
    assert len(view.results[0].predictions) == 2
    view.move_confidence.set(0.3)
    assert len(view.tree.get_children(str(source / "a.png"))) == 2
    assert len(calls) == 1

    view.scan_confidence.set(0.15)
    assert view.move_button.instate(["!disabled"])

    view.start_scan()
    assert view.media_stats.get() == "0 files · 0 labels · 0 to move (0%)"
    finish()
    assert len(calls) == 2
    assert calls[1]["conf"] == 0.15
    assert view.label_vars["label-B"].get()
    assert not view.label_vars["label-A"].get()
    view.move_confidence.set(0.7)
    view.move_button.invoke()
    finish()
    assert (source / "a.png").exists()
    assert not (source / "b.png").exists()
    assert (source / "label-B" / "b.png").exists()
    assert view.media_stats.get() == "2 files · 2 labels · 0 to move (0%)"
    view.move_confidence.set(0.3)
    assert [result.source.name for result in view.move_plan] == ["a.png"]
    assert view.media_stats.get() == "2 files · 2 labels · 1 to move (50%)"
    assert view.result_paths[str(source / "b.png")] == source / "label-B" / "b.png"
    assert len(calls) == 2
    view.close()


def test_directory_scan_displays_only_results_returned_by_ultralytics(tmp_path):
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
        return [Results(
            np.array(Image.open(path)), str(path), names, probs=torch.tensor([1.0])
        ) for path in sorted(Path(source).iterdir()) if path.name in {"a.png", "d.png"}]

    monkeypatch.setattr(scanner, "load_model", lambda _: SimpleNamespace(
        names=names, ckpt_path=str(weights), predict=predict,
    ))
    root = tk.Tk()
    view = MainView(root, Settings(tmp_path / "settings", {}))
    view.pack(fill="both", expand=True)
    view.source.set(str(source))
    for attempt in range(2):
        view.start_scan()
        for _ in range(1000):
            root.update()
            if not view.busy:
                break
            time.sleep(0.01)
        view.future.result()
        assert not view.busy
        assert [result.source.name for result in view.results] == ["a.png", "d.png"]
        assert all(not result.cached for result in view.results)
        assert view.progress["value"] == view.progress["maximum"] == 100
        assert view.status.get() == "Preview ready · 2 files"
        assert view.media_stats.get() == "4 files · 1 labels · 0 to move (0%)"
    assert sorted(path.name for path in source.iterdir()) == ["a.png", "b.png", "c.png", "d.png"]
    view.close()
    """
    subprocess.run([sys.executable, "-c", textwrap.dedent(script), str(tmp_path)], check=True)
