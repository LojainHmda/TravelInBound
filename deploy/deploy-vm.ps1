# Google Compute Engine VM Deployment Script

param(
    [string]$ProjectId = "",
    [string]$Zone = "us-central1-a",
    [string]$VmName = "travel-inbound-vm",
    [string]$MachineType = "e2-medium",
    [string]$DiskSize = "20GB"
)

$ErrorActionPreference = "Stop"

function Write-Step($message) { Write-Host "`n>>> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "✓ $message" -ForegroundColor Green }
function Write-Error($message) { Write-Host "✗ $message" -ForegroundColor Red }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Travel Inbound - VM Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get project ID
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        Write-Error "No GCP project set. Please set it:"
        Write-Host "  gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
        exit 1
    }
}

Write-Step "Project: $ProjectId"
Write-Step "Zone: $Zone"
Write-Step "VM Name: $VmName"

# Enable APIs
Write-Step "Enabling required APIs..."
gcloud services enable compute.googleapis.com --project=$ProjectId --quiet

# Create startup script
Write-Step "Creating startup script..."
$startupScript = @"
#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git nginx supervisor

# Create app directory
mkdir -p /opt/travel-inbound
cd /opt/travel-inbound

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Set up Nginx
cat > /etc/nginx/sites-available/travel-inbound << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/travel-inbound /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Set up Supervisor
cat > /etc/supervisor/conf.d/travel-inbound.conf << 'SUPERVISOR_EOF'
[program:travel-inbound]
command=/opt/travel-inbound/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 main:app
directory=/opt/travel-inbound
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/travel-inbound.err.log
stdout_logfile=/var/log/travel-inbound.out.log
SUPERVISOR_EOF

supervisorctl reread
supervisorctl update
"@

$startupScript | Out-File -FilePath "$env:TEMP\vm-startup.sh" -Encoding utf8

# Create VM
Write-Step "Creating VM instance..."
gcloud compute instances create $VmName `
    --project=$ProjectId `
    --zone=$Zone `
    --machine-type=$MachineType `
    --boot-disk-size=$DiskSize `
    --image-family=ubuntu-2204-lts `
    --image-project=ubuntu-os-cloud `
    --metadata-from-file startup-script="$env:TEMP\vm-startup.sh" `
    --tags=http-server,https-server `
    --scopes=cloud-platform

if ($LASTEXITCODE -ne 0) {
    Write-Error "VM creation failed!"
    exit 1
}

Write-Success "VM created successfully!"

# Get VM IP
Write-Step "Getting VM IP address..."
$vmIp = gcloud compute instances describe $VmName --zone=$Zone --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  VM Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nVM Name: $VmName" -ForegroundColor Cyan
Write-Host "Zone: $Zone" -ForegroundColor Cyan
Write-Host "IP Address: $vmIp" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. SSH into VM: gcloud compute ssh $VmName --zone=$Zone" -ForegroundColor White
Write-Host "  2. Upload your application code" -ForegroundColor White
Write-Host "  3. Install dependencies and configure" -ForegroundColor White
Write-Host "  4. Set up firewall rules if needed`n" -ForegroundColor White
