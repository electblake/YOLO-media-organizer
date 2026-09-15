$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) ".venv-build/Scripts/python.exe"
$version = & $python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
$architecture = & $python -c "import platform; print(platform.machine().lower())"
$isccPath = Join-Path $env:LOCALAPPDATA "Programs/Inno Setup 6/ISCC.exe"
& $isccPath "/DAppVersion=$version" "/DAppArchitecture=$architecture" "scripts/installer.iss"
& $python -c "import shutil; shutil.make_archive('dist/YOLO-media-organizer-$version-windows-$architecture-portable', 'zip', 'dist', 'YOLO-media-organizer-$version-windows-$architecture')"
$artifacts = @("dist/YOLO-media-organizer-$version-windows-$architecture-Setup.exe", "dist/YOLO-media-organizer-$version-windows-$architecture-portable.zip")
$artifacts | Get-FileHash -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" } | Set-Content -Encoding ascii "dist/SHA256SUMS.txt"
