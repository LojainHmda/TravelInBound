# Verify production deployment - check /health endpoint
# Usage: .\verify-production.ps1
#        .\verify-production.ps1 -Url "https://your-service.run.app"

param(
    [string]$Url = ""
)

if (-not $Url) {
    $Url = gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)' 2>$null
    if (-not $Url) {
        Write-Host "Could not get service URL. Run: .\verify-production.ps1 -Url https://your-service.run.app" -ForegroundColor Red
        exit 1
    }
}

$healthUrl = $Url.TrimEnd('/') + "/health"
Write-Host "`nChecking: $healthUrl" -ForegroundColor Cyan

try {
    $r = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 15
    Write-Host "`n=== Health Check Result ===" -ForegroundColor Green
    Write-Host "Status: $($r.status)" -ForegroundColor $(if ($r.status -eq "ok") { "Green" } else { "Yellow" })
    Write-Host "Database type: $($r.database_type)" -ForegroundColor White
    Write-Host "DATABASE_URL set: $($r.database_url_set)" -ForegroundColor $(if ($r.database_url_set) { "Green" } else { "Red" })
    Write-Host "DB connected: $($r.db_connected)" -ForegroundColor $(if ($r.db_connected) { "Green" } else { "Red" })
    Write-Host "Schema OK: $($r.schema_ok)" -ForegroundColor $(if ($r.schema_ok) { "Green" } else { "Red" })
    if ($r.errors -and $r.errors.Count -gt 0) {
        Write-Host "`nErrors:" -ForegroundColor Red
        $r.errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        exit 1
    }
    if ($r.schema_ok -and $r.db_connected -and $r.database_url_set) {
        Write-Host "`nProduction is configured correctly. Data will persist." -ForegroundColor Green
    } else {
        Write-Host "`nWARNING: Issues detected. Data may not persist." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "`nFailed to reach /health: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""
