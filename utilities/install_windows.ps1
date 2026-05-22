# install_windows.ps1
# One-click setup script for Windows users after `git clone`
# This script ensures a consistent Python 3.12 + uv environment.

$ErrorActionPreference = "Stop"

Write-Host "=== D&D Encounter Manager - Windows Installer ===" -ForegroundColor Cyan

# 1. Check for uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    # Refresh PATH for current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")
}

# 2. Pin Python 3.12 (project requirement)
Write-Host "Pinning Python 3.12..." -ForegroundColor Green
uv python pin 3.12

# 3. Sync dependencies (creates .venv and installs everything)
Write-Host "Running uv sync (this may take a minute)..." -ForegroundColor Green
uv sync --dev

# 4. Ensure data directories exist
$dataDir = "data\srd"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

# 5. Check for bestiary
$bestiary = "data\srd\monsters.json"
if (-not (Test-Path $bestiary)) {
    Write-Host "WARNING: $bestiary not found." -ForegroundColor Red
    Write-Host "The rich bestiary (~4400 monsters) should be included in the repo." -ForegroundColor Yellow
    Write-Host "If it's missing, re-clone or restore from git." -ForegroundColor Yellow
} else {
    Write-Host "Bestiary found: $bestiary" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To run the app:" -ForegroundColor Cyan
Write-Host "    uv run python run_ui.py" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "    uv run pytest" -ForegroundColor White
Write-Host ""
Write-Host "Tip: Always use 'uv run ...' so you use the project's exact Python + dependencies." -ForegroundColor Yellow