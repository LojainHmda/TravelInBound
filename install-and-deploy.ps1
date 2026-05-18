# Install Google Cloud SDK and deploy Travel Inbound to Cloud Run
# Run this script - you may need to approve UAC and sign in to Google in browser

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

function Find-Gcloud {
    $paths = @(
        "$env:ProgramFiles\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        "${env:ProgramFiles(x86)}\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    $cmd = Get-Command gcloud -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

Write-Host "`n=== Travel Inbound - Install and Deploy to Cloud Run ===`n" -ForegroundColor Cyan

# Refresh PATH so we find gcloud if recently installed
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Step 1: Install gcloud if needed
$gcloud = Find-Gcloud
if (-not $gcloud) {
    Write-Host "[1/5] Installing Google Cloud SDK via winget..." -ForegroundColor Yellow
    Write-Host "      (A UAC prompt may appear - click Yes)" -ForegroundColor Gray
    winget install Google.CloudSDK --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
    $gcloud = Find-Gcloud
    if (-not $gcloud) {
        Write-Host "[ERROR] gcloud not found. Restart terminal and run again, or install from cloud.google.com/sdk" -ForegroundColor Red
        exit 1
    }
    # Refresh PATH for current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    $gcloud = Find-Gcloud
    if (-not $gcloud) {
        Write-Host "[!] Restart your terminal and run this script again." -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "[OK] gcloud found: $gcloud" -ForegroundColor Green

# Step 2: Auth
Write-Host "`n[2/5] Checking authentication..." -ForegroundColor Yellow
$account = & $gcloud config get-value account 2>$null
if (-not $account) {
    Write-Host "      Opening browser for sign-in..." -ForegroundColor Gray
    & $gcloud auth login
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Write-Host "[OK] Logged in" -ForegroundColor Green

# Step 3: Project
Write-Host "`n[3/5] Checking project..." -ForegroundColor Yellow
$proj = & $gcloud config get-value project 2>$null
if (-not $proj) {
    $proj = Read-Host "Enter your GCP Project ID (or create one at console.cloud.google.com)"
    if ($proj) {
        & $gcloud config set project $proj
    } else {
        Write-Host "[ERROR] Project required. Run: gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Red
        exit 1
    }
}
Write-Host "[OK] Project: $proj" -ForegroundColor Green

# Step 4: Enable APIs (skip if permission denied - APIs may already be enabled)
Write-Host "`n[4/5] Enabling APIs..." -ForegroundColor Yellow
$prevErr = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
@("run.googleapis.com", "containerregistry.googleapis.com", "cloudbuild.googleapis.com") | ForEach-Object {
    & $gcloud services enable $_ --quiet 2>&1 | Out-Null
}
$ErrorActionPreference = $prevErr
Write-Host "[OK] APIs ready" -ForegroundColor Green

# Step 5: Deploy
Write-Host "`n[5/5] Deploying via Cloud Build (5-10 min)..." -ForegroundColor Yellow
& $gcloud builds submit --config cloudbuild.yaml . --project $proj

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Deployment failed!" -ForegroundColor Red
    exit 1
}

$url = & $gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)' 2>$null
Write-Host "`n=== Deployment complete! ===" -ForegroundColor Green
Write-Host "Service URL: $url" -ForegroundColor Cyan
Write-Host "`n"
