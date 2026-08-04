[CmdletBinding()]
param(
    [string]$RepoPath = "C:\Program Files\MusicClean",
    [string]$Python = ".venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $RepoPath

$pythonPath = Join-Path $RepoPath $Python
if (-not (Test-Path $pythonPath)) {
    throw "Python runtime not found: $pythonPath"
}

& $pythonPath -m musicclean.orion.runtime
exit $LASTEXITCODE
