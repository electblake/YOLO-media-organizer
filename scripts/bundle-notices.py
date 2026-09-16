"""Include installed dependency licenses with the release bundle."""

import importlib.metadata
import os
import platform
import shutil
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parent.parent
version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
bundle = root / "dist" / f"YOLO-media-organizer-{version}-windows-{platform.machine().lower()}-{os.environ['YOLO_BUILD_BACKEND']}"
for distribution in importlib.metadata.distributions():
    for file in distribution.files:
        if file.name.lower().startswith(("license", "copying", "notice")):
            target = bundle / "licenses" / distribution.metadata["Name"] / file
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(distribution.locate_file(file), target)
