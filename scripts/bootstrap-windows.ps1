$ErrorActionPreference = "Stop"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11 or newer."
}

py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -e ".[dev]"
& .\.venv\Scripts\musicclean.exe init

Write-Host ""
Write-Host "MusicClean development environment is ready."
Write-Host "Activate it with: .\.venv\Scripts\Activate.ps1"
