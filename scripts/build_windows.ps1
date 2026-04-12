param(
    [switch]$Clean = $true
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if ($Clean) {
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
}

python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install pyinstaller
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name PX4OfflineTuner `
    --paths src `
    --hidden-import px4_offline_tuner.webapp `
    --collect-all streamlit `
    --collect-all plotly `
    --collect-all altair `
    --collect-all pydeck `
    --collect-all pyarrow `
    --collect-data pyulog `
    --add-data "sample_data;sample_data" `
    src/px4_offline_tuner/desktop.py

Write-Host ""
Write-Host "Build complete:"
Write-Host "dist/PX4OfflineTuner/PX4OfflineTuner.exe"
