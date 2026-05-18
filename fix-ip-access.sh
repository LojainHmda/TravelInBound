#!/bin/bash
# Fix script to make server accessible by IP address
# Run this ON your Ubuntu VM

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Fix: Make Server Accessible by IP                   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

APP_DIR="/opt/travel-inbound"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root or with sudo${NC}"
    echo -e "${YELLOW}  Usage: sudo bash fix-ip-access.sh${NC}"
    exit 1
fi

# Step 1: Check current Supervisor configuration
echo -e "${CYAN}>>> Step 1: Checking Supervisor configuration...${NC}"
if [ -f "/etc/supervisor/conf.d/travel-inbound.conf" ]; then
    echo -e "  ${GREEN}✓ Supervisor config found${NC}"
    
    # Check if binding to 127.0.0.1
    if grep -q "127.0.0.1:5000" /etc/supervisor/conf.d/travel-inbound.conf; then
        echo -e "  ${YELLOW}⚠ Application is binding to 127.0.0.1 (localhost only)${NC}"
        echo -e "  ${CYAN}  This is OK if Nginx is working correctly${NC}"
    fi
else
    echo -e "  ${RED}✗ Supervisor config not found${NC}"
    exit 1
fi

# Step 2: Check Nginx configuration
echo -e "\n${CYAN}>>> Step 2: Checking Nginx configuration...${NC}"
if [ -f "/etc/nginx/sites-available/travel-inbound" ]; then
    echo -e "  ${GREEN}✓ Nginx config found${NC}"
    
    # Check if listening on 0.0.0.0 or all interfaces
    if grep -q "listen 80;" /etc/nginx/sites-available/travel-inbound; then
        echo -e "  ${GREEN}✓ Nginx listening on port 80${NC}"
    fi
    
    # Check proxy_pass configuration
    if grep -q "proxy_pass.*127.0.0.1:5000" /etc/nginx/sites-available/travel-inbound; then
        echo -e "  ${GREEN}✓ Nginx proxy configured correctly${NC}"
    else
        echo -e "  ${RED}✗ Nginx proxy configuration issue${NC}"
    fi
else
    echo -e "  ${RED}✗ Nginx config not found${NC}"
    exit 1
fi

# Step 3: Ensure Nginx is listening on 0.0.0.0
echo -e "\n${CYAN}>>> Step 3: Ensuring Nginx listens on all interfaces...${NC}"

# Backup current config
cp /etc/nginx/sites-available/travel-inbound /etc/nginx/sites-available/travel-inbound.backup

# Update Nginx config to explicitly listen on all interfaces
cat > /etc/nginx/sites-available/travel-inbound << 'NGINX_EOF'
server {
    listen 0.0.0.0:80;
    listen [::]:80;
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

echo -e "  ${GREEN}✓ Nginx config updated${NC}"

# Step 4: Test Nginx configuration
echo -e "\n${CYAN}>>> Step 4: Testing Nginx configuration...${NC}"
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "  ${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "  ${RED}✗ Nginx configuration has errors:${NC}"
    nginx -t
    # Restore backup
    cp /etc/nginx/sites-available/travel-inbound.backup /etc/nginx/sites-available/travel-inbound
    exit 1
fi

# Step 5: Restart services
echo -e "\n${CYAN}>>> Step 5: Restarting services...${NC}"

# Restart Nginx
systemctl restart nginx
if systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}✓ Nginx restarted successfully${NC}"
else
    echo -e "  ${RED}✗ Nginx failed to start${NC}"
    systemctl status nginx
    exit 1
fi

# Restart application
supervisorctl restart travel-inbound
sleep 2

if supervisorctl status travel-inbound | grep -q RUNNING; then
    echo -e "  ${GREEN}✓ Application restarted successfully${NC}"
else
    echo -e "  ${RED}✗ Application failed to start${NC}"
    supervisorctl status travel-inbound
    exit 1
fi

# Step 6: Verify ports are listening
echo -e "\n${CYAN}>>> Step 6: Verifying ports are listening...${NC}"

# Check port 80
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    PORT_INFO=$(netstat -tlnp 2>/dev/null | grep ":80 ")
    echo -e "  ${GREEN}✓ Port 80 is listening${NC}"
    echo -e "    ${PORT_INFO}"
    
    if echo "$PORT_INFO" | grep -q "0.0.0.0"; then
        echo -e "  ${GREEN}✓ Listening on 0.0.0.0 (accessible externally)${NC}"
    fi
else
    echo -e "  ${RED}✗ Port 80 is NOT listening${NC}"
fi

# Check port 5000
if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
    echo -e "  ${GREEN}✓ Port 5000 is listening (application)${NC}"
else
    echo -e "  ${RED}✗ Port 5000 is NOT listening${NC}"
fi

# Step 7: Test connections
echo -e "\n${CYAN}>>> Step 7: Testing connections...${NC}"

# Test localhost
echo -n "  Testing http://localhost... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✓ OK (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "502" ]; then
    echo -e "${YELLOW}⚠ 502 Bad Gateway (application may not be running)${NC}"
else
    echo -e "${RED}✗ FAILED (HTTP $HTTP_CODE)${NC}"
fi

# Get external IP
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Could not determine")

# Summary
echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Fix Complete!                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}Your server should now be accessible at:${NC}"
echo -e "  ${GREEN}http://${EXTERNAL_IP}${NC}\n"

echo -e "${YELLOW}If still not accessible:${NC}"
echo -e "  1. Check firewall: ${GREEN}gcloud compute firewall-rules list${NC}"
echo -e "  2. Verify VM has http-server tag: ${GREEN}gcloud compute instances describe VM-NAME --format='get(tags.items)'${NC}"
echo -e "  3. Check application logs: ${GREEN}sudo tail -f /var/log/travel-inbound.err.log${NC}"
echo -e "  4. Check Nginx logs: ${GREEN}sudo tail -f /var/log/nginx/error.log${NC}\n"

echo -e "${CYAN}Test from VM itself:${NC}"
echo -e "  ${GREEN}curl http://${EXTERNAL_IP}${NC}\n"
