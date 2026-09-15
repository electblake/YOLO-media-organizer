$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) ".venv-build"
uv sync --locked --no-default-groups --group build
uv run --no-sync python -m PyInstaller scripts/YOLO-media-sorter.spec --clean --noconfirm
uv run --no-sync python scripts/bundle-notices.py
