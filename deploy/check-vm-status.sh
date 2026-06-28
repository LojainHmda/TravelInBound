#!/bin/bash
# Quick diagnostic script to check VM web server status

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     VM Web Server Status Check                         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

# Get IP addresses
echo -e "${CYAN}>>> IP Addresses:${NC}"
INTERNAL_IP=$(hostname -I | awk '{print $1}')
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Could not determine")
echo -e "  Internal IP: ${GREEN}${INTERNAL_IP}${NC}"
echo -e "  External IP: ${GREEN}${EXTERNAL_IP}${NC}"
echo -e "  ${YELLOW}Use External IP to access from browser${NC}\n"

# Check application status
echo -e "${CYAN}>>> Application Status:${NC}"
if command -v supervisorctl &> /dev/null; then
    if supervisorctl status travel-inbound &> /dev/null; then
        APP_STATUS=$(supervisorctl status travel-inbound)
        echo -e "  ${APP_STATUS}"
        if echo "$APP_STATUS" | grep -q "RUNNING"; then
            echo -e "  ${GREEN}✓ Application is RUNNING${NC}"
        else
            echo -e "  ${RED}✗ Application is NOT running${NC}"
            echo -e "  ${YELLOW}  Fix: sudo supervisorctl start travel-inbound${NC}"
        fi
    else
        echo -e "  ${RED}✗ Application not found in supervisor${NC}"
        echo -e "  ${YELLOW}  Check if deployment script ran successfully${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Supervisor not installed${NC}"
fi

# Check if port 5000 is listening
echo -e "\n${CYAN}>>> Port 5000 (Application):${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
    PORT_INFO=$(netstat -tlnp 2>/dev/null | grep ":5000 ")
    echo -e "  ${GREEN}✓ Port 5000 is listening${NC}"
    echo -e "  ${PORT_INFO}"
    
    # Check if listening on 127.0.0.1 or 0.0.0.0
    if echo "$PORT_INFO" | grep -q "127.0.0.1"; then
        echo -e "  ${GREEN}✓ Listening on 127.0.0.1 (correct for Nginx proxy)${NC}"
    elif echo "$PORT_INFO" | grep -q "0.0.0.0"; then
        echo -e "  ${GREEN}✓ Listening on 0.0.0.0 (also OK)${NC}"
    fi
else
    echo -e "  ${RED}✗ Port 5000 is NOT listening${NC}"
    echo -e "  ${YELLOW}  Application may not be running${NC}"
fi

# Check Nginx status
echo -e "\n${CYAN}>>> Nginx Status:${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}✓ Nginx is running${NC}"
else
    echo -e "  ${RED}✗ Nginx is NOT running${NC}"
    echo -e "  ${YELLOW}  Fix: sudo systemctl start nginx${NC}"
fi

# Check if port 80 is listening
echo -e "\n${CYAN}>>> Port 80 (Nginx):${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    PORT_INFO=$(netstat -tlnp 2>/dev/null | grep ":80 ")
    echo -e "  ${GREEN}✓ Port 80 is listening${NC}"
    echo -e "  ${PORT_INFO}"
    
    # Check if listening on 0.0.0.0 (required for external access)
    if echo "$PORT_INFO" | grep -q "0.0.0.0"; then
        echo -e "  ${GREEN}✓ Listening on 0.0.0.0 (accessible externally)${NC}"
    elif echo "$PORT_INFO" | grep -q "127.0.0.1"; then
        echo -e "  ${RED}✗ Listening only on 127.0.0.1 (NOT accessible externally)${NC}"
        echo -e "  ${YELLOW}  Fix: Update Nginx config to listen on 0.0.0.0${NC}"
    fi
else
    echo -e "  ${RED}✗ Port 80 is NOT listening${NC}"
    echo -e "  ${YELLOW}  Nginx may not be running or configured${NC}"
fi

# Test local connections
echo -e "\n${CYAN}>>> Testing Local Connections:${NC}"

echo -n "  Testing http://localhost:5000 (application)... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo -e "    ${YELLOW}Application may not be responding${NC}"
fi

echo -n "  Testing http://localhost (Nginx)... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302\|502"; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
    if [ "$HTTP_CODE" = "502" ]; then
        echo -e "${YELLOW}⚠ 502 Bad Gateway${NC}"
        echo -e "    ${YELLOW}Nginx can't reach application on port 5000${NC}"
    else
        echo -e "${GREEN}✓ OK (HTTP $HTTP_CODE)${NC}"
    fi
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# Check Nginx configuration
echo -e "\n${CYAN}>>> Nginx Configuration:${NC}"
if [ -f "/etc/nginx/sites-available/travel-inbound" ]; then
    echo -e "  ${GREEN}✓ Config file exists${NC}"
    
    # Check if it's enabled
    if [ -L "/etc/nginx/sites-enabled/travel-inbound" ]; then
        echo -e "  ${GREEN}✓ Config is enabled${NC}"
    else
        echo -e "  ${RED}✗ Config is NOT enabled${NC}"
        echo -e "  ${YELLOW}  Fix: sudo ln -s /etc/nginx/sites-available/travel-inbound /etc/nginx/sites-enabled/${NC}"
    fi
    
    # Test configuration
    if nginx -t 2>&1 | grep -q "successful"; then
        echo -e "  ${GREEN}✓ Configuration is valid${NC}"
    else
        echo -e "  ${RED}✗ Configuration has errors:${NC}"
        nginx -t 2>&1 | grep -i error || true
    fi
    
    # Check proxy_pass configuration
    if grep -q "proxy_pass.*127.0.0.1:5000" /etc/nginx/sites-available/travel-inbound; then
        echo -e "  ${GREEN}✓ Proxy configured correctly${NC}"
    else
        echo -e "  ${YELLOW}⚠ Proxy configuration may be incorrect${NC}"
    fi
else
    echo -e "  ${RED}✗ Config file not found${NC}"
fi

# Check recent logs
echo -e "\n${CYAN}>>> Recent Application Logs:${NC}"
if [ -f "/var/log/travel-inbound.out.log" ]; then
    echo -e "  ${CYAN}Last 3 lines:${NC}"
    tail -3 /var/log/travel-inbound.out.log 2>/dev/null || echo "  No log entries"
else
    echo -e "  ${YELLOW}⚠ Log file not found${NC}"
fi

if [ -f "/var/log/travel-inbound.err.log" ]; then
    ERR_LINES=$(wc -l < /var/log/travel-inbound.err.log 2>/dev/null || echo "0")
    if [ "$ERR_LINES" -gt 0 ]; then
        echo -e "  ${RED}✗ Errors found in error log:${NC}"
        tail -3 /var/log/travel-inbound.err.log 2>/dev/null
    else
        echo -e "  ${GREEN}✓ No errors in error log${NC}"
    fi
fi

# Check Nginx error log
echo -e "\n${CYAN}>>> Nginx Error Log:${NC}"
if [ -f "/var/log/nginx/error.log" ]; then
    RECENT_ERRORS=$(tail -5 /var/log/nginx/error.log | grep -i error | wc -l)
    if [ "$RECENT_ERRORS" -gt 0 ]; then
        echo -e "  ${RED}✗ Recent errors found:${NC}"
        tail -5 /var/log/nginx/error.log | grep -i error
    else
        echo -e "  ${GREEN}✓ No recent errors${NC}"
    fi
fi

# Summary and recommendations
echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Quick Fixes                           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}If application is not running:${NC}"
echo -e "  ${GREEN}sudo supervisorctl restart travel-inbound${NC}\n"

echo -e "${YELLOW}If Nginx is not running:${NC}"
echo -e "  ${GREEN}sudo systemctl restart nginx${NC}\n"

echo -e "${YELLOW}If you see 502 Bad Gateway:${NC}"
echo -e "  ${GREEN}sudo supervisorctl restart travel-inbound${NC}"
echo -e "  ${GREEN}sudo systemctl restart nginx${NC}\n"

echo -e "${YELLOW}Test from browser:${NC}"
echo -e "  ${GREEN}http://${EXTERNAL_IP}${NC}\n"

echo -e "${YELLOW}If still not working, check:${NC}"
echo -e "  1. Application logs: ${GREEN}sudo tail -f /var/log/travel-inbound.err.log${NC}"
echo -e "  2. Nginx logs: ${GREEN}sudo tail -f /var/log/nginx/error.log${NC}"
echo -e "  3. Application status: ${GREEN}sudo supervisorctl status travel-inbound${NC}\n"
