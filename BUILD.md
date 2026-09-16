# Build instructions

## Build Windows artifacts

Build both CPU and CUDA 13.0 bundles, then create their installers and portable ZIPs:

```powershell
./scripts/build.ps1
./scripts/build-setup.ps1
```

To build one variant, pass `-Backend cpu` or `-Backend gpu` to both scripts.
Artifacts in `dist/` are labeled `cpu` or `cu130`, with separate `SHA256SUMS-cpu.txt` and `SHA256SUMS-cu130.txt` files.

## Build Pip Wheel

```powershell
./scripts/build-wheel.ps1
```

```sh
pip install ./dist/yolo_media_organizer-0.6.2-py3-none-any.whl
yolo-media-organizer
```
