"""Locations for app-managed files and dependency caches."""

import os
import tempfile

from platformdirs import PlatformDirs

dirs = PlatformDirs("YOLO-media-sorter", appauthor=False)
CONFIG_DIR = dirs.user_config_path
MODELS_DIR = CONFIG_DIR / "models"
HF_CACHE_DIR = MODELS_DIR / "huggingface"


def configure_runtime():
    locations = {
        "YOLO_CONFIG_DIR": CONFIG_DIR / "ultralytics",
        "HF_HOME": CONFIG_DIR / "huggingface",
        "HF_HUB_CACHE": HF_CACHE_DIR,
        "HF_XET_CACHE": CONFIG_DIR / "cache" / "xet",
        "TORCH_HOME": CONFIG_DIR / "cache" / "torch",
        "TORCHINDUCTOR_CACHE_DIR": CONFIG_DIR / "cache" / "torchinductor",
        "TRITON_CACHE_DIR": CONFIG_DIR / "cache" / "triton",
        "CUDA_CACHE_PATH": CONFIG_DIR / "cache" / "cuda",
        "PYTORCH_KERNEL_CACHE_PATH": CONFIG_DIR / "cache" / "torch-kernels",
        "MPLCONFIGDIR": CONFIG_DIR / "cache" / "matplotlib",
    }
    for variable, directory in locations.items():
        directory.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(directory)
    temporary = CONFIG_DIR / "cache" / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temporary)
