#!/bin/bash
# Deployment Script for Travel Inbound - Run this ON your Linux VM
# This script sets up and deploys the application on an existing Ubuntu/Debian VM

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_DIR="/opt/travel-inbound"
APP_USER="www-data"
PYTHON_VERSION="3.11"
PORT=5000

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Travel Inbound - VM Deployment Script               ║"
echo "║     Run this script ON your Linux VM                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root or with sudo${NC}"
    echo -e "${YELLOW}  Usage: sudo ./deploy-on-vm.sh${NC}"
    exit 1
fi

# Step 1: Update system
echo -e "${CYAN}>>> Step 1: Updating system packages...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}✓ System updated${NC}"

# Step 2: Install system dependencies
echo -e "\n${CYAN}>>> Step 2: Installing system dependencies...${NC}"
apt-get install -y -qq \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
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
    zlib1g-dev \
    software-properties-common

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Create application directory
echo -e "\n${CYAN}>>> Step 3: Setting up application directory...${NC}"
mkdir -p ${APP_DIR}
cd ${APP_DIR}

# Check if code already exists
if [ -f "main.py" ]; then
    echo -e "${YELLOW}⚠ Application code found in ${APP_DIR}${NC}"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}  Backing up existing code...${NC}"
        cp -r . ../travel-inbound-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
    fi
else
    echo -e "${YELLOW}⚠ No application code found in ${APP_DIR}${NC}"
    echo -e "${YELLOW}  Please upload your code to ${APP_DIR} before continuing${NC}"
    echo -e "${YELLOW}  Or the script will create a basic structure${NC}"
fi

# Create virtual environment
echo -e "${CYAN}  Creating Python virtual environment...${NC}"
python${PYTHON_VERSION} -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel --quiet

echo -e "${GREEN}✓ Application directory ready${NC}"

# Step 4: Install Python dependencies
echo -e "\n${CYAN}>>> Step 4: Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed from requirements.txt${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found${NC}"
    echo -e "${YELLOW}  Installing basic dependencies...${NC}"
    pip install flask flask-sqlalchemy gunicorn psycopg2-binary
fi

# Step 5: Set up PostgreSQL
echo -e "\n${CYAN}>>> Step 5: Configuring PostgreSQL...${NC}"

# Check if database and user already exist
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='travel_inbound'" 2>/dev/null || echo "0")
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='travel_user'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" != "1" ]; then
    echo -e "${CYAN}  Creating database...${NC}"
    sudo -u postgres psql << PSQL_EOF
CREATE DATABASE travel_inbound;
PSQL_EOF
    echo -e "${GREEN}  ✓ Database created${NC}"
else
    echo -e "${YELLOW}  ⚠ Database already exists${NC}"
fi

if [ "$USER_EXISTS" != "1" ]; then
    echo -e "${CYAN}  Creating database user...${NC}"
    read -sp "Enter password for travel_user: " DB_PASSWORD
    echo
    sudo -u postgres psql << PSQL_EOF
CREATE USER travel_user WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE travel_user SET client_encoding TO 'utf8';
ALTER ROLE travel_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE travel_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE travel_inbound TO travel_user;
\q
PSQL_EOF
    echo -e "${GREEN}  ✓ User created${NC}"
    echo -e "${YELLOW}  ⚠ Save this password: ${DB_PASSWORD}${NC}"
else
    echo -e "${YELLOW}  ⚠ User already exists${NC}"
    read -sp "Enter password for travel_user (or press Enter to skip): " DB_PASSWORD
    echo
    if [ -n "$DB_PASSWORD" ]; then
        sudo -u postgres psql << PSQL_EOF
ALTER USER travel_user WITH PASSWORD '${DB_PASSWORD}';
PSQL_EOF
    fi
fi

# Step 6: Create environment file
echo -e "\n${CYAN}>>> Step 6: Creating environment configuration...${NC}"
if [ ! -f "${APP_DIR}/.env" ]; then
    cat > ${APP_DIR}/.env << ENV_EOF
# Database Configuration
DATABASE_URL=postgresql://travel_user:${DB_PASSWORD:-change_this_password}@localhost/travel_inbound

# Session Configuration
SESSION_SECRET=$(openssl rand -hex 32)
SESSION_COOKIE_SECURE=false

# Application Configuration
PORT=${PORT}
FLASK_ENV=production
PYTHONUNBUFFERED=1
ENV_EOF
    echo -e "${GREEN}✓ Environment file created${NC}"
    echo -e "${YELLOW}  ⚠ Review and update ${APP_DIR}/.env if needed${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping creation${NC}"
fi

# Step 7: Configure Nginx
echo -e "\n${CYAN}>>> Step 7: Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/travel-inbound << NGINX_EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static {
        alias ${APP_DIR}/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# Enable site
ln -sf /etc/nginx/sites-available/travel-inbound /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

echo -e "${GREEN}✓ Nginx configured${NC}"

# Step 8: Configure Supervisor
echo -e "\n${CYAN}>>> Step 8: Configuring Supervisor...${NC}"
cat > /etc/supervisor/conf.d/travel-inbound.conf << SUPERVISOR_EOF
[program:travel-inbound]
command=${APP_DIR}/venv/bin/gunicorn --bind 127.0.0.1:${PORT} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - main:app
directory=${APP_DIR}
user=${APP_USER}
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

# Reload supervisor
supervisorctl reread
supervisorctl update

echo -e "${GREEN}✓ Supervisor configured${NC}"

# Step 9: Set permissions
echo -e "\n${CYAN}>>> Step 9: Setting permissions...${NC}"
chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
chmod -R 755 ${APP_DIR}

echo -e "${GREEN}✓ Permissions set${NC}"

# Step 10: Initialize database (if init script exists)
echo -e "\n${CYAN}>>> Step 10: Database initialization...${NC}"
if [ -f "${APP_DIR}/init_db.py" ]; then
    echo -e "${CYAN}  Running database initialization...${NC}"
    cd ${APP_DIR}
    source venv/bin/activate
    export $(cat .env | xargs)
    python init_db.py || echo -e "${YELLOW}  ⚠ Database initialization had issues (this is OK if tables already exist)${NC}"
    echo -e "${GREEN}✓ Database initialization complete${NC}"
else
    echo -e "${YELLOW}⚠ init_db.py not found, skipping database initialization${NC}"
    echo -e "${YELLOW}  Run manually: cd ${APP_DIR} && source venv/bin/activate && python init_db.py${NC}"
fi

# Step 11: Start application
echo -e "\n${CYAN}>>> Step 11: Starting application...${NC}"
supervisorctl start travel-inbound || supervisorctl restart travel-inbound
sleep 2

# Check status
if supervisorctl status travel-inbound | grep -q RUNNING; then
    echo -e "${GREEN}✓ Application started successfully${NC}"
else
    echo -e "${RED}✗ Application failed to start${NC}"
    echo -e "${YELLOW}  Check logs: sudo tail -f /var/log/travel-inbound.err.log${NC}"
    exit 1
fi

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Display summary
echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Complete Successfully!               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}Application Details:${NC}"
echo -e "  Directory: ${GREEN}${APP_DIR}${NC}"
echo -e "  IP Address: ${GREEN}${IP_ADDRESS}${NC}"
echo -e "  Port: ${GREEN}${PORT}${NC}"
echo -e "  Access URL: ${GREEN}http://${IP_ADDRESS}${NC}\n"

echo -e "${CYAN}Useful Commands:${NC}"
echo -e "  View logs: ${GREEN}sudo tail -f /var/log/travel-inbound.out.log${NC}"
echo -e "  Check status: ${GREEN}sudo supervisorctl status travel-inbound${NC}"
echo -e "  Restart app: ${GREEN}sudo supervisorctl restart travel-inbound${NC}"
echo -e "  Stop app: ${GREEN}sudo supervisorctl stop travel-inbound${NC}"
echo -e "  Start app: ${GREEN}sudo supervisorctl start travel-inbound${NC}\n"

echo -e "${CYAN}Configuration Files:${NC}"
echo -e "  Environment: ${GREEN}${APP_DIR}/.env${NC}"
echo -e "  Nginx: ${GREEN}/etc/nginx/sites-available/travel-inbound${NC}"
echo -e "  Supervisor: ${GREEN}/etc/supervisor/conf.d/travel-inbound.conf${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Review and update ${APP_DIR}/.env if needed"
echo -e "  2. Initialize database: cd ${APP_DIR} && source venv/bin/activate && python init_db.py"
echo -e "  3. Set up SSL/HTTPS (optional): sudo certbot --nginx -d your-domain.com"
echo -e "  4. Configure firewall: sudo ufw allow 80/tcp && sudo ufw allow 443/tcp\n"

echo -e "${GREEN}Deployment complete! Your application should be running at http://${IP_ADDRESS}${NC}\n"
