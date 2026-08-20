<#
.SYNOPSIS
    BioArbitrage MVP — one-command local startup (PowerShell)

.DESCRIPTION
    Starts the FastAPI backend (port 8000) and Vite frontend dev server (port 5173)
    in separate terminal windows.

.USAGE
    From the project root:
        .\start.ps1

    To stop, close the two launched terminals or press Ctrl+C in each.
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend  = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

# --- Backend ---
Write-Host "`n[BioArbitrage] Starting backend..." -ForegroundColor Cyan

$backendCmd = @"
Set-Location '$backend'
Write-Host 'Activating Python virtual environment...' -ForegroundColor Yellow
if (Test-Path '.\venv\Scripts\Activate.ps1') {
    & '.\venv\Scripts\Activate.ps1'
} else {
    Write-Host 'venv not found. Creating...' -ForegroundColor Yellow
    python -m venv venv
    & '.\venv\Scripts\Activate.ps1'
    pip install -r requirements.txt
}
Write-Host 'Starting FastAPI on http://localhost:8000' -ForegroundColor Green
uvicorn main:app --reload --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# Brief pause so backend can start first
Start-Sleep -Seconds 2

# --- Frontend ---
Write-Host "[BioArbitrage] Starting frontend..." -ForegroundColor Cyan

$frontendCmd = @"
Set-Location '$frontend'
if (-not (Test-Path '.\node_modules')) {
    Write-Host 'Installing npm dependencies...' -ForegroundColor Yellow
    npm install
}
Write-Host 'Starting Vite dev server on http://localhost:5173' -ForegroundColor Green
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "`n[BioArbitrage] Both services launching in separate windows." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  API Docs: http://localhost:8000/docs`n"
