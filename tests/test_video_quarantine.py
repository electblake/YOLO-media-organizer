import subprocess
import sys
from threading import Event
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
import torch
from PIL import Image
from ultralytics.data.loaders import LoadImagesAndVideos
from ultralytics.engine.results import Results

from app import scanner
from app.scanner import ScanOptions


@pytest.mark.parametrize("good_media", [False, True])
@pytest.mark.parametrize("stream", [False, True])
def test_quarantine_restarts_native_folder_loader(tmp_path, monkeypatch, good_media, stream):
    source = tmp_path / "media"
    source.mkdir()
    for name in ("a.mp4", "b.mp4"):
        (source / name).write_bytes(b"broken video")
    if good_media:
        Image.new("RGB", (32, 32)).save(source / "photo.png")
        video = cv2.VideoWriter(str(source / "c.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 32))
        for _ in range(4):
            video.write(np.zeros((32, 32, 3), dtype=np.uint8))
        video.release()
    weights = tmp_path / "model.pt"
    weights.touch()
    calls = []

    def predict(source, **kwargs):
        calls.append(source)

        def results():
            for paths, images, _ in LoadImagesAndVideos(source, vid_stride=kwargs["vid_stride"]):
                for path, image in zip(paths, images):
                    yield Results(image, path, {0: "cat"}, probs=torch.tensor([1.0]))

        return results() if kwargs["stream"] else list(results())

    monkeypatch.setattr(scanner, "load_model", lambda _: SimpleNamespace(ckpt_path=str(weights), predict=predict))
    events = []
    results = scanner.scan(
        ScanOptions(source, quarantine_video_failures=True, quarantine_folder="bad videos", vid_stride=2, stream=stream),
        tmp_path / "index.db", tmp_path / "scan.log", Event(), lambda *event: events.append(event),
    )
    assert len(calls) == (3 if good_media else 2)
    assert all(call == str(source) for call in calls)
    for name in ("a.mp4", "b.mp4"):
        assert not (source / name).exists()
        assert (source / "bad videos" / name).read_bytes() == b"broken video"
    assert {result.source.name for result in results} == ({"photo.png", "c.avi"} if good_media else set())
    assert not [event for event in events if event[0] == "item"]
    assert [payload for kind, payload in events if kind == "total"] == ([4, 3, 2] if good_media else [2, 1, 0])
    log = (tmp_path / "scan.log").read_text(encoding="utf-8")
    assert "FileNotFoundError: Failed to open video" in log
    assert log.count("Quarantined ") == 2


@pytest.mark.parametrize("enabled, message, collision", [
    (False, "Failed to open video ", False),
    (True, "Missing dependency ", False),
    (True, "Failed to open video ", True),
])
def test_quarantine_leaves_original_on_disabled_unrelated_error_or_collision(tmp_path, monkeypatch, enabled, message, collision):
    source = tmp_path / "media"
    source.mkdir()
    video = source / "bad.mp4"
    video.write_bytes(b"original")
    weights = tmp_path / "model.pt"
    weights.touch()
    destination = source / "quarantine" / video.name
    if collision:
        destination.parent.mkdir()
        destination.write_bytes(b"existing")

    def predict(**kwargs):
        raise FileNotFoundError(message + str(video))
        yield

    monkeypatch.setattr(scanner, "load_model", lambda _: SimpleNamespace(ckpt_path=str(weights), predict=predict))
    with pytest.raises(FileExistsError if collision else FileNotFoundError):
        scanner.scan(
            ScanOptions(source, quarantine_video_failures=enabled),
            tmp_path / "index.db", tmp_path / "scan.log", Event(), lambda *_: None,
        )
    assert video.read_bytes() == b"original"
    if collision:
        assert destination.read_bytes() == b"existing"
    else:
        assert not destination.exists()


def test_quarantine_controls_options_and_persistence(tmp_path):
    script = '''
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import patch
from app.config import Settings
from app.main import MainView
root = tk.Tk()
root.geometry("1440x960")
directory = Path(sys.argv[1])
view = MainView(root, Settings(directory, {}))
view.pack(fill="both", expand=True)
root.update()
assert not view.quarantine_video_failures.get()
assert view.quarantine_folder.get() == "quarantine"
assert view.quarantine_entry.instate(["disabled"])
view.quarantine_toggle.invoke()
assert not view.quarantine_entry.instate(["disabled"])
assert view.quarantine_entry.winfo_rootx() > view.quarantine_toggle.winfo_rootx()
assert view.quarantine_entry.winfo_rooty() == view.quarantine_toggle.winfo_rooty()
view.quarantine_folder.set("bad videos")
view.source.set(str(directory))
with patch.object(view.executor, "submit") as submit, patch.object(view, "after"):
    view.start_scan()
assert submit.call_args.args[1].quarantine_video_failures
assert submit.call_args.args[1].quarantine_folder == "bad videos"
assert view.quarantine_entry.instate(["disabled"])
view.set_busy(False)
assert not view.quarantine_entry.instate(["disabled"])
view.save_config()
restored = Settings(directory, {})
assert restored.values.quarantine_video_failures
assert restored.values.quarantine_folder == "bad videos"
view.reset_defaults()
assert not view.quarantine_video_failures.get()
assert view.quarantine_folder.get() == "quarantine"
assert view.quarantine_entry.instate(["disabled"])
view.set_busy(True)
view.set_busy(False)
assert view.quarantine_entry.instate(["disabled"])
view.close()
'''
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
