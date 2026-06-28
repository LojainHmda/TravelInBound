# Automated Cloud Run Deployment Script
# Run this script to deploy Travel Inbound to Google Cloud Run
# REQUIRES: DATABASE_URL (PostgreSQL) - set in .env or $env:DATABASE_URL

$ErrorActionPreference = "Stop"

# Load .env if present (sets $env:DATABASE_URL etc.)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($key, $val, "Process")
            Set-Item -Path "env:$key" -Value $val -Force
        }
    }
}

# Colors
function Write-Step($message) { Write-Host "`n>>> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "✓ $message" -ForegroundColor Green }
function Write-Error($message) { Write-Host "✗ $message" -ForegroundColor Red }
function Write-Warning($message) { Write-Host "⚠ $message" -ForegroundColor Yellow }

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Travel Inbound - Cloud Run Deployment               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Check prerequisites
Write-Step "Step 1: Checking prerequisites..."

# Check gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
}
Write-Success "gcloud CLI found"

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Please install Docker Desktop and ensure it's running."
    Write-Host "  Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}
Write-Success "Docker found"

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Success "Docker is running"
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Check project files
if (-not (Test-Path "Dockerfile")) {
    Write-Error "Dockerfile not found in current directory"
    exit 1
}
if (-not (Test-Path "requirements.txt")) {
    Write-Error "requirements.txt not found"
    exit 1
}
if (-not (Test-Path "main.py")) {
    Write-Error "main.py not found"
    exit 1
}
Write-Success "All required files found"

# Step 2: Get project configuration
Write-Step "Step 2: Getting project configuration..."

$PROJECT_ID = gcloud config get-value project 2>$null
if (-not $PROJECT_ID) {
    Write-Error "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
}
Write-Success "Project: $PROJECT_ID"

$ACCOUNT = gcloud config get-value account 2>$null
if (-not $ACCOUNT) {
    Write-Warning "Not logged in. Attempting login..."
    gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to login"
        exit 1
    }
} else {
    Write-Success "Logged in as: $ACCOUNT"
}

# Step 3: Enable APIs
Write-Step "Step 3: Enabling required APIs..."

$apis = @(
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "sqladmin.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Enabling $api..." -NoNewline
    gcloud services enable $api --quiet 2>&1 | Out-Null
    Write-Success " Done"
}

# Step 4: Configure Docker for GCR
Write-Step "Step 4: Configuring Docker for Google Container Registry..."
gcloud auth configure-docker --quiet 2>&1 | Out-Null
Write-Success "Docker configured"

# Step 5: Build Docker image
Write-Step "Step 5: Building Docker image..."
Write-Host "  This may take 5-10 minutes..." -ForegroundColor Yellow

$IMAGE_TAG = "gcr.io/$PROJECT_ID/travel-inbound:latest"
docker build -t $IMAGE_TAG .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed!"
    exit 1
}
Write-Success "Docker image built: $IMAGE_TAG"

# Step 6: Push to Container Registry
Write-Step "Step 6: Pushing image to Container Registry..."
Write-Host "  This may take a few minutes..." -ForegroundColor Yellow

docker push $IMAGE_TAG

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed!"
    exit 1
}
Write-Success "Image pushed successfully"

# Step 6.5: Run schema migrations on production DB (ensures columns exist before deploy)
Write-Step "Step 6.5: Running schema migrations on production database..."
$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $py run_production_migrations.py 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Schema migrations complete"
} else {
    Write-Warning "Migration script had issues - app will run migrations on startup"
}

# Step 7: Generate session secret
Write-Step "Step 7: Generating session secret..."
$SESSION_SECRET = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Success "Session secret generated"

# Database URL (PostgreSQL REQUIRED for production - blocks deploy without it)
$DATABASE_URL = $env:DATABASE_URL
if (-not $DATABASE_URL -and $args.Count -gt 0) { $DATABASE_URL = $args[0] }
if ($DATABASE_URL -match '^postgres') {
    Write-Success "PostgreSQL DATABASE_URL configured"
} else {
    Write-Error "DATABASE_URL is REQUIRED for production. Data will NOT persist without PostgreSQL."
    Write-Host "  1. Create .env with: DATABASE_URL=postgresql://user:pass@host:5432/db" -ForegroundColor Yellow
    Write-Host "  2. Or: `$env:DATABASE_URL=`"postgresql://...`"; .\deploy-cloud-run.ps1" -ForegroundColor Yellow
    Write-Host "  Free PostgreSQL: Supabase, Neon, Railway. Or use Google Cloud SQL." -ForegroundColor Gray
    exit 1
}

# Step 8: Deploy to Cloud Run
Write-Step "Step 8: Deploying to Cloud Run..."
Write-Host "  This may take 2-3 minutes..." -ForegroundColor Yellow

$ENV_VARS = "PORT=8080,SESSION_SECRET=$SESSION_SECRET,SESSION_COOKIE_SECURE=true,DATABASE_URL=$DATABASE_URL"

$CLOUD_SQL = $env:CLOUD_SQL_INSTANCE
$deployArgs = @(
    "run", "deploy", "travel-inbound",
    "--image", $IMAGE_TAG,
    "--platform", "managed",
    "--region", "us-central1",
    "--allow-unauthenticated",
    "--memory", "2Gi",
    "--cpu", "2",
    "--timeout", "300",
    "--max-instances", "10",
    "--min-instances", "0",
    "--set-env-vars", $ENV_VARS
)
if ($CLOUD_SQL) {
    $deployArgs += "--add-cloudsql-instances"
    $deployArgs += $CLOUD_SQL
    Write-Success "Cloud SQL instance: $CLOUD_SQL"
}
gcloud @deployArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Cloud Run deployment failed!"
    exit 1
}
Write-Success "Deployment successful!"

# Step 9: Get service URL
Write-Step "Step 9: Getting service URL..."
$SERVICE_URL = gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)' 2>$null

if ($SERVICE_URL) {
    Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║           Deployment Complete Successfully!               ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
    
    Write-Host "Service URL: " -NoNewline
    Write-Host $SERVICE_URL -ForegroundColor Cyan
    Write-Host "`nVerifying production health..." -ForegroundColor Cyan
    & "$PSScriptRoot\verify-production.ps1" -Url $SERVICE_URL
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nYour application is live and configured for persistent data." -ForegroundColor Green
    }
    Write-Host "`nUseful commands:" -ForegroundColor Yellow
    Write-Host "  View logs: gcloud run services logs read travel-inbound --region us-central1" -ForegroundColor White
    Write-Host "  Verify: .\verify-production.ps1" -ForegroundColor White
    Write-Host "  Update: gcloud run services update travel-inbound --region us-central1" -ForegroundColor White
} else {
    Write-Warning "Could not retrieve service URL. Check Cloud Console."
}

Write-Host "`n"
