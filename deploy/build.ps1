# Travel Inbound - Local Build & Setup Script
# Run this to set up and build the project for local development

$ErrorActionPreference = "Stop"

function Write-Step($message) { Write-Host "`n>>> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "  [OK] $message" -ForegroundColor Green }
function Write-Error($message) { Write-Host "  [ERROR] $message" -ForegroundColor Red }
function Write-Warning($message) { Write-Host "  [WARN] $message" -ForegroundColor Yellow }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Travel Inbound - Build & Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check Python
Write-Step "Checking Python..."
$pythonCmd = $null
$pythonPaths = @(
    "python", "python3", "py",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
)
foreach ($cmd in $pythonPaths) {
    try {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python") {
            $pythonCmd = $cmd
            Write-Success "Found: $ver"
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Error "Python not found. Please install Python 3.10+ from:"
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Or: winget install Python.Python.3.11" -ForegroundColor Yellow
    Write-Host "`nMake sure to check 'Add Python to PATH' during installation." -ForegroundColor Gray
    exit 1
}

# Step 2: Create virtual environment
$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Step "Creating virtual environment..."
    & $pythonCmd -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
    Write-Success "Virtual environment created at .venv"
} else {
    Write-Success "Virtual environment already exists"
}

# Step 3: Activate venv and install dependencies
Write-Step "Installing dependencies..."
$pipPath = Join-Path $venvPath "Scripts\pip.exe"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"

& $pipPath install --upgrade pip -q
& $pipPath install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies"
    exit 1
}
Write-Success "Dependencies installed"

# Step 4: Ensure instance directory exists (for SQLite)
$instancePath = "instance"
if (-not (Test-Path $instancePath)) {
    New-Item -ItemType Directory -Path $instancePath | Out-Null
    Write-Success "Created instance directory"
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nTo run the server:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python start_server.py" -ForegroundColor White
Write-Host "`nOr in one line:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\python.exe start_server.py" -ForegroundColor White
Write-Host "`nServer will be at: http://localhost:5000" -ForegroundColor Gray
Write-Host ""
