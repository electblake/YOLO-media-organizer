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


def test_reset_is_unsaved_and_preserves_api_launch_overrides(tmp_path):
    AppConfig(model="user-default", ultralytics_api_key="saved-key").save(tmp_path / "config.json")
    AppState(model="saved-model", active_tab="Extras", selected_labels=["person"]).save(tmp_path / "state.json")
    settings = Settings(tmp_path, {"model": "launch-model", "ultralytics_api_key": "launch-key"})
    config_before = settings.config_path.read_bytes()
    state_before = settings.state_path.read_bytes()
    settings.reset_state()
    assert settings.values.model == AppState().model
    assert settings.values.active_tab == "Scan"
    assert settings.values.selected_labels == []
    assert settings.values.ultralytics_api_key == "launch-key"
    assert settings.state.model == "saved-model"
    assert settings.config_path.read_bytes() == config_before
    assert settings.state_path.read_bytes() == state_before
    assert Settings(tmp_path, {}).values.model == "saved-model"
    settings.save_state(AppState.model_validate(settings.values.model_dump()))
    restored = Settings(tmp_path, {})
    assert restored.values.model == AppState().model
    assert restored.values.active_tab == "Scan"
    assert restored.values.ultralytics_api_key == "saved-key"
    assert settings.config_path.read_bytes() == config_before


def test_first_launch_reset_does_not_create_saved_files(tmp_path):
    settings = Settings(tmp_path, {"model": "launch-model"})
    settings.reset_state()
    assert settings.values.model == AppState().model
    assert not settings.config_path.exists()
    assert not settings.state_path.exists()


def test_ui_manual_save_reset_and_default_without_auto_saving(tmp_path):
    script = '''
import sys
import tkinter as tk
from pathlib import Path
from app.config import AppConfig, AppState, Settings
from app.main import MainView
from app.scanner import MediaResult, ScanOptions
directory = Path(sys.argv[1])
AppConfig(model="configured", source=str(directory), move_confidence=.6).save(directory / "config.json")
root = tk.Tk()
root.withdraw()
settings = Settings(directory, {})
view = MainView(root, settings)
assert not settings.state_path.exists()
assert [view.tabs.tab(tab, "text") for tab in view.tabs.tabs()] == ["Sort Media", "Models", "Settings", "Extras"]
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
assert view.model.get() == AppState().model
assert view.move_confidence.get() == AppState().move_confidence
assert view.sort_columns == {}
assert not view.label_vars["dynamic"].get()
assert restored.state_path.read_text() == saved
assert Settings(directory, {}).values.model == "custom"
assert view.ultralytics_api_key.get() == "manual-test-key"
assert restored.values.ultralytics_api_key == "manual-test-key"
view.model.set("new-default")
view.move_confidence.set(.42)
assert restored.config.model == "configured"
view.default_config_button.invoke()
assert Settings(directory, {}).values.model == "new-default"
view.model.set("unsaved")
view.reset_config_button.invoke()
assert view.model.get() == AppState().model
assert view.move_confidence.get() == AppState().move_confidence
view.model.set("discard-on-close")
before_close = restored.state_path.read_text()
view.close()
assert restored.state_path.read_text() == before_close
assert Settings(directory, {}).values.model == "new-default"
'''
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)


def test_layout_dividers_and_persistent_controls(tmp_path):
    script = """
import sys
import tkinter as tk
from pathlib import Path
from app.config import AppState, Settings
from app.main import MainView
root = tk.Tk()
root.geometry("1440x960")
settings = Settings(Path(sys.argv[1]), {"active_tab": "Settings", "scan_divider": 240})
view = MainView(root, settings)
view.pack(fill="both", expand=True)
root.update()
view.save_config()
assert settings.state.scan_divider == 240
view.tabs.select(view.scan_tab)
root.update()
assert view.scan_panes.sashpos(0) == 240
view.main_panes.sashpos(0, 500)
view.scan_panes.sashpos(0, 80)
root.update()
assert view.main_scrollbar.winfo_ismapped()
view.main_canvas.yview_moveto(1)
assert view.main_canvas.yview()[0] > 0
view.scan_panes.sashpos(0, 200)
root.update()
assert view.label_canvas.winfo_height() > 64
saved = settings.state_path.read_bytes()
for tab in (view.settings_tab, view.extras_tab, view.scan_tab):
    view.tabs.select(tab)
    root.update()
    assert all(widget.winfo_ismapped() for widget in (
        view.scan_button, view.move_button, view.stop_button,
        view.save_config_button, view.progress, view.tree,
    ))
assert view.scan_panes.sashpos(0) == 200
assert settings.state_path.read_bytes() == saved
view.save_config()
view.executor.shutdown(wait=False)
view.destroy()
settings = Settings(Path(sys.argv[1]), {})
view = MainView(root, settings)
view.pack(fill="both", expand=True)
root.update()
assert (view.main_panes.sashpos(0), view.scan_panes.sashpos(0)) == (500, 200)
root.geometry("920x620")
root.update()
assert view.main_panes.sashpos(0) == 500
assert view.tree.winfo_width() > 300
view.inputs[0].focus_force()
root.update()
view.inputs[0].event_generate("<Tab>")
root.update()
assert root.focus_get() == view.inputs[1]
view.reset_config()
root.update()
assert view.main_panes.sashpos(0) == AppState().main_divider
assert view.scan_panes.sashpos(0) == AppState().scan_divider
assert Settings(Path(sys.argv[1]), {}).values.scan_divider == 200
view.close()
"""
    subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True)
