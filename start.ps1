param(
    [string]$HostName = "localhost",
    [int]$Port = 8080,          # Frontend Port
    [int]$BackendPort = 5000,   # Backend API Port
    [switch]$SkipBrowser
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $root

$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

# Check for virtual environment python, fallback to system python
$pythonExe = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
    Write-Warning "Python virtual environment not found in .venv. Falling back to system python."
}

$frontendNodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Warning "frontend/node_modules is missing. Please run 'cd frontend; npm install' prior to launching if it fails."
}

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error "Node.js not found in PATH. Install Node.js or add it to PATH."
}

# Dynamically set Environment Variables in the new processes
$backendCmd = "& { Set-Location -LiteralPath '$backendDir'; `$env:PORT='$BackendPort'; `$env:FLASK_DEBUG='True'; & '$pythonExe' app.py }"
$frontendCmd = "& { Set-Location -LiteralPath '$frontendDir'; `$env:VITE_API_BASE_URL='http://$HostName`:$BackendPort/api'; & npm run dev -- --host $HostName --port $Port }"

# Launch Backend and Frontend in separate PowerShell Windows
Write-Host "Starting Backend API on Port $BackendPort..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $backendCmd | Out-Null

Write-Host "Starting Frontend Vite Server on $HostName`:$Port..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $frontendCmd | Out-Null

$frontendUrl = "http://${HostName}:${Port}"

if (-not $SkipBrowser) {
    Write-Host "Waiting a few seconds for servers to start before opening browser..." -ForegroundColor Yellow
    Start-Sleep -Seconds 4
    Start-Process $frontendUrl | Out-Null
}

Write-Host "`nDevToolBox Started Successfully!" -ForegroundColor Green
Write-Host "Backend API running on : http://$HostName`:$BackendPort"
Write-Host "Frontend App running on: $frontendUrl`n"

if ($SkipBrowser) {
    Write-Host "Browser not auto-opened (SkipBrowser switch used)."
} else {
    Write-Host "Browser opened to $frontendUrl"
}
