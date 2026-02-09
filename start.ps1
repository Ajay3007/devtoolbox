# One-click launcher for DevToolBox (Windows)
param(
    [switch]$SkipBrowser
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $root

$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

$pythonExe = Join-Path $root ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python virtual environment not found. Create/activate .venv first."
}

$frontendNodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Warning "frontend/node_modules is missing. Run 'cd frontend; npm install' before launching."
}

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error "Node.js not found in PATH. Install Node.js or add it to PATH."
}

$backendCmd = "& { Set-Location -LiteralPath '$backendDir'; & '$pythonExe' app.py }"
$frontendCmd = "& { Set-Location -LiteralPath '$frontendDir'; & node node_modules/vite/bin/vite.js --host }"

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $backendCmd | Out-Null
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $frontendCmd | Out-Null

if (-not $SkipBrowser) {
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:8080" | Out-Null
}

Write-Host "Backend: http://127.0.0.1:5000"
Write-Host "Frontend: http://localhost:8080"
if ($SkipBrowser) {
    Write-Host "Browser not auto-opened (SkipBrowser)."
} else {
    Write-Host "Browser opened to http://localhost:8080"
}
