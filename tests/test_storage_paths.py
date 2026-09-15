import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from app import scanner
from app.config import CONFIG_DIR, dirs


def test_model_storage_routes(tmp_path, monkeypatch):
    config = tmp_path / "config"
    models = config / "models"
    hf_cache = models / "huggingface"
    monkeypatch.setattr(scanner, "CONFIG_DIR", config)
    monkeypatch.setattr(scanner, "MODELS_DIR", models)
    monkeypatch.setattr(scanner, "HF_CACHE_DIR", hf_cache)
    settings = {}
    monkeypatch.setattr(scanner.ultralytics, "settings", SimpleNamespace(update=lambda **kwargs: settings.update(kwargs)))
    monkeypatch.setattr(scanner, "YOLO", lambda reference: Path(reference))
    monkeypatch.chdir(tmp_path)
    platform_calls = []

    def platform_file(reference, download_dir):
        platform_calls.append((reference, download_dir))
        return str(download_dir / "rpi5/person-detection/yolov8nbest/best.pt")

    monkeypatch.setattr(scanner, "check_file", platform_file)
    platform_uri = scanner.MODEL_PRESETS["rpi5/person-detection/yolov8nbest"]
    platform_model = scanner.load_model(platform_uri)
    assert platform_model.is_relative_to(models / "platform")
    assert scanner.load_model("https://platform.ultralytics.com/rpi5/person-detection/yolov8nbest?tab=export") == platform_model
    assert platform_calls == [(platform_uri, models / "platform")] * 2
    assert scanner.load_model("yolo26n-cls.pt") == models / "ultralytics" / "yolo26n-cls.pt"
    assert all(Path(path).is_relative_to(config) for path in settings.values())

    hf_calls = []

    def download(**kwargs):
        hf_calls.append(kwargs)
        return str(hf_cache / "checkpoint.pt")

    monkeypatch.setattr(scanner, "hf_hub_download", download)
    assert scanner.load_model("hf://owner/repo/nested/model.pt") == hf_cache / "checkpoint.pt"
    assert hf_calls == [{"repo_id": "owner/repo", "filename": "nested/model.pt", "cache_dir": hf_cache}]

    local = tmp_path / "custom.pt"
    local.write_bytes(b"custom weights")
    imported = scanner.load_model(str(local))
    assert imported.is_relative_to(models / "local")
    assert imported.read_bytes() == local.read_bytes()
    assert local.exists()
    assert scanner.load_model(str(imported)) == imported
    local.write_bytes(b"updated weights")
    assert scanner.load_model(str(local)).read_bytes() == b"updated weights"
    export = tmp_path / "export"
    export.mkdir()
    (export / "model.xml").write_text("model")
    assert (scanner.load_model(str(export)) / "model.xml").read_text() == "model"
    with pytest.raises(FileNotFoundError):
        scanner.load_model(str(tmp_path / "missing" / "custom.pt"))
    url_calls = []

    def retrieve(url, target):
        url_calls.append(url)
        target.write_bytes(b"downloaded weights")

    monkeypatch.setattr(scanner, "urlretrieve", retrieve)
    url = "https://example.com/models/custom.pt"
    downloaded = scanner.load_model(url)
    assert downloaded.is_relative_to(models / "urls")
    assert scanner.load_model(url) == downloaded
    assert url_calls == [url]

    def retrieve_archive(url, target):
        url_calls.append(url)
        with ZipFile(target, "w") as archive:
            archive.writestr("yolov8m_as03.pt", b"archived weights")

    monkeypatch.setattr(scanner, "urlretrieve", retrieve_archive)
    archive_url = scanner.MODEL_PRESETS["booru_yolo / yolov8m_as03"]
    checkpoint = scanner.load_model(archive_url)
    assert checkpoint.is_relative_to(models / "urls")
    assert checkpoint.name == "yolov8m_as03.pt"
    assert checkpoint.read_bytes() == b"archived weights"
    assert scanner.load_model(archive_url) == checkpoint
    assert url_calls == [url, archive_url]


def test_dependency_caches_use_config_root_on_startup():
    assert CONFIG_DIR == dirs.user_config_path
    script = """
import app
import json
import tempfile
from app.config import CONFIG_DIR
from huggingface_hub import constants
from ultralytics.utils import USER_CONFIG_DIR
from torch.hub import get_dir
from matplotlib import get_configdir
print(json.dumps([str(CONFIG_DIR), str(constants.HF_HUB_CACHE), str(constants.HF_XET_CACHE),
                  str(USER_CONFIG_DIR), get_dir(), get_configdir(), tempfile.gettempdir()]))
"""
    paths = json.loads(subprocess.check_output([sys.executable, "-c", script], text=True).splitlines()[-1])
    assert all(Path(path).is_relative_to(Path(paths[0])) for path in paths[1:])
