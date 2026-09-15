"""User configuration, saved UI state, and app-owned directories."""

import os
from pathlib import Path
from typing import Literal

from platformdirs import PlatformDirs
from pydantic import BaseModel, Field

dirs = PlatformDirs("YOLO-media-sorter", appauthor=False)
CONFIG_DIR = dirs.user_config_path
MODELS_DIR = CONFIG_DIR / "models"
HF_CACHE_DIR = MODELS_DIR / "huggingface"


class AppState(BaseModel):
    source: str = ""
    model: str = "DhanushSGowda/yolov8n-gender-classification"
    crop_model: str = ""
    scan_confidence: float = 0.25
    move_confidence: float = 0.5
    min_predictions: int = 1
    max_predictions: int = -1
    frame_percentage: float = 50
    device: str = ""
    recursive: bool = True
    videos: bool = True
    selected_labels: list[str] = Field(default_factory=list)
    sort_columns: dict[str, bool] = Field(default_factory=dict)
    window_geometry: str = "1440x960"
    main_divider: int = 460
    scan_divider: int = 350
    expanded_rows: list[str] = Field(default_factory=list)
    active_tab: Literal["Scan", "Models", "Settings", "Extras"] = "Scan"

    def save(self, path: Path):
        path.write_text(self.model_dump_json(indent=2, exclude_unset=True), encoding="utf-8")


class AppConfig(AppState):
    ultralytics_api_key: str = ""
    huggingface_api_key: str = ""

    def save(self, path: Path):
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")


class Settings:
    def __init__(self, directory: Path, arguments: dict):
        directory.mkdir(parents=True, exist_ok=True)
        self.config_path = directory / "config.json"
        self.state_path = directory / "state.json"
        self.environment_keys = {
            "ULTRALYTICS_API_KEY": os.environ.get("ULTRALYTICS_API_KEY", ""),
            "HF_TOKEN": os.environ.get("HF_TOKEN", ""),
        }
        self.config = (AppConfig.model_validate_json(self.config_path.read_text(encoding="utf-8"))
                       if self.config_path.exists() else AppConfig())
        self.state = (AppState.model_validate_json(self.state_path.read_text(encoding="utf-8"))
                      if self.state_path.exists() else AppState())
        self.values = AppConfig.model_validate(
            self.config.model_dump() | self.state.model_dump(exclude_unset=True) | arguments
        )

    def save_state(self, state: AppState):
        self.state = state
        self.values = AppConfig.model_validate(self.values.model_dump() | state.model_dump(exclude_unset=True))
        self.state.save(self.state_path)

    def reset_state(self):
        self.values = AppConfig.model_validate(self.values.model_dump() | AppState().model_dump())

    def set_default(self, state: AppState):
        self.config = AppConfig.model_validate(self.config.model_dump() | state.model_dump())
        self.config.save(self.config_path)
        self.state = AppState()
        self.state.save(self.state_path)
        self.values = self.config.model_copy(deep=True)

    def save_config(self, **changes):
        self.config = AppConfig.model_validate(self.config.model_dump() | changes)
        self.config.save(self.config_path)
        self.values = AppConfig.model_validate(self.values.model_dump() | changes)
        self.apply_api_keys()

    def apply_api_keys(self):
        os.environ["ULTRALYTICS_API_KEY"] = self.values.ultralytics_api_key or self.environment_keys["ULTRALYTICS_API_KEY"]
        os.environ["HF_TOKEN"] = self.values.huggingface_api_key or self.environment_keys["HF_TOKEN"]
