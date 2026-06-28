# Google Cloud Run Deployment Script
# This script handles the complete deployment process
# REQUIRES: DATABASE_URL (PostgreSQL) - set in .env or -DatabaseUrl

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "travel-inbound",
    [switch]$SkipBuild = $false,
    [switch]$SkipPush = $false,
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$CloudSqlInstance = $env:CLOUD_SQL_INSTANCE,
    [string]$SessionSecret = ""
)

$ErrorActionPreference = "Stop"

# Load .env if present
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "env:$key" -Value $val -Force
        }
    }
    if (-not $DatabaseUrl) { $DatabaseUrl = $env:DATABASE_URL }
    if (-not $CloudSqlInstance) { $CloudSqlInstance = $env:CLOUD_SQL_INSTANCE }
}

# Colors
function Write-Step($message) { Write-Host "`n>>> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Write-Error($message) { Write-Host "[X] $message" -ForegroundColor Red }
function Write-Warning($message) { Write-Host "[!] $message" -ForegroundColor Yellow }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Travel Inbound - Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Get or set project ID
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Error "No GCP project set. Please set it:"
        Write-Host "  gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
        Write-Host "  OR use: .\deploy.ps1 -ProjectId YOUR_PROJECT_ID" -ForegroundColor Yellow
        exit 1
    }
}

Write-Step "Using Project: $ProjectId"
Write-Step "Region: $Region"
Write-Step "Service: $ServiceName"

# Step 2: Verify prerequisites
Write-Step "Checking prerequisites..."

# Check Docker
try {
    $dockerVersion = docker --version 2>$null
    Write-Success "Docker found: $dockerVersion"
} catch {
    Write-Error "Docker not found. Please install Docker Desktop."
    exit 1
}

# Check gcloud
try {
    $gcloudVersion = gcloud --version 2>$null | Select-Object -First 1
    Write-Success "gcloud CLI found"
} catch {
    Write-Error "gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
}

# Check if logged in
$currentAccount = gcloud config get-value account 2>$null
if (-not $currentAccount) {
    Write-Warning "Not logged in to gcloud. Attempting login..."
    gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to login. Please run: gcloud auth login"
        exit 1
    }
}

Write-Success "Logged in as: $currentAccount"

# Step 3: Enable required APIs
Write-Step "Enabling required Google Cloud APIs..."
$apis = @(
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "sqladmin.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Checking $api..." -NoNewline
    $enabled = gcloud services list --enabled --filter="name:$api" --format="value(name)" 2>$null
    if (-not $enabled) {
        gcloud services enable $api --quiet 2>$null
        Write-Success " Enabled"
    } else {
        Write-Success " Already enabled"
    }
}

# Step 4: Build Docker image
if (-not $SkipBuild) {
    Write-Step "Building Docker image..."
    $imageTag = "gcr.io/$ProjectId/$ServiceName:latest"
    
    docker build -t $imageTag .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed!"
        exit 1
    }
    Write-Success "Docker image built successfully: $imageTag"
} else {
    Write-Warning 'Skipping Docker build (because -SkipBuild was specified)'
}

# Step 5: Push to Container Registry
if (-not $SkipPush) {
    Write-Step "Pushing image to Container Registry..."
    $imageTag = "gcr.io/$ProjectId/$ServiceName:latest"
    
    docker push $imageTag
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker push failed!"
        exit 1
    }
    Write-Success "Image pushed successfully"
} else {
    Write-Warning 'Skipping Docker push (because -SkipPush was specified)'
}

# Step 6: Prepare environment variables
Write-Step "Preparing environment variables..."

$envVars = @("PORT=8080")

# Generate session secret if not provided
if (-not $SessionSecret) {
    $SessionSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    Write-Warning "Generated new SESSION_SECRET (save this for future deployments!)"
    Write-Host "  SESSION_SECRET: $SessionSecret" -ForegroundColor Gray
}

$envVars += "SESSION_SECRET=$SessionSecret"
$envVars += "SESSION_COOKIE_SECURE=true"

# Database URL REQUIRED for production
if ($DatabaseUrl -and $DatabaseUrl -match '^postgres') {
    $envVars += "DATABASE_URL=$DatabaseUrl"
    Write-Success "PostgreSQL DATABASE_URL configured"
} else {
    Write-Error "DATABASE_URL (PostgreSQL) is REQUIRED. Data will NOT persist without it."
    Write-Host "  Set in .env: DATABASE_URL=postgresql://user:pass@host:5432/db" -ForegroundColor Yellow
    Write-Host "  Or: .\deploy.ps1 -DatabaseUrl `"postgresql://...`"" -ForegroundColor Yellow
    exit 1
}

$envVarsString = $envVars -join ","

# Step 7: Deploy to Cloud Run
Write-Step "Deploying to Cloud Run..."

$deployArgs = @(
    "run", "deploy", $ServiceName,
    "--image", "gcr.io/$ProjectId/$ServiceName:latest",
    "--platform", "managed",
    "--region", $Region,
    "--allow-unauthenticated",
    "--memory", "2Gi",
    "--cpu", "2",
    "--timeout", "300",
    "--max-instances", "10",
    "--min-instances", "0",
    "--set-env-vars", $envVarsString
)
if ($CloudSqlInstance) {
    $deployArgs += "--add-cloudsql-instances"
    $deployArgs += $CloudSqlInstance
    Write-Success "Cloud SQL instance: $CloudSqlInstance"
}

gcloud @deployArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cloud Run deployment failed!"
    exit 1
}

Write-Success "Deployment successful!"

# Step 8: Get service URL
Write-Step "Getting service URL..."
$serviceUrl = gcloud run services describe $ServiceName --region $Region --format 'value(status.url)' 2>$null

if ($serviceUrl) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  Deployment Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nService URL: " -NoNewline
    Write-Host $serviceUrl -ForegroundColor Cyan
    Write-Host "`nVerifying production health..." -ForegroundColor Cyan
    & "$PSScriptRoot\verify-production.ps1" -Url $serviceUrl
    Write-Host "`nView logs: gcloud run services logs read $ServiceName --region $Region" -ForegroundColor Gray
} else {
    Write-Warning "Could not retrieve service URL. Check Cloud Console."
}

Write-Host ""
