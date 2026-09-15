import csv
from dataclasses import replace
from threading import Event
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
import torch
from PIL import Image
from ultralytics.engine.results import Results

from app import scanner
from app.organizer import move_media, plan_moves
from app.scanner import MediaResult, ScanOptions


def test_standard_classification_and_detection_outputs():
    image = np.zeros((24, 24, 3), dtype=np.uint8)
    classification = Results(image, "test.png", {0: "cat", 1: "dog"}, probs=torch.tensor([0.2, 0.8]))
    detection = Results(image, "test.png", {0: "0-14", 1: "22+"}, boxes=torch.tensor([
        [0, 0, 10, 10, 0.9, 1], [2, 2, 20, 20, 0.7, 0], [12, 12, 23, 23, 0.8, 1],
    ]))
    assert scanner.result_labels(classification)[1]["label"] == "dog"
    predictions = scanner.result_labels(detection)
    assert [prediction["label"] for prediction in predictions] == ["22+", "0-14", "22+"]
    assert [prediction["confidence"] for prediction in predictions] == pytest.approx([0.9, 0.7, 0.8])
    assert all(set(prediction) == {"label", "confidence"} for prediction in predictions)
    empty = Results(image, "test.png", {0: "face"}, boxes=torch.empty((0, 6)))
    assert scanner.result_labels(empty) == []


def test_crop_detector_uses_default_predict_pipeline(tmp_path):
    calls = []

    class Classifier:
        def predict(self, source, **kwargs):
            calls.append((source.size, kwargs))
            return [Results(np.array(source), "crop", {0: "label"}, probs=torch.tensor([1.0]))]

    detector = SimpleNamespace(predict=lambda **kwargs: [SimpleNamespace(
        boxes=SimpleNamespace(xyxy=torch.tensor([[2, 3, 12, 18], [0, 0, 5, 5]]))
    )])
    predictions = scanner.predict_image(Classifier(), detector, Image.new("RGB", (30, 30)), ScanOptions(tmp_path))
    assert [size for size, _ in calls] == [(10, 15), (5, 5)]
    assert len(predictions) == 2
    assert calls[0][1] == {"verbose": False, "save": False, "conf": 0.25}


def test_video_snapshot_percentage_and_rgb(tmp_path):
    path = tmp_path / "clip.avi"
    video = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 32))
    for value in range(11):
        video.write(np.full((32, 32, 3), (value * 20, 0, 0), dtype=np.uint8))
    video.release()
    image, frame = scanner.media_image(path, 50)
    assert frame == 5
    assert image.mode == "RGB"
    assert abs(image.getpixel((10, 10))[2] - 100) < 5
    _, end = scanner.media_image(path, 100)
    assert end == 10


def test_discovery_excludes_output_and_preserves_unicode(tmp_path):
    source = tmp_path / "input"
    output = source / "sorted"
    output.mkdir(parents=True)
    (source / "nested").mkdir()
    for name in ["one.JPG", "clip.MP4", "ignore.txt", "nested/日本.png", "sorted/old.jpg"]:
        (source / name).touch()
    options = ScanOptions(source)
    assert {p.name for p in scanner.discover(options, {output})} == {"one.JPG", "clip.MP4", "日本.png"}
    assert {p.name for p in scanner.discover(replace(options, recursive=False, include_videos=False))} == {"one.JPG"}


def test_index_reuse_and_invalidation(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    image = source / "image.png"
    Image.new("RGB", (16, 16)).save(image)
    weights = tmp_path / "test.pt"
    weights.write_bytes(b"weights")
    monkeypatch.setattr(scanner, "load_model", lambda _: SimpleNamespace(ckpt_path=str(weights), names={0: "cat"}))
    calls = []

    def predict(*args):
        calls.append(True)
        return [{"label": "cat", "confidence": 0.8}]

    monkeypatch.setattr(scanner, "predict_image", predict)
    options = ScanOptions(source)
    index = tmp_path / "index.db"

    def run(settings=options):
        return scanner.scan(settings, index, Event(), lambda *_: None)[0]

    assert run().destination is None
    assert run().cached
    assert len(calls) == 1
    Image.new("RGB", (40, 40)).save(image)
    assert not run().cached
    weights.write_bytes(b"new weights")
    assert not run().cached
    assert not run(replace(options, frame_percentage=75)).cached
    assert not run(replace(options, scan_confidence=0.1)).cached
    assert len(calls) == 5


def test_moves_originals_and_journals_without_overwriting(tmp_path):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"original video bytes")
    destination = tmp_path / "sorted" / "cat" / source.name
    item = MediaResult(source, "cat", 0.9, [], destination, False, 5)
    journal = tmp_path / "moves.csv"
    assert move_media([item], journal, Event(), lambda *_: None) == 1
    assert not source.exists()
    assert destination.read_bytes() == b"original video bytes"
    with journal.open() as stream:
        assert next(iter(csv.DictReader(stream)))["label"] == "cat"
    source.write_bytes(b"another video")
    with pytest.raises(FileExistsError):
        move_media([item], tmp_path / "second.csv", Event(), lambda *_: None)
    assert source.read_bytes() == b"another video"
    assert destination.read_bytes() == b"original video bytes"


def test_loaded_model_labels_determine_folders_and_rescan_exclusions(tmp_path, monkeypatch):
    source = tmp_path / "media"
    nested = source / "nested"
    nested.mkdir(parents=True)
    image = nested / "sample.png"
    Image.new("RGB", (16, 16)).save(image)
    weights = tmp_path / "model.pt"
    weights.write_bytes(b"test weights")
    names = {0: "custom-class-A", 1: "custom-class-B"}
    model = SimpleNamespace(
        ckpt_path=str(weights), names=names,
        predict=lambda source, **kwargs: [Results(
            np.array(source), "sample.png", names, probs=torch.tensor([0.1, 0.9])
        )],
    )
    monkeypatch.setattr(scanner, "load_model", lambda _: model)
    options = ScanOptions(source)
    results = scanner.scan(options, tmp_path / "index.db", Event(), lambda *_: None)
    assert results[0].predictions[0]["label"] == "custom-class-B"
    assert results[0].destination is None
    planned = plan_moves(results, source, {names[1]}, 0.5)
    assert planned[0].destination == source / names[1] / "nested" / "sample.png"
    move_media(planned, tmp_path / "moves.csv", Event(), lambda *_: None)
    assert scanner.scan(options, tmp_path / "index.db", Event(), lambda *_: None) == []


def test_stop_and_unclassified_media_stay_in_place(tmp_path):
    source = tmp_path / "photo.png"
    source.touch()
    item = MediaResult(source, None, None, [], None, False, None)
    assert move_media([item], tmp_path / "moves.csv", Event(), lambda *_: None) == 0
    stop = Event()
    stop.set()
    assert move_media([replace(item, destination=tmp_path / "other.png")], tmp_path / "stopped.csv", stop, lambda *_: None) == 0
    assert source.exists()


@pytest.mark.parametrize("minimum, maximum, expected", [
    (1, -1, [1, 2, 3]), (1, 1, [1]), (1, 2, [1, 2]),
    (2, 2, [2]), (3, -1, [3]), (3, 2, []), (1, 0, []),
])
def test_move_prediction_count_bounds(tmp_path, minimum, maximum, expected):
    results = [MediaResult(
        tmp_path / f"{count}.png", None, None,
        [{"label": "checked", "confidence": 0.8}] * count + [
            {"label": "unchecked", "confidence": 0.99},
            {"label": "checked", "confidence": 0.2},
        ], None, False, None,
    ) for count in range(4)]
    planned = plan_moves(results, tmp_path, {"checked"}, 0.8, minimum, maximum)
    assert [int(result.source.stem) for result in planned] == expected


@pytest.mark.parametrize("label, expected", [("22+", "22+"), ("../cat", "%2E%2E%2Fcat"), ("CON", "%43ON"), ("cat ", "cat%20"), ("a:b", "a%3Ab")])
def test_label_folder_names(label, expected):
    assert scanner.label_folder(label) == expected
