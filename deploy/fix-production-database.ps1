# Add DATABASE_URL to existing Cloud Run deployment (quick fix for data not persisting)
# Use when production was deployed without DATABASE_URL
# Usage: .\fix-production-database.ps1
#        $env:DATABASE_URL="postgresql://..."; .\fix-production-database.ps1

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
}

$DATABASE_URL = $env:DATABASE_URL
if (-not $DATABASE_URL -or $DATABASE_URL -notmatch '^postgres') {
    Write-Host "DATABASE_URL (PostgreSQL) is required." -ForegroundColor Red
    Write-Host "Set in .env or: `$env:DATABASE_URL=`"postgresql://user:pass@host:5432/db`"" -ForegroundColor Yellow
    exit 1
}

Write-Host "Updating Cloud Run service with DATABASE_URL..." -ForegroundColor Cyan
$args = @(
    "run", "services", "update", "travel-inbound",
    "--region", "us-central1",
    "--update-env-vars", "DATABASE_URL=$DATABASE_URL"
)

$CLOUD_SQL = $env:CLOUD_SQL_INSTANCE
if ($CLOUD_SQL) {
    $args += "--add-cloudsql-instances"
    $args += $CLOUD_SQL
    Write-Host "Adding Cloud SQL instance: $CLOUD_SQL" -ForegroundColor Gray
}

gcloud @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "Update failed." -ForegroundColor Red
    exit 1
}

Write-Host "`nDone. Verifying..." -ForegroundColor Green
& "$PSScriptRoot\verify-production.ps1"
