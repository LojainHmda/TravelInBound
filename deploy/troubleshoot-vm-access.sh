#!/bin/bash
# Troubleshooting script for VM web server access issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     VM Web Server Access Troubleshooting               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

# Step 1: Check IP addresses
echo -e "${CYAN}>>> Step 1: Checking IP addresses...${NC}"
INTERNAL_IP=$(hostname -I | awk '{print $1}')
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Could not determine")

echo -e "  Internal IP: ${GREEN}${INTERNAL_IP}${NC}"
echo -e "  External IP: ${GREEN}${EXTERNAL_IP}${NC}"
echo -e "  ${YELLOW}Note: Use External IP to access from outside${NC}\n"

# Step 2: Check if application is running
echo -e "${CYAN}>>> Step 2: Checking application status...${NC}"
if command -v supervisorctl &> /dev/null; then
    if supervisorctl status travel-inbound &> /dev/null; then
        STATUS=$(supervisorctl status travel-inbound | awk '{print $2}')
        if [ "$STATUS" = "RUNNING" ]; then
            echo -e "  ${GREEN}✓ Application is RUNNING${NC}"
        else
            echo -e "  ${RED}✗ Application status: ${STATUS}${NC}"
            echo -e "  ${YELLOW}  Try: sudo supervisorctl restart travel-inbound${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ Application not found in supervisor${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Supervisor not found${NC}"
fi

# Check if port 5000 is listening
if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
    echo -e "  ${GREEN}✓ Port 5000 is listening${NC}"
    netstat -tlnp 2>/dev/null | grep ":5000 " | head -1
else
    echo -e "  ${RED}✗ Port 5000 is NOT listening${NC}"
    echo -e "  ${YELLOW}  Application may not be running${NC}"
fi

# Step 3: Check Nginx status
echo -e "\n${CYAN}>>> Step 3: Checking Nginx status...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}✓ Nginx is running${NC}"
else
    echo -e "  ${RED}✗ Nginx is NOT running${NC}"
    echo -e "  ${YELLOW}  Try: sudo systemctl start nginx${NC}"
fi

# Check if port 80 is listening
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "  ${GREEN}✓ Port 80 is listening${NC}"
    netstat -tlnp 2>/dev/null | grep ":80 " | head -1
else
    echo -e "  ${RED}✗ Port 80 is NOT listening${NC}"
    echo -e "  ${YELLOW}  Nginx may not be running or configured${NC}"
fi

# Step 4: Check firewall status
echo -e "\n${CYAN}>>> Step 4: Checking firewall status...${NC}"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | head -1)
    echo -e "  UFW Status: ${UFW_STATUS}"
    if echo "$UFW_STATUS" | grep -q "active"; then
        echo -e "  ${YELLOW}⚠ Firewall is active - checking rules...${NC}"
        ufw status | grep -E "(80|443|22)" || echo -e "  ${RED}  No HTTP/HTTPS rules found${NC}"
        echo -e "  ${YELLOW}  To allow HTTP: sudo ufw allow 80/tcp${NC}"
        echo -e "  ${YELLOW}  To allow HTTPS: sudo ufw allow 443/tcp${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ UFW not installed (check iptables or cloud firewall)${NC}"
fi

# Step 5: Check Google Cloud firewall rules
echo -e "\n${CYAN}>>> Step 5: Google Cloud Firewall Rules...${NC}"
echo -e "  ${YELLOW}Checking if HTTP traffic is allowed...${NC}"
echo -e "  ${CYAN}Run this on your local machine:${NC}"
echo -e "  ${GREEN}gcloud compute firewall-rules list --filter='name~http'${NC}"
echo -e "  ${CYAN}If no HTTP rule exists, create one:${NC}"
echo -e "  ${GREEN}gcloud compute firewall-rules create allow-http --allow tcp:80 --source-ranges 0.0.0.0/0 --target-tags http-server${NC}"

# Step 6: Check Nginx configuration
echo -e "\n${CYAN}>>> Step 6: Checking Nginx configuration...${NC}"
if [ -f "/etc/nginx/sites-available/travel-inbound" ]; then
    echo -e "  ${GREEN}✓ Nginx config file exists${NC}"
    if nginx -t 2>&1 | grep -q "successful"; then
        echo -e "  ${GREEN}✓ Nginx configuration is valid${NC}"
    else
        echo -e "  ${RED}✗ Nginx configuration has errors:${NC}"
        nginx -t 2>&1 | grep -i error || true
    fi
else
    echo -e "  ${RED}✗ Nginx config file not found${NC}"
fi

# Step 7: Test local connection
echo -e "\n${CYAN}>>> Step 7: Testing local connections...${NC}"
echo -e "  Testing localhost:5000 (application)..."
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Application responds on localhost:5000${NC}"
else
    echo -e "  ${RED}✗ Application does NOT respond on localhost:5000${NC}"
fi

echo -e "  Testing localhost:80 (Nginx)..."
if curl -s http://localhost:80 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Nginx responds on localhost:80${NC}"
else
    echo -e "  ${RED}✗ Nginx does NOT respond on localhost:80${NC}"
fi

# Step 8: Check application logs
echo -e "\n${CYAN}>>> Step 8: Recent application logs...${NC}"
if [ -f "/var/log/travel-inbound.out.log" ]; then
    echo -e "  ${CYAN}Last 5 lines of application log:${NC}"
    tail -5 /var/log/travel-inbound.out.log 2>/dev/null || echo "  No log entries"
else
    echo -e "  ${YELLOW}⚠ Log file not found${NC}"
fi

if [ -f "/var/log/travel-inbound.err.log" ]; then
    ERR_COUNT=$(wc -l < /var/log/travel-inbound.err.log 2>/dev/null || echo "0")
    if [ "$ERR_COUNT" -gt 0 ]; then
        echo -e "  ${RED}✗ Found errors in error log:${NC}"
        tail -5 /var/log/travel-inbound.err.log 2>/dev/null
    fi
fi

# Summary and recommendations
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Summary & Fixes                       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}Common Issues & Solutions:${NC}\n"

echo -e "${CYAN}1. Google Cloud Firewall (Most Common):${NC}"
echo -e "   ${GREEN}gcloud compute firewall-rules create allow-http \\${NC}"
echo -e "       --allow tcp:80 \\${NC}"
echo -e "       --source-ranges 0.0.0.0/0 \\${NC}"
echo -e "       --target-tags http-server${NC}\n"

echo -e "${CYAN}2. Add http-server tag to VM:${NC}"
echo -e "   ${GREEN}gcloud compute instances add-tags YOUR-VM-NAME \\${NC}"
echo -e "       --tags http-server \\${NC}"
echo -e "       --zone YOUR-ZONE${NC}\n"

echo -e "${CYAN}3. Restart services:${NC}"
echo -e "   ${GREEN}sudo supervisorctl restart travel-inbound${NC}"
echo -e "   ${GREEN}sudo systemctl restart nginx${NC}\n"

echo -e "${CYAN}4. Check VM external IP:${NC}"
echo -e "   ${GREEN}gcloud compute instances describe YOUR-VM-NAME \\${NC}"
echo -e "       --zone YOUR-ZONE \\${NC}"
echo -e "       --format='get(networkInterfaces[0].accessConfigs[0].natIP)'${NC}\n"

echo -e "${CYAN}5. Test from VM itself:${NC}"
echo -e "   ${GREEN}curl http://localhost${NC}"
echo -e "   ${GREEN}curl http://EXTERNAL-IP${NC}\n"

echo -e "${GREEN}Use the External IP shown above to access your server!${NC}\n"
