#!/bin/bash
# Google Compute Engine VM Deployment Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
PROJECT_ID=""
ZONE="us-central1-a"
VM_NAME="travel-inbound-vm"
MACHINE_TYPE="e2-medium"
DISK_SIZE="20GB"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --zone)
            ZONE="$2"
            shift 2
            ;;
        --vm-name)
            VM_NAME="$2"
            shift 2
            ;;
        --machine-type)
            MACHINE_TYPE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Travel Inbound - VM Deployment${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Get project ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}✗ No GCP project set.${NC}"
        echo -e "${YELLOW}  Set it with: gcloud config set project YOUR_PROJECT_ID${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}>>> Project: ${PROJECT_ID}${NC}"
echo -e "${CYAN}>>> Zone: ${ZONE}${NC}"
echo -e "${CYAN}>>> VM Name: ${VM_NAME}${NC}\n"

# Enable APIs
echo -e "${CYAN}>>> Enabling required APIs...${NC}"
gcloud services enable compute.googleapis.com --project="$PROJECT_ID" --quiet

# Create startup script
echo -e "${CYAN}>>> Creating startup script...${NC}"
cat > /tmp/vm-startup.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git nginx supervisor

# Create app directory
mkdir -p /opt/travel-inbound
cd /opt/travel-inbound

# Clone or copy application (you'll need to upload your code)
# For now, we'll set up the environment

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies (when code is available)
# pip install -r requirements.txt

# Set up Nginx
cat > /etc/nginx/sites-available/travel-inbound << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
EOF

# Create VM
echo -e "${CYAN}>>> Creating VM instance...${NC}"
gcloud compute instances create "$VM_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --boot-disk-size="$DISK_SIZE" \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --metadata-from-file startup-script=/tmp/vm-startup.sh \
    --tags=http-server,https-server \
    --scopes=cloud-platform

echo -e "${GREEN}✓ VM created successfully!${NC}"

# Get VM IP
echo -e "\n${CYAN}>>> Getting VM IP address...${NC}"
VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  VM Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "VM Name: ${CYAN}${VM_NAME}${NC}"
echo -e "Zone: ${CYAN}${ZONE}${NC}"
echo -e "IP Address: ${CYAN}${VM_IP}${NC}\n"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. SSH into VM: ${CYAN}gcloud compute ssh ${VM_NAME} --zone=${ZONE}${NC}"
echo -e "  2. Upload your application code"
echo -e "  3. Install dependencies and configure"
echo -e "  4. Set up firewall rules if needed\n"
