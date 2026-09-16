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
    monkeypatch.setattr(scanner.ultralytics, "settings", settings)
    monkeypatch.setenv("ULTRALYTICS_API_KEY", "test-platform-key")
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
    monkeypatch.setattr(scanner, "get_token", lambda: "test-hf-token")

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

    def retrieve(url, target, reporthook):
        url_calls.append(url)
        target.write_bytes(b"downloaded weights")

    monkeypatch.setattr(scanner, "urlretrieve", retrieve)
    url = "https://example.com/models/custom.pt"
    downloaded = scanner.load_model(url)
    assert downloaded.is_relative_to(models / "urls")
    assert scanner.load_model(url) == downloaded
    assert url_calls == [url]

    def retrieve_archive(url, target, reporthook):
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


@pytest.mark.parametrize("reference", ["ul://owner/project/model", "https://platform.ultralytics.com/owner/project/model"])
@pytest.mark.parametrize("key_source", ["missing", "environment", "ultralytics_settings"])
def test_platform_model_requires_api_key(tmp_path, monkeypatch, reference, key_source):
    monkeypatch.delenv("ULTRALYTICS_API_KEY", raising=False)
    settings = {}
    monkeypatch.setattr(scanner.ultralytics, "settings", settings)
    if key_source == "environment":
        monkeypatch.setenv("ULTRALYTICS_API_KEY", "test-platform-key")
    elif key_source == "ultralytics_settings":
        settings["api_key"] = "test-platform-key"
    calls = []

    def download(reference, download_dir):
        calls.append(reference)
        return str(tmp_path / "model.pt")

    monkeypatch.setattr(scanner, "check_file", download)
    monkeypatch.setattr(scanner, "YOLO", lambda reference: Path(reference))
    if key_source == "missing":
        with pytest.raises(ValueError, match="Set ULTRALYTICS_API_KEY in Settings or your environment"):
            scanner.load_model(reference)
        assert calls == []
    else:
        assert scanner.load_model(reference) == tmp_path / "model.pt"
        assert calls == ["ul://owner/project/model"]


@pytest.mark.parametrize("token", [None, "test-hf-token"])
def test_hf_model_requires_token(tmp_path, monkeypatch, token):
    monkeypatch.setattr(scanner.ultralytics, "settings", {})
    monkeypatch.setattr(scanner, "get_token", lambda: token)
    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        return str(tmp_path / "model.pt")

    monkeypatch.setattr(scanner, "hf_hub_download", download)
    monkeypatch.setattr(scanner, "YOLO", lambda reference: Path(reference))
    if token is None:
        with pytest.raises(ValueError, match="Set HF_TOKEN in Settings or your environment"):
            scanner.load_model("hf://owner/repo/model.pt")
        assert calls == []
    else:
        assert scanner.load_model("hf://owner/repo/model.pt") == tmp_path / "model.pt"
        assert len(calls) == 1


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
    assert all(Path(path).resolve().is_relative_to(Path(paths[0]).resolve()) for path in paths[1:])


def test_hf_progress_without_console(tmp_path, monkeypatch):
    events = []
    monkeypatch.setattr(scanner, "get_token", lambda: "test-hf-token")
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(scanner.ultralytics, "settings", SimpleNamespace(update=lambda **kwargs: None))
    monkeypatch.setattr(scanner, "YOLO", lambda reference: SimpleNamespace(names={0: "person"}))

    def download(**kwargs):
        with kwargs["tqdm_class"](total=100, desc="model.pt", mininterval=0) as progress:
            progress.update(50)
            progress.update(50)
        return str(tmp_path / "model.pt")

    monkeypatch.setattr(scanner, "hf_hub_download", download)
    model = scanner.load_model("hf://owner/repo/model.pt", lambda *event: events.append(event))
    assert model.names == {0: "person"}
    assert ("download_progress", ("model.pt", 50, 100)) in events
    assert ("download_progress", ("model.pt", 100, 100)) in events
    assert events[-1] == ("status", "Reading model classes")
