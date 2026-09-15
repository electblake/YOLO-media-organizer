import subprocess
import sys

import pytest
from pydantic import ValidationError

from app.arguments import build_parser
from app.config import AppConfig, AppState, Settings


def test_defaults_config_state_and_explicit_arguments(tmp_path):
    AppConfig(model="configured", move_confidence=0.7, device="cpu", videos=False).save(tmp_path / "config.json")
    AppState(model="remembered", move_confidence=0.8, recursive=False).save(tmp_path / "state.json")
    assert vars(build_parser().parse_args([])) == {}
    arguments = vars(build_parser().parse_args(["--model", "argument", "--move-confidence", "0", "--videos"]))
    settings = Settings(tmp_path, arguments)
    assert settings.values.model == "argument"
    assert settings.values.move_confidence == 0
    assert settings.values.device == "cpu"
    assert settings.values.videos is True
    assert settings.values.recursive is False
    assert settings.values.min_predictions == 1
    settings.save_state(AppState.model_validate(settings.state.model_dump(exclude_unset=True) | {"source": "chosen folder"}))
    restored = Settings(tmp_path, {})
    assert restored.values.model == "remembered"
    assert restored.values.move_confidence == 0.8
    assert restored.values.source == "chosen folder"
    assert restored.values.videos is False
    assert "device" not in restored.state.model_fields_set
    assert restored.config.source == ""
    assert vars(build_parser().parse_args(["--no-recursive", "--selected-labels"])) == {
        "recursive": False, "selected_labels": [],
    }


def test_first_launch_uses_defaults_without_writing_files(tmp_path):
    settings = Settings(tmp_path, {})
    assert settings.values == AppConfig()
    assert not settings.config_path.exists()
    assert not settings.state_path.exists()
    settings.state_path.write_text('{"min_predictions": "invalid"}')
    with pytest.raises(ValidationError):
        Settings(tmp_path, {})


def test_api_overrides_save_only_to_config_and_clear_to_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ULTRALYTICS_API_KEY", "environment-ultralytics")
    monkeypatch.setenv("HF_TOKEN", "environment-hf")
    settings = Settings(tmp_path, {})
    settings.apply_api_keys()
    import os
    assert os.environ["HF_TOKEN"] == "environment-hf"
    assert not settings.config_path.exists()
    settings.save_config(ultralytics_api_key="manual-ultralytics", huggingface_api_key="manual-hf")
    assert os.environ["ULTRALYTICS_API_KEY"] == "manual-ultralytics"
    assert os.environ["HF_TOKEN"] == "manual-hf"
    assert settings.environment_keys["HF_TOKEN"] == "environment-hf"
    assert not settings.state_path.exists()
    assert "environment-" not in settings.config_path.read_text()
    settings.save_config(ultralytics_api_key="", huggingface_api_key="")
    assert os.environ["HF_TOKEN"] == "environment-hf"
    assert os.environ["ULTRALYTICS_API_KEY"] == "environment-ultralytics"


def test_ui_manual_save_reset_and_default_without_auto_saving(tmp_path):
    script = '''
import sys
import tkinter as tk
from pathlib import Path
from app.config import AppConfig, Settings
from app.main import MainView
from app.scanner import MediaResult, ScanOptions
directory = Path(sys.argv[1])
AppConfig(model="configured", source=str(directory), move_confidence=.6).save(directory / "config.json")
root = tk.Tk()
root.withdraw()
settings = Settings(directory, {})
view = MainView(root, settings)
assert not settings.state_path.exists()
assert [view.tabs.tab(tab, "text") for tab in view.tabs.tabs()] == ["Scan", "Settings"]
assert view.config_path_var.get() == str(settings.config_path)
config_before = settings.config_path.read_text()
view.ultralytics_api_key.set("manual-test-key")
view.huggingface_api_key.set("manual-test-hf")
assert settings.config_path.read_text() == config_before
assert not settings.state_path.exists()
view.save_settings_button.invoke()
assert settings.config.ultralytics_api_key == "manual-test-key"
assert settings.config.huggingface_api_key == "manual-test-hf"
assert not settings.state_path.exists()
view.options = ScanOptions(directory)
result = MediaResult(directory / "image.png", None, None, [{"label": "dynamic", "confidence": .9}], None, False, None)
view.results = [result]
view.refresh_results()
view.model.set("custom")
view.move_confidence.set(.75)
view.recursive.set(False)
view.label_checks["dynamic"].invoke()
view.toggle_sort("confidence")
view.set_preview_expanded(True)
view.tabs.select(view.settings_tab)
root.update()
assert not settings.state_path.exists()
view.tabs.select(view.scan_tab)
view.save_config_button.invoke()
saved = settings.state_path.read_text()
view.executor.shutdown(wait=False)
view.destroy()
restored = Settings(directory, {})
view = MainView(root, restored)
assert view.model.get() == "custom"
assert view.ultralytics_api_key.get() == "manual-test-key"
assert view.huggingface_api_key.get() == "manual-test-hf"
assert view.move_confidence.get() == .75
assert not view.recursive.get()
assert view.source.get() == str(directory)
view.options = ScanOptions(directory)
view.results = [result]
view.refresh_results()
assert view.label_vars["dynamic"].get()
assert view.sort_columns == {"confidence": False}
assert view.tree.item(str(result.source), "open")
assert restored.state_path.read_text() == saved
assert restored.config.model == "configured"
view.reset_config_button.invoke()
assert view.model.get() == "configured"
assert view.move_confidence.get() == .6
assert view.sort_columns == {}
assert not view.label_vars["dynamic"].get()
assert restored.state_path.read_text() == "{}"
view.model.set("new-default")
view.move_confidence.set(.42)
assert restored.config.model == "configured"
view.default_config_button.invoke()
assert Settings(directory, {}).values.model == "new-default"
view.model.set("unsaved")
view.reset_config_button.invoke()
assert view.model.get() == "new-default"
assert view.move_confidence.get() == .42
view.model.set("discard-on-close")
before_close = restored.state_path.read_text()
view.close()
assert restored.state_path.read_text() == before_close
assert Settings(directory, {}).values.model == "new-default"
'''
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
