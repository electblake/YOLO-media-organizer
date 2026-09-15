"""Move reviewed originals, retaining their names and recording completed moves."""

import csv
import os
import shutil
from dataclasses import replace
from pathlib import Path
from threading import Event

from app.scanner import MediaResult, label_folder


def plan_moves(results: list[MediaResult], source: Path, labels: set[str], move_confidence: float,
               min_predictions: int = 1, max_predictions: int = -1):
    planned = []
    for result in results:
        matches = [prediction for prediction in result.predictions
                   if prediction["label"] in labels and prediction["confidence"] >= move_confidence]
        if matches and len(matches) >= min_predictions and (max_predictions == -1 or len(matches) <= max_predictions):
            match = max(matches, key=lambda prediction: prediction["confidence"])
            planned.append(replace(
                result, label=match["label"], confidence=match["confidence"],
                destination=source / label_folder(match["label"]) / result.source.relative_to(source),
            ))
    return planned


def move_media(results: list[MediaResult], journal: Path, stop: Event, emit):
    journal.parent.mkdir(parents=True, exist_ok=True)
    moved = 0
    with journal.open("x", newline="", encoding="utf-8") as log:
        writer = csv.writer(log)
        writer.writerow(["source", "destination", "label", "confidence"])
        log.flush()
        for result in results:
            if stop.is_set():
                break
            if result.destination is None:
                continue
            result.destination.parent.mkdir(parents=True, exist_ok=True)
            with result.source.open("rb") as source, result.destination.open("xb") as destination:
                shutil.copyfileobj(source, destination)
                destination.flush()
                os.fsync(destination.fileno())
            shutil.copystat(result.source, result.destination)
            result.source.unlink()
            writer.writerow([result.source, result.destination, result.label, result.confidence])
            log.flush()
            os.fsync(log.fileno())
            moved += 1
            emit("moved", result)
    return moved
