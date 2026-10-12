# Deploy via Google Cloud Build (no Docker required locally)
# Builds in the cloud and deploys to Cloud Run
# REQUIRES: DATABASE_URL_LIVE (PostgreSQL) in .env, or -DatabaseUrl
# (an older .env with DATABASE_URL still works)

param(
    [string]$ProjectId = "kartacagenai",
    [string]$GcpAccount = "lojainhmda@gmail.com",
    [string]$Region = "us-central1",
    [string]$ServiceName = "travel-inbound",
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$CloudSqlInstance = $env:CLOUD_SQL_INSTANCE,
    # The live site's Neon database. Deploying any other one needs -AllowOtherDatabase.
    [string]$ProductionDbEndpoint = "ep-fancy-hill-b5rwffyj",
    [switch]$AllowOtherDatabase
)

$ErrorActionPreference = "Stop"

# This script builds with the repository root as the Docker context. Running it
# from deploy/ would upload only that folder and the image would have no app.
if (-not (Test-Path "app/__init__.py") -or -not (Test-Path "deploy/cloudbuild.yaml")) {
    Write-Host "[ERROR] Run this from the repository root: .\deploy\deploy-cloudbuild.ps1" -ForegroundColor Red
    exit 1
}

# Load .env if present
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "env:$key" -Value $val -Force
        }
    }
    if (-not $DatabaseUrl) { $DatabaseUrl = $env:DATABASE_URL_LIVE }
    if (-not $DatabaseUrl) { $DatabaseUrl = $env:DATABASE_URL }
    if (-not $CloudSqlInstance) { $CloudSqlInstance = $env:CLOUD_SQL_INSTANCE }
}
# The local database, which must never be deployed as live
$LocalDatabaseUrl = $env:DATABASE_URL_LOCAL
if (-not $LocalDatabaseUrl) { $LocalDatabaseUrl = $env:DATABASE_URL_TEST }

function Write-Step($message) { Write-Host "`n>>> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Write-Err($message) { Write-Host "[ERROR] $message" -ForegroundColor Red }
function Write-Warning($message) { Write-Host "[!] $message" -ForegroundColor Yellow }

function Invoke-GcloudQuiet {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & gcloud @Args 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    return $code
}

Write-Host "`n=== Travel Inbound - Cloud Build Deployment ===" -ForegroundColor Cyan
Write-Host "(No Docker needed - builds in Google Cloud)`n" -ForegroundColor Cyan

# Check gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Err "gcloud CLI not found."
    Write-Host "`nInstall from: https://cloud.google.com/sdk/docs/install-windows" -ForegroundColor Yellow
    Write-Host "Quick install:" -ForegroundColor Yellow
    Write-Host '  (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")' -ForegroundColor White
    Write-Host '  & $env:Temp\GoogleCloudSDKInstaller.exe' -ForegroundColor White
    exit 1
}
Write-Success "gcloud CLI found"

# Target project (production: kartacagenai -> travel-inbound-d5jj5uif3a-uc.a.run.app)
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
}
if (-not $ProjectId) {
    Write-Err "No GCP project set. Use -ProjectId kartacagenai or: gcloud config set project kartacagenai"
    exit 1
}
if ($GcpAccount) {
    Invoke-GcloudQuiet config set account $GcpAccount | Out-Null
}
Invoke-GcloudQuiet config set project $ProjectId | Out-Null
$PROJECT_ID = $ProjectId
Write-Success "Project: $PROJECT_ID (region: $Region, service: $ServiceName)"

# Check auth
$ACCOUNT = gcloud config get-value account 2>$null
if (-not $ACCOUNT) {
    Write-Warning "Not logged in. Opening browser..."
    gcloud auth login
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Write-Success "Logged in as: $ACCOUNT"

# Check files
if (-not (Test-Path "deploy/cloudbuild.yaml")) {
    Write-Err "deploy/cloudbuild.yaml not found"
    exit 1
}
Write-Success "deploy/cloudbuild.yaml found"

# Enable APIs
Write-Step "Enabling required APIs..."
$apis = @("run.googleapis.com", "containerregistry.googleapis.com", "cloudbuild.googleapis.com")
foreach ($api in $apis) {
    Invoke-GcloudQuiet services enable $api --quiet | Out-Null
}
Write-Success "APIs enabled"

# Database URL (PostgreSQL REQUIRED for production)
if (-not $DatabaseUrl -or $DatabaseUrl -notmatch '^postgres') {
    Write-Host "`nThe live database URL is REQUIRED (DATABASE_URL_LIVE in .env)." -ForegroundColor Cyan
    Write-Host "Set it in .env or enter it now." -ForegroundColor Gray
    $DatabaseUrl = Read-Host "Enter PostgreSQL URL (postgresql://user:password@host:5432/database)"
    $DatabaseUrl = $DatabaseUrl.Trim()
    if (-not $DatabaseUrl -or $DatabaseUrl -notmatch '^postgres') {
        Write-Err "DATABASE_URL_LIVE (postgresql://...) is required. Deployment cancelled."
        exit 1
    }
}
if ($LocalDatabaseUrl -and $DatabaseUrl -eq $LocalDatabaseUrl) {
    Write-Err "This is the local database (DATABASE_URL_LOCAL). The live site must use DATABASE_URL_LIVE. Deployment cancelled."
    exit 1
}
try {
    $dbHost = ([System.Uri]$DatabaseUrl).Host
} catch {
    Write-Err "DATABASE_URL_LIVE is not a valid URL. Deployment cancelled."
    exit 1
}
if (-not $AllowOtherDatabase -and -not $dbHost.StartsWith($ProductionDbEndpoint)) {
    Write-Err "DATABASE_URL_LIVE points at $dbHost, not the live database ($ProductionDbEndpoint). Deployment cancelled."
    Write-Host "  If the live database has really moved, rerun with -AllowOtherDatabase." -ForegroundColor Yellow
    exit 1
}
Write-Success "Live database: $dbHost"

# Submit build with substitutions
Write-Step "Submitting build to Cloud Build (builds in cloud, ~5-10 min)..."

$subs = @()
if ($DatabaseUrl) {
    # Base64: the "&" in Neon URLs would cut the command short in gcloud's Windows launcher
    $subs += "_DATABASE_URL_B64=" + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DatabaseUrl))
}
if ($CloudSqlInstance) {
    $subs += "_CLOUD_SQL_INSTANCE=$CloudSqlInstance"
}

if ($subs.Count -gt 0) {
    $subsStr = $subs -join ","
    # Names only: the values hold the database password
    Write-Host "  Passing: $(($subs | ForEach-Object { $_.Split('=')[0] }) -join ', ')" -ForegroundColor Gray
    gcloud builds submit --config deploy/cloudbuild.yaml . --project $PROJECT_ID --substitutions="$subsStr"
} else {
    gcloud builds submit --config deploy/cloudbuild.yaml . --project $PROJECT_ID
}

if ($LASTEXITCODE -ne 0) {
    Write-Err "Deployment failed!"
    exit 1
}

Write-Success "Deployment complete!"

# Get URL and verify
$SERVICE_URL = gcloud run services describe $ServiceName --project $PROJECT_ID --region $Region --format 'value(status.url)' 2>$null
if ($SERVICE_URL) {
    Write-Host "`n=== Deployment Complete Successfully! ===`n" -ForegroundColor Green
    Write-Host "Service URL: " -NoNewline
    Write-Host $SERVICE_URL -ForegroundColor Cyan
    Write-Host "`nVerifying production health..." -ForegroundColor Cyan
    & "$PSScriptRoot\verify-production.ps1" -Url $SERVICE_URL
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nDatabase: PostgreSQL (persistent)" -ForegroundColor Green
    }
}

Write-Host ""
