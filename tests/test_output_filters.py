import time
import tkinter as tk
from threading import Event
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image
from ultralytics.engine.results import Results

from app import scanner
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
    view = MainView(root)
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
    assert view.label_checks["label-A"].instate(["!disabled"])
    view.label_checks["label-A"].invoke()
    assert view.label_vars["label-A"].get()
    assert len(view.move_plan) == 1
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
    assert len(view.tree.get_children(str(source / "a.png"))) == 0
    assert len(view.results[0].predictions) == 2
    view.move_confidence.set(0.3)
    assert len(view.tree.get_children(str(source / "a.png"))) == 2
    assert len(calls) == 2

    view.scan_confidence.set(0.15)
    assert view.move_button.instate(["!disabled"])

    view.start_scan()
    finish()
    assert len(calls) == 4
    assert all(kwargs["conf"] == 0.15 for kwargs in calls[2:])
    assert not any(variable.get() for variable in view.label_vars.values())
    view.label_checks["label-B"].invoke()
    view.move_confidence.set(0.7)
    view.move_button.invoke()
    finish()
    assert (source / "a.png").exists()
    assert not (source / "b.png").exists()
    assert (source / "label-B" / "b.png").exists()
    view.move_confidence.set(0.3)
    assert [result.source.name for result in view.move_plan] == ["a.png"]
    assert view.result_paths[str(source / "b.png")] == source / "label-B" / "b.png"
    assert len(calls) == 4
    view.close()
