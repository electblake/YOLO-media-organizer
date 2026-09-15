<img src="assets/YOLOmo-blue.png" alt="YOLOmo" width="500" style="max-width: 100%; height: auto;">

# YOLO Media Organizer

<strong>YOLOmo</strong> is a desktop app for sorting images and videos using Ultralytics YOLO models.

## Install

Download the [Windows installer](https://github.com/electblake/YOLO-media-organizer/releases/download/v0.6.1/YOLO-media-organizer-0.6.1-windows-amd64-Setup.exe), run it, then open the app from the Start menu.

## Run from source

```powershell
uv sync
uv run yolo-media-organizer
```

## Build a wheel

With uv and PowerShell 7 installed, run:

```powershell
./scripts/build-wheel.ps1
```

The wheel is written to `dist/` using the version in `pyproject.toml`.
To install and run it in a Python 3.12+ environment with Tkinter available:

```powershell
python -m pip install ./dist/yolo_media_organizer-0.6.1-py3-none-any.whl
yolo-media-organizer
```

Dependencies are installed separately by pip; they are not bundled in the wheel.


- [Models](Models.md)
- [CHANGELOG.md](CHANGELOG.md)

## Disclaimer

This project is not affiliated with Ultralytics or the [YOLO models](https://docs.ultralytics.com/models). For more information, see the [Ultralytics documentation](https://docs.ultralytics.com) and [Ultralytics website](https://www.ultralytics.com).

YOLO is licensed under [AGPL-3.0 license](LICENSE) so we use that license here.
