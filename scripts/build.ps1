param(
    [ValidateSet("cpu", "gpu")]
    [string[]]$Backend = @("cpu", "gpu")
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONDONTWRITEBYTECODE = "1"
foreach ($variant in $Backend) {
    $env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) ".venv-build/$variant"
    $env:YOLO_BUILD_BACKEND = @{ cpu = "cpu"; gpu = "cu130" }[$variant]
    uv sync --locked --no-default-groups --group build --group $variant
    uv run --no-sync python -m PyInstaller scripts/YOLO-media-organizer.spec --workpath "build/$variant" --clean --noconfirm
    uv run --no-sync python scripts/bundle-notices.py
}
