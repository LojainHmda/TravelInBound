# Run this as a project OWNER (e.g. marei.eyad@gmail.com or eyad_a_m@hotmail.com)
# Adds permissions so lojainhmda@gmail.com can deploy

$gcloud = "C:\Users\lojai\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$project = "kartacagenai"
$user = "lojainhmda@gmail.com"

Write-Host "Adding Service Usage Consumer to $user..." -ForegroundColor Cyan
& $gcloud projects add-iam-policy-binding $project --member="user:$user" --role="roles/serviceusage.serviceUsageConsumer" --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Done. Now run: .\install-and-deploy.ps1" -ForegroundColor Green
} else {
    Write-Host "Failed. Ensure you're logged in as project Owner." -ForegroundColor Red
}
