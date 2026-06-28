#!/bin/bash
# Ubuntu VM Deployment Script for Travel Inbound
# Optimized for Ubuntu 22.04 LTS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
PROJECT_ID=""
ZONE="us-central1-a"
VM_NAME="travel-inbound-ubuntu"
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
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--project-id PROJECT] [--zone ZONE] [--vm-name NAME] [--machine-type TYPE]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Travel Inbound - Ubuntu VM Deployment Script        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Step 1: Get or set project ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}✗ No GCP project set.${NC}"
        echo -e "${YELLOW}  Set it with: gcloud config set project YOUR_PROJECT_ID${NC}"
        echo -e "${YELLOW}  OR use: $0 --project-id YOUR_PROJECT_ID${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Configuration:${NC}"
echo -e "  Project ID: ${GREEN}${PROJECT_ID}${NC}"
echo -e "  Zone: ${GREEN}${ZONE}${NC}"
echo -e "  VM Name: ${GREEN}${VM_NAME}${NC}"
echo -e "  Machine Type: ${GREEN}${MACHINE_TYPE}${NC}"
echo -e "  Image: ${GREEN}${IMAGE_FAMILY}${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}\n"

# Step 2: Verify prerequisites
echo -e "${CYAN}>>> Step 1: Checking prerequisites...${NC}"

# Check Docker (optional, for local testing)
if command -v docker &> /dev/null; then
    echo -e "${GREEN}  ✓ Docker found${NC}"
else
    echo -e "${YELLOW}  ⚠ Docker not found (optional for local testing)${NC}"
fi

# Check gcloud
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud --version | head -n 1)
    echo -e "${GREEN}  ✓ gcloud CLI found: ${GCLOUD_VERSION}${NC}"
else
    echo -e "${RED}  ✗ gcloud CLI not found${NC}"
    echo -e "${YELLOW}    Install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check if logged in
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$CURRENT_ACCOUNT" ]; then
    echo -e "${YELLOW}  ⚠ Not logged in to gcloud. Attempting login...${NC}"
    gcloud auth login
    if [ $? -ne 0 ]; then
        echo -e "${RED}  ✗ Failed to login${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ Logged in as: ${CURRENT_ACCOUNT}${NC}"
fi

# Step 3: Enable required APIs
echo -e "\n${CYAN}>>> Step 2: Enabling required Google Cloud APIs...${NC}"
APIS=(
    "compute.googleapis.com"
    "sqladmin.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -n "  Checking $api... "
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" 2>/dev/null | grep -q "$api"; then
        echo -e "${GREEN}Already enabled${NC}"
    else
        gcloud services enable "$api" --project="$PROJECT_ID" --quiet 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Enabled${NC}"
        else
            echo -e "${RED}Failed${NC}"
        fi
    fi
done

# Step 4: Create comprehensive startup script
echo -e "\n${CYAN}>>> Step 3: Creating Ubuntu startup script...${NC}"

STARTUP_SCRIPT=$(cat << 'EOF'
#!/bin/bash
# Travel Inbound - Ubuntu VM Startup Script
set -e

exec > /var/log/travel-inbound-startup.log 2>&1

echo "=========================================="
echo "Travel Inbound - VM Startup Script"
echo "Started at: $(date)"
echo "=========================================="

# Update system
echo "[1/8] Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# Install system dependencies
echo "[2/8] Installing system dependencies..."
apt-get install -y -qq \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    nginx \
    supervisor \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    build-essential \
    curl \
    wget \
    unzip \
    poppler-utils \
    wkhtmltopdf \
    xvfb \
    libjpeg-dev \
    zlib1g-dev

# Create application directory
echo "[3/8] Setting up application directory..."
mkdir -p /opt/travel-inbound
cd /opt/travel-inbound
chown -R www-data:www-data /opt/travel-inbound

# Create virtual environment
echo "[4/8] Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Set up PostgreSQL
echo "[5/8] Configuring PostgreSQL..."
sudo -u postgres psql << PSQL_EOF
CREATE DATABASE travel_inbound;
CREATE USER travel_user WITH PASSWORD 'change_this_password_in_production';
ALTER ROLE travel_user SET client_encoding TO 'utf8';
ALTER ROLE travel_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE travel_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE travel_inbound TO travel_user;
\q
PSQL_EOF

# Configure Nginx
echo "[6/8] Configuring Nginx..."
cat > /etc/nginx/sites-available/travel-inbound << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static {
        alias /opt/travel-inbound/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/travel-inbound /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

# Configure Supervisor
echo "[7/8] Configuring Supervisor..."
cat > /etc/supervisor/conf.d/travel-inbound.conf << 'SUPERVISOR_EOF'
[program:travel-inbound]
command=/opt/travel-inbound/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - main:app
directory=/opt/travel-inbound
user=www-data
autostart=true
autorestart=true
autorestart_delay=5
stopwaitsecs=30
stderr_logfile=/var/log/travel-inbound.err.log
stdout_logfile=/var/log/travel-inbound.out.log
stderr_logfile_maxbytes=10MB
stdout_logfile_maxbytes=10MB
environment=PYTHONUNBUFFERED=1
SUPERVISOR_EOF

supervisorctl reread
supervisorctl update
supervisorctl start travel-inbound || true

# Create deployment helper script
echo "[8/8] Creating deployment helper script..."
cat > /opt/travel-inbound/deploy-app.sh << 'DEPLOY_EOF'
#!/bin/bash
# Helper script to deploy/update application
set -e

cd /opt/travel-inbound
source venv/bin/activate

echo "Installing/updating dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

echo "Restarting application..."
supervisorctl restart travel-inbound

echo "Deployment complete!"
DEPLOY_EOF

chmod +x /opt/travel-inbound/deploy-app.sh

# Set permissions
chown -R www-data:www-data /opt/travel-inbound

echo "=========================================="
echo "Startup script completed at: $(date)"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH into VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "2. Upload application code to /opt/travel-inbound"
echo "3. Run: cd /opt/travel-inbound && source venv/bin/activate"
echo "4. Install dependencies: pip install -r requirements.txt"
echo "5. Initialize database: python init_db.py"
echo "6. Restart: supervisorctl restart travel-inbound"
EOF
)

# Save startup script to temp file
TEMP_SCRIPT=$(mktemp)
echo "$STARTUP_SCRIPT" > "$TEMP_SCRIPT"
chmod +x "$TEMP_SCRIPT"

echo -e "${GREEN}  ✓ Startup script created${NC}"

# Step 5: Create firewall rules
echo -e "\n${CYAN}>>> Step 4: Configuring firewall rules...${NC}"

# Check if firewall rules exist
if ! gcloud compute firewall-rules describe allow-http --project="$PROJECT_ID" &>/dev/null; then
    echo -n "  Creating HTTP firewall rule... "
    gcloud compute firewall-rules create allow-http \
        --project="$PROJECT_ID" \
        --allow tcp:80 \
        --source-ranges 0.0.0.0/0 \
        --target-tags http-server \
        --description "Allow HTTP traffic" \
        --quiet 2>/dev/null
    echo -e "${GREEN}Created${NC}"
else
    echo -e "${GREEN}  ✓ HTTP firewall rule already exists${NC}"
fi

if ! gcloud compute firewall-rules describe allow-https --project="$PROJECT_ID" &>/dev/null; then
    echo -n "  Creating HTTPS firewall rule... "
    gcloud compute firewall-rules create allow-https \
        --project="$PROJECT_ID" \
        --allow tcp:443 \
        --source-ranges 0.0.0.0/0 \
        --target-tags https-server \
        --description "Allow HTTPS traffic" \
        --quiet 2>/dev/null
    echo -e "${GREEN}Created${NC}"
else
    echo -e "${GREEN}  ✓ HTTPS firewall rule already exists${NC}"
fi

# Step 6: Create VM instance
echo -e "\n${CYAN}>>> Step 5: Creating VM instance...${NC}"
echo -e "${YELLOW}  This may take a few minutes...${NC}"

gcloud compute instances create "$VM_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --boot-disk-size="$DISK_SIZE" \
    --boot-disk-type=pd-standard \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --metadata-from-file startup-script="$TEMP_SCRIPT" \
    --tags=http-server,https-server \
    --scopes=cloud-platform \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD

if [ $? -ne 0 ]; then
    echo -e "${RED}  ✗ VM creation failed!${NC}"
    rm -f "$TEMP_SCRIPT"
    exit 1
fi

echo -e "${GREEN}  ✓ VM created successfully${NC}"

# Clean up temp script
rm -f "$TEMP_SCRIPT"

# Step 7: Wait for VM to be ready
echo -e "\n${CYAN}>>> Step 6: Waiting for VM to be ready...${NC}"
echo -e "${YELLOW}  Waiting 30 seconds for startup script to begin...${NC}"
sleep 30

# Step 8: Get VM information
echo -e "\n${CYAN}>>> Step 7: Retrieving VM information...${NC}"

VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --project="$PROJECT_ID" --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)
INTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --project="$PROJECT_ID" --format='get(networkInterfaces[0].networkIP)' 2>/dev/null)

# Display results
echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Complete Successfully!               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}VM Details:${NC}"
echo -e "  Name: ${GREEN}${VM_NAME}${NC}"
echo -e "  Zone: ${GREEN}${ZONE}${NC}"
echo -e "  External IP: ${GREEN}${VM_IP}${NC}"
echo -e "  Internal IP: ${GREEN}${INTERNAL_IP}${NC}"
echo -e "  Machine Type: ${GREEN}${MACHINE_TYPE}${NC}\n"

echo -e "${CYAN}Next Steps:${NC}"
echo -e "  1. ${YELLOW}SSH into VM:${NC}"
echo -e "     ${GREEN}gcloud compute ssh ${VM_NAME} --zone=${ZONE}${NC}\n"
echo -e "  2. ${YELLOW}Upload application code:${NC}"
echo -e "     ${GREEN}gcloud compute scp --recurse . ${VM_NAME}:/opt/travel-inbound --zone=${ZONE}${NC}\n"
echo -e "  3. ${YELLOW}Or use Git (from inside VM):${NC}"
echo -e "     ${GREEN}cd /opt/travel-inbound${NC}"
echo -e "     ${GREEN}git clone YOUR_REPO_URL .${NC}\n"
echo -e "  4. ${YELLOW}Install dependencies:${NC}"
echo -e "     ${GREEN}cd /opt/travel-inbound${NC}"
echo -e "     ${GREEN}source venv/bin/activate${NC}"
echo -e "     ${GREEN}pip install -r requirements.txt${NC}\n"
echo -e "  5. ${YELLOW}Initialize database:${NC}"
echo -e "     ${GREEN}python init_db.py${NC}\n"
echo -e "  6. ${YELLOW}Restart application:${NC}"
echo -e "     ${GREEN}supervisorctl restart travel-inbound${NC}\n"

echo -e "${CYAN}Useful Commands:${NC}"
echo -e "  View logs: ${GREEN}sudo tail -f /var/log/travel-inbound.out.log${NC}"
echo -e "  Check status: ${GREEN}supervisorctl status travel-inbound${NC}"
echo -e "  Restart app: ${GREEN}supervisorctl restart travel-inbound${NC}"
echo -e "  View startup log: ${GREEN}sudo cat /var/log/travel-inbound-startup.log${NC}\n"

echo -e "${YELLOW}Note:${NC} The startup script is still running. Check progress with:"
echo -e "  ${GREEN}gcloud compute ssh ${VM_NAME} --zone=${ZONE} --command='sudo tail -f /var/log/travel-inbound-startup.log'${NC}\n"
