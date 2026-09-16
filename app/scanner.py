"""Media discovery, standard YOLO inference, and a persistent metadata index."""

import hashlib
import json
import logging
import shutil
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from threading import Event
from urllib.parse import quote, unquote, urlsplit
from urllib.request import urlretrieve
from zipfile import ZipFile

import cv2
import torch
import ultralytics
from huggingface_hub import hf_hub_download
from PIL import Image, ImageOps
from tqdm import tqdm
from ultralytics import YOLO
from ultralytics.data.utils import IMG_FORMATS, VID_FORMATS
from ultralytics.utils import LOGGER
from ultralytics.utils.checks import check_file

from app.config import CONFIG_DIR, HF_CACHE_DIR, MODELS_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".wmv", ".mpeg", ".mpg", ".mov", ".m4v", ".mkv", ".webm"}
# TODO: convert MODEL_PRESETS to pydantic models saved in one models.json app config,
# with the current values committed as the default JSON.
MODEL_PRESETS = {
    "rpi5/person-detection/yolov8nbest": "ul://rpi5/person-detection/yolov8nbest",
    "NguyenToanLe/Age-Gender-Detection-YOLO / age": "https://media.githubusercontent.com/media/NguyenToanLe/Age-Gender-Detection-YOLO/main/models/age.pt",
    "NguyenToanLe/Age-Gender-Detection-YOLO / gender": "https://media.githubusercontent.com/media/NguyenToanLe/Age-Gender-Detection-YOLO/main/models/gender.pt",
    "DhanushSGowda/yolov8n-gender-classification": "hf://DhanushSGowda/yolov8n-gender-classification/best_Gender_classification.pt",
    "AdamCodd/yolo11n-face-age": "hf://AdamCodd/yolo11n-face-age/best.pt",
    "leeyunjai/yolo11-ko-face-emotion-cls": "hf://leeyunjai/yolo11-ko-face-emotion-cls/yolo11x-face-emotion.pt",
    "MnLgt/yolo-human-parse": "hf://MnLgt/yolo-human-parse/yolo-human-parse-epoch-125.pt",
    "yolo26n-cls": "yolo26n-cls.pt",
    "yolo11n-cls": "yolo11n-cls.pt",
    "yolov8n-cls": "yolov8n-cls.pt",
    "yolov8n-oiv7": "yolov8n-oiv7.pt",
    "yolov8s-oiv7": "hf://shirabendor/YOLOV8-oiv7/yolov8s-oiv7.pt",
    "yolov8m-oiv7": "hf://shirabendor/YOLOV8-oiv7/yolov8m-oiv7.pt",
    "yolov8l-oiv7": "yolov8l-oiv7.pt",
    "yolov8x-oiv7": "yolov8x-oiv7.pt",
    "dgyawa/yolo12n-cls-imagenet1k": "hf://dgyawa/yolo12n-cls-imagenet1k/yolo12n-cls.pt",
    "Anzhcs Breast size det cls v8 640 y11m": "hf://Anzhc/Anzhcs_YOLOs/Anzhcs Breast size det cls v8 640 y11m.pt",
    "booru_yolo / yolov11m_aa22": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov11m_aa22.pt",
    "booru_yolo / yolov11m_mm07": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov11m_mm07.pt",
    "booru_yolo / yolov11m_pp15": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov11m_pp15.pt",
    "booru_yolo / yolov8m_as02": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8m_as02.zip",
    "booru_yolo / yolov8m_as03": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8m_as03.zip",
    "booru_yolo / yolov8m_pp14": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8m_pp14.zip",
    "booru_yolo / yolov8n_as01": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8n_as01.pt",
    "booru_yolo / yolov8s_aa06": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8s_aa06.pt",
    "booru_yolo / yolov8s_aa09": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8s_aa09.pt",
    "booru_yolo / yolov8s_aa10": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8s_aa10.pt",
    "booru_yolo / yolov8s_aa11": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8s_aa11.pt",
    "booru_yolo / yolov8s_pp09": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8s_pp09.pt",
    "booru_yolo / yolov8s_pp12": "https://raw.githubusercontent.com/aperveyev/booru_yolo/main/models/yolov8s_pp12.pt",
}


@dataclass(frozen=True)
class ScanOptions:
    source: Path
    model: str = MODEL_PRESETS["DhanushSGowda/yolov8n-gender-classification"]
    crop_model: str = ""
    scan_confidence: float = 0.25
    frame_percentage: float = 50
    recursive: bool = True
    include_videos: bool = True
    device: str = ""


@dataclass(frozen=True)
class MediaResult:
    source: Path
    label: str | None
    confidence: float | None
    predictions: list[dict]
    destination: Path | None
    cached: bool
    frame_number: int | None


def load_model(reference: str, emit=None):
    if emit is not None:
        emit("status", f"Resolving model: {reference}")
    ultralytics.settings.update(
        weights_dir=str(MODELS_DIR / "ultralytics"),
        runs_dir=str(CONFIG_DIR / "runs"),
        datasets_dir=str(CONFIG_DIR / "datasets"),
    )
    if reference.startswith(("ul://", "https://platform.ultralytics.com/")):
        if emit is not None:
            emit("status", "Checking cache / downloading Ultralytics model")
        if reference.startswith("https://"):
            reference = "ul://" + urlsplit(reference).path.strip("/")
        reference = check_file(reference, download_dir=MODELS_DIR / "platform")
    elif reference.startswith("hf://"):
        owner, repo, filename = reference[5:].split("/", 2)
        download_options = {}
        if emit is not None:
            emit("status", f"Checking Hugging Face cache / requesting {owner}/{repo}/{filename}")

            class DownloadProgress(tqdm):
                def __init__(self, *args, **kwargs):
                    kwargs["file"] = StringIO()
                    super().__init__(*args, **kwargs)

                def display(self, msg=None, pos=None):
                    emit("download_progress", (self.desc, self.n, self.total))

            download_options["tqdm_class"] = DownloadProgress
        reference = hf_hub_download(repo_id=f"{owner}/{repo}", filename=filename, cache_dir=HF_CACHE_DIR, **download_options)
    elif reference.startswith(("https://", "http://")):
        target = MODELS_DIR / "urls" / hashlib.sha256(reference.encode()).hexdigest() / Path(unquote(urlsplit(reference).path)).name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            if emit is not None:
                emit("status", f"Downloading {target.name}")
            reporthook = (lambda blocks, size, total: emit("download_progress", (target.name, blocks * size, total))) if emit is not None else None
            urlretrieve(reference, target, reporthook=reporthook)
        if target.suffix == ".zip":
            if emit is not None:
                emit("status", f"Extracting {target.name}")
            checkpoint = target.with_suffix(".pt")
            if not checkpoint.exists():
                with ZipFile(target) as archive:
                    archive.extract(checkpoint.name, target.parent)
            target = checkpoint
        reference = str(target)
    elif Path(reference).name == reference and not Path(reference).exists():
        target = MODELS_DIR / "ultralytics" / reference
        target.parent.mkdir(parents=True, exist_ok=True)
        reference = str(target)
    else:
        source = Path(reference).resolve()
        if not source.is_relative_to(CONFIG_DIR):
            if emit is not None:
                emit("status", f"Copying local model: {source.name}")
            target = MODELS_DIR / "local" / hashlib.sha256(str(source).encode()).hexdigest() / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)
            reference = str(target)
    if emit is not None:
        emit("status", "Loading YOLO weights (downloading if not cached)")
    model = YOLO(reference)
    if emit is not None:
        emit("status", "Reading model classes")
    return model


def discover(options: ScanOptions, label_folders=()):
    extensions = IMAGE_EXTENSIONS | (VIDEO_EXTENSIONS if options.include_videos else set())

    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.is_symlink():
                continue
            if path.is_dir():
                if options.recursive and path.name != ".yolo-organizer" and path not in label_folders:
                    yield from visit(path)
            elif path.suffix.lower() in extensions:
                yield path

    yield from visit(options.source)


def media_image(path: Path, frame_percentage: float):
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        video = cv2.VideoCapture(str(path), cv2.CAP_FFMPEG)
        frame_number = round((int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1) * frame_percentage / 100)
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        _, frame = video.read()
        video.release()
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), frame_number
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB"), None


def result_labels(result):
    if result.probs is not None:
        return [
            {"label": result.names[index], "confidence": float(score)}
            for index, score in enumerate(result.probs.data.tolist())
        ]
    boxes = result.obb if result.obb is not None else result.boxes
    return [
        {"label": result.names[int(index)], "confidence": float(score)}
        for index, score in zip(boxes.cls.tolist(), boxes.conf.tolist())
    ]


def predict_image(model, crop_model, image, options: ScanOptions):
    kwargs = {"verbose": False, "save": False, "conf": options.scan_confidence}
    if options.device:
        kwargs["device"] = options.device
    images = [image]
    if crop_model is not None:
        detection = crop_model.predict(source=image, **kwargs)[0]
        images = [image.crop(tuple(box)) for box in detection.boxes.xyxy.tolist()]
    predictions = []
    for crop in images:
        result = model.predict(source=crop, **kwargs)[0]
        predictions.extend(result_labels(result))
    return sorted(predictions, key=lambda item: (-item["confidence"], item["label"]))


def label_folder(label: str):
    # Encode path separators and Windows-special names while keeping labels readable.
    encoded = quote(label, safe=" -_+").replace(".", "%2E")
    encoded = encoded.rstrip(" ") + "%20" * (len(encoded) - len(encoded.rstrip(" ")))
    if encoded.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}:
        encoded = f"%{ord(encoded[0]):02X}" + encoded[1:]
    return encoded


def scan(options: ScanOptions, index_path: Path, log_path: Path, stop: Event, emit):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handler = logging.FileHandler(log_path, encoding="utf-8")
    log_handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(log_handler)
    try:
        formats = IMG_FORMATS | VID_FORMATS
        total = sum(
            path.is_file() and path.suffix.removeprefix(".").lower() in formats
            for path in options.source.iterdir()
        )
        emit("total", total)
        emit("status", "Loading YOLO models")
        model = load_model(options.model)
        crop_model = load_model(options.crop_model) if options.crop_model else None
        signature = asdict(options)
        signature.pop("source")
        signature["ultralytics"] = ultralytics.__version__
        signature["pipeline_version"] = 2
        signature["weights"] = []
        for loaded in [model] + ([crop_model] if crop_model is not None else []):
            weights = Path(loaded.ckpt_path if loaded.ckpt_path else loaded.model).resolve()
            stat = weights.stat()
            signature["weights"].append([str(weights), stat.st_size, stat.st_mtime_ns])
        signature = json.dumps(signature, sort_keys=True)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        results = []
        with closing(sqlite3.connect(index_path)) as database:
            database.execute("""CREATE TABLE IF NOT EXISTS media (
                path TEXT NOT NULL, signature TEXT NOT NULL, size INTEGER NOT NULL,
                modified INTEGER NOT NULL, predictions TEXT NOT NULL, frame INTEGER,
                PRIMARY KEY(path, signature))""")
            kwargs = {"verbose": True, "save": False, "conf": options.scan_confidence, "stream": True}
            if options.device:
                kwargs["device"] = options.device
            status = f"Scanning (0/{total})"
            emit("status", status)
            indexed = {}
            device_reported = False
            inference = (crop_model if crop_model is not None else model).predict(source=str(options.source), **kwargs)
            for inference_result in inference:
                if not device_reported:
                    output = inference_result.probs if inference_result.probs is not None else (
                        inference_result.obb if inference_result.obb is not None else inference_result.boxes
                    )
                    device = output.data.device
                    device_name = str(device)
                    if device.type == "cuda":
                        device_name += f" ({torch.cuda.get_device_name(device)})"
                    LOGGER.info(f"Inference device: {device_name}")
                    emit("device", device_name)
                    device_reported = True
                path = Path(inference_result.path)
                path = (path if path.is_absolute() else options.source / path).resolve()
                first_result_for_path = path not in indexed
                stat = path.stat()
                if crop_model is None:
                    predictions = result_labels(inference_result)
                else:
                    image = Image.fromarray(cv2.cvtColor(inference_result.orig_img, cv2.COLOR_BGR2RGB))
                    crops = [image.crop(tuple(box)) for box in inference_result.boxes.xyxy.tolist()]
                    predictions = [
                        prediction
                        for crop in crops
                        for result in model.predict(source=crop, **kwargs)
                        for prediction in result_labels(result)
                    ]
                predictions.sort(key=lambda item: (-item["confidence"], item["label"]))
                database.execute(
                    "INSERT OR REPLACE INTO media VALUES (?, ?, ?, ?, ?, ?)",
                    (str(path), signature, stat.st_size, stat.st_mtime_ns, json.dumps(predictions), None),
                )
                indexed[path] = MediaResult(path, None, None, predictions, None, False, None)
                if first_result_for_path:
                    completed = len(indexed)
                    emit("scan_progress", (completed, total, path.name))
                if stop.is_set():
                    break
            database.commit()
            results = list(indexed.values())
            for result in results:
                emit("item", result)
        return results
    finally:
        LOGGER.removeHandler(log_handler)
        log_handler.close()
