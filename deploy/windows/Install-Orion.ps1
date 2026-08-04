[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$InstallPath = "C:\Program Files\MusicClean",
    [string]$StatePath = "C:\ProgramData\MusicClean",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([Parameter(Mandatory=$true)][string]$Path)

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Test-OrionHealth {
    param(
        [string]$Uri = "http://127.0.0.1:8765/v1/health"
    )

    $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -ne 200) {
        throw "Orion health check failed with HTTP $($response.StatusCode)."
    }
}

Ensure-Directory -Path $InstallPath
Ensure-Directory -Path $StatePath
Ensure-Directory -Path (Join-Path $StatePath "telemetry")
Ensure-Directory -Path (Join-Path $StatePath "logs")

$venv = Join-Path $InstallPath ".venv"
$pythonExe = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    & $Python -m venv $venv
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -e "$InstallPath[orion-runtime]"

Write-Host "Runtime installed at $InstallPath"
Write-Host "Configure service environment before starting Orion."
Write-Host "After startup, run Test-OrionHealth to verify /v1/health."
