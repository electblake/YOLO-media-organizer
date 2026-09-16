param(
    [ValidateSet("cpu", "gpu")]
    [string[]]$Backend = @("cpu", "gpu")
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
$isccPath = Join-Path $env:LOCALAPPDATA "Programs/Inno Setup 6/ISCC.exe"
foreach ($variant in $Backend) {
    $python = Join-Path (Get-Location) ".venv-build/$variant/Scripts/python.exe"
    $version = & $python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
    $architecture = & $python -c "import platform; print(platform.machine().lower())"
    $backendLabel = @{ cpu = "cpu"; gpu = "cu130" }[$variant]
    $artifact = "YOLO-media-organizer-$version-windows-$architecture-$backendLabel"
    & $isccPath "/DAppVersion=$version" "/DAppArchitecture=$architecture" "/DAppBackend=$backendLabel" "scripts/installer.iss"
    & $python -c "import shutil; shutil.make_archive('dist/$artifact-portable', 'zip', 'dist', '$artifact')"
    $artifacts = @("dist/$artifact-Setup.exe", "dist/$artifact-portable.zip")
    $artifacts | Get-FileHash -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" } | Set-Content -Encoding ascii "dist/SHA256SUMS-$backendLabel.txt"
}
