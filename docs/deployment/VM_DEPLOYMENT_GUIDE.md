# Linux VM Deployment Guide

Complete guide for deploying Travel Inbound on an existing Linux VM.

## Quick Start

### 1. Upload Files to VM

```bash
# From your local machine, upload the application
gcloud compute scp --recurse . your-vm-name:/opt/travel-inbound --zone=us-central1-a

# Or using rsync
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
  ./ your-vm-name:/opt/travel-inbound/
```

### 2. SSH into VM

```bash
gcloud compute ssh your-vm-name --zone=us-central1-a
```

### 3. Run Deployment Script

```bash
# Upload the deployment script if not already there
# Or download it:
wget https://raw.githubusercontent.com/your-repo/deploy-on-vm.sh

# Make executable
chmod +x deploy-on-vm.sh

# Run as root
sudo ./deploy-on-vm.sh
```

## What the Script Does

The `deploy-on-vm.sh` script automatically:

1. ✅ Updates system packages
2. ✅ Installs Python 3.11, PostgreSQL, Nginx, Supervisor
3. ✅ Creates virtual environment
4. ✅ Installs Python dependencies
5. ✅ Sets up PostgreSQL database and user
6. ✅ Configures Nginx reverse proxy
7. ✅ Configures Supervisor for process management
8. ✅ Creates environment configuration file
9. ✅ Sets proper permissions
10. ✅ Starts the application

## Manual Deployment (Step by Step)

If you prefer to deploy manually:

### Step 1: Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install Dependencies

```bash
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    supervisor \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    build-essential
```

### Step 3: Set Up Application

```bash
# Create directory
sudo mkdir -p /opt/travel-inbound
cd /opt/travel-inbound

# Upload your code here (or clone from Git)
# Then create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure PostgreSQL

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE travel_inbound;
CREATE USER travel_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE travel_inbound TO travel_user;
\q
```

### Step 5: Create Environment File

```bash
cat > /opt/travel-inbound/.env << EOF
DATABASE_URL=postgresql://travel_user:your_password@localhost/travel_inbound
SESSION_SECRET=$(openssl rand -hex 32)
SESSION_COOKIE_SECURE=false
PORT=5000
EOF
```

### Step 6: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/travel-inbound
```

Add:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/travel-inbound /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Configure Supervisor

```bash
sudo nano /etc/supervisor/conf.d/travel-inbound.conf
```

Add:
```ini
[program:travel-inbound]
command=/opt/travel-inbound/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 main:app
directory=/opt/travel-inbound
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/travel-inbound.err.log
stdout_logfile=/var/log/travel-inbound.out.log
```

Reload:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start travel-inbound
```

### Step 8: Initialize Database

```bash
cd /opt/travel-inbound
source venv/bin/activate
export $(cat .env | xargs)
python init_db.py
```

## Updating the Application

### Quick Update Script

Create `/opt/travel-inbound/update.sh`:

```bash
#!/bin/bash
cd /opt/travel-inbound
source venv/bin/activate

# Pull latest code (if using Git)
git pull

# Install/update dependencies
pip install -r requirements.txt

# Restart application
sudo supervisorctl restart travel-inbound

echo "Update complete!"
```

Make executable:
```bash
chmod +x /opt/travel-inbound/update.sh
```

Run updates:
```bash
sudo /opt/travel-inbound/update.sh
```

## Troubleshooting

### Application Not Starting

```bash
# Check supervisor status
sudo supervisorctl status travel-inbound

# View error logs
sudo tail -f /var/log/travel-inbound.err.log

# Check if port is in use
sudo netstat -tlnp | grep 5000

# Try starting manually
cd /opt/travel-inbound
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 main:app
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U travel_user -d travel_inbound -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/travel-inbound
sudo chmod -R 755 /opt/travel-inbound
```

## SSL/HTTPS Setup

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

## Monitoring

### View Application Logs

```bash
# Real-time logs
sudo tail -f /var/log/travel-inbound.out.log

# Error logs
sudo tail -f /var/log/travel-inbound.err.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Application Status

```bash
# Supervisor status
sudo supervisorctl status travel-inbound

# System resources
htop
df -h
free -h
```

## Backup

### Database Backup

```bash
# Create backup script
cat > /opt/travel-inbound/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
mkdir -p $BACKUP_DIR
pg_dump -U travel_user travel_inbound | gzip > $BACKUP_DIR/travel_inbound_$(date +%Y%m%d_%H%M%S).sql.gz
# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /opt/travel-inbound/backup-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /opt/travel-inbound/backup-db.sh
```

## Security

### Firewall Setup

```bash
# Install UFW
sudo apt-get install ufw

# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### Change Default Passwords

```bash
# Change PostgreSQL password
sudo -u postgres psql
ALTER USER travel_user WITH PASSWORD 'new_strong_password';
\q

# Update .env file
sudo nano /opt/travel-inbound/.env
```

## Useful Commands Reference

```bash
# Application
sudo supervisorctl start travel-inbound
sudo supervisorctl stop travel-inbound
sudo supervisorctl restart travel-inbound
sudo supervisorctl status travel-inbound

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl status nginx
sudo nginx -t

# PostgreSQL
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
sudo systemctl status postgresql

# View logs
sudo tail -f /var/log/travel-inbound.out.log
sudo tail -f /var/log/travel-inbound.err.log
sudo journalctl -u supervisor -f
```

## Next Steps

1. ✅ Set up SSL certificate
2. ✅ Configure custom domain
3. ✅ Set up automated backups
4. ✅ Configure monitoring
5. ✅ Set up log rotation
6. ✅ Configure firewall rules
