# Build instructions

## Build Windows artifacts

Build both CPU and CUDA 13.0 bundles, then create their installers:

```powershell
./scripts/build.ps1
./scripts/build-setup.ps1
```

To build one variant, pass `-Backend cpu` or `-Backend gpu` to both scripts.
Installers in `dist/` are labeled `cpu` or `cu130`. Releases include only these two installers.
Installers larger than 500 MB are packaged into 500 MB 7z volumes; download every part and extract `.7z.001` to recover the installer.

## Build Pip Wheel

```powershell
./scripts/build-wheel.ps1
```

```sh
pip install ./dist/yolo_media_organizer-0.6.2-py3-none-any.whl
yolo-media-organizer
```
