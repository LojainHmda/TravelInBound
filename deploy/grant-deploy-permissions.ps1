# Run this as a project OWNER (e.g. marei.eyad@gmail.com or eyad_a_m@hotmail.com)
# Adds permissions so lojainhmda@gmail.com can deploy

$gcloud = "C:\Users\lojai\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$project = "kartacagenai"
$user = "lojainhmda@gmail.com"

$roles = @(
    "roles/serviceusage.serviceUsageConsumer",
    "roles/cloudbuild.builds.editor",
    "roles/storage.admin",
    "roles/run.admin",
    "roles/iam.serviceAccountUser"
)

$failed = $false
foreach ($role in $roles) {
    Write-Host "Adding $role to $user..." -ForegroundColor Cyan
    & $gcloud projects add-iam-policy-binding $project --member="user:$user" --role=$role --quiet
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
    Write-Host "[OK] Done. Deploy with: .\deploy-cloudbuild.ps1 -ProjectId kartacagenai" -ForegroundColor Green
} else {
    Write-Host "Failed. Ensure you're logged in as project Owner on kartacagenai." -ForegroundColor Red
}
