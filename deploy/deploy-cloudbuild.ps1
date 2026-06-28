# Deploy via Google Cloud Build (no Docker required locally)
# Builds in the cloud and deploys to Cloud Run
# REQUIRES: DATABASE_URL (PostgreSQL) - set in .env or -DatabaseUrl

param(
    [string]$ProjectId = "kartacagenai",
    [string]$GcpAccount = "lojainhmda@gmail.com",
    [string]$Region = "us-central1",
    [string]$ServiceName = "travel-inbound",
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$CloudSqlInstance = $env:CLOUD_SQL_INSTANCE
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
if (-not (Test-Path "cloudbuild.yaml")) {
    Write-Err "cloudbuild.yaml not found"
    exit 1
}
Write-Success "cloudbuild.yaml found"

# Enable APIs
Write-Step "Enabling required APIs..."
$apis = @("run.googleapis.com", "containerregistry.googleapis.com", "cloudbuild.googleapis.com")
foreach ($api in $apis) {
    Invoke-GcloudQuiet services enable $api --quiet | Out-Null
}
Write-Success "APIs enabled"

# Database URL (PostgreSQL REQUIRED for production)
if (-not $DatabaseUrl -or $DatabaseUrl -notmatch '^postgres') {
    Write-Host "`nPostgreSQL DATABASE_URL is REQUIRED for persistent data." -ForegroundColor Cyan
    Write-Host "Set in .env or enter now. Examples: Supabase, Neon, Railway, Cloud SQL" -ForegroundColor Gray
    $DatabaseUrl = Read-Host "Enter PostgreSQL URL (postgresql://user:password@host:5432/database)"
    $DatabaseUrl = $DatabaseUrl.Trim()
    if (-not $DatabaseUrl -or $DatabaseUrl -notmatch '^postgres') {
        Write-Err "DATABASE_URL (postgresql://...) is required. Deployment cancelled."
        exit 1
    }
}
Write-Success "PostgreSQL DATABASE_URL configured"

# Submit build with substitutions
Write-Step "Submitting build to Cloud Build (builds in cloud, ~5-10 min)..."

$subs = @()
if ($DatabaseUrl) {
    $subs += "_DATABASE_URL=$DatabaseUrl"
}
if ($CloudSqlInstance) {
    $subs += "_CLOUD_SQL_INSTANCE=$CloudSqlInstance"
}

if ($subs.Count -gt 0) {
    $subsStr = $subs -join ","
    Write-Host "  Passing: $($subs -join ', ')" -ForegroundColor Gray
    gcloud builds submit --config cloudbuild.yaml . --project $PROJECT_ID --substitutions="$subsStr"
} else {
    gcloud builds submit --config cloudbuild.yaml . --project $PROJECT_ID
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
