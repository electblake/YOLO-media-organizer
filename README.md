<img src="assets/YOLOmo-blue.png" alt="YOLOmo" width="500" style="max-width: 100%; height: auto;">

# YOLO Media Organizer

<strong>YOLOmo</strong> is a desktop app for sorting images and videos using Ultralytics YOLO models.

## Installer

[Download the latest installer (Windows)](https://github.com/electblake/YOLO-media-organizer/releases)

Choose CPU or NVIDIA GPU during setup. Installer will download Python and dependencies. GPU mode requires an NVIDIA driver compatible with CUDA 13.0.

## Run from source

```powershell
uv sync --locked --group cpu
uv run --no-sync yolo-media-organizer
```

Use `--group gpu` for NVIDIA CUDA 13.0.

## Build the Windows installer

Requires PowerShell 7 and Inno Setup 6.7.3.

```powershell
./scripts/build-setup.ps1
```

The installer is written to `dist/`.

- [Models](Models.md)
- [CHANGELOG.md](CHANGELOG.md)

## Disclaimer

This project is not affiliated with Ultralytics or the [YOLO models](https://docs.ultralytics.com/models). For more information, see the [Ultralytics documentation](https://docs.ultralytics.com) and [Ultralytics website](https://www.ultralytics.com).

YOLO is licensed under [AGPL-3.0 license](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) so we use that [license here](LICENSE).
