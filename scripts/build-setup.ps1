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
    if ((Get-Item "dist/$artifact-Setup.exe").Length -gt 500MB) {
        Push-Location dist
        7z a -t7z -mx=0 -v500m "$artifact-Setup.7z" "$artifact-Setup.exe"
        Pop-Location
    }
}
