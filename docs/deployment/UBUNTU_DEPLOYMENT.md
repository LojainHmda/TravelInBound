# Ubuntu VM Deployment Guide

Complete guide for deploying Travel Inbound to Ubuntu on Google Compute Engine.

## Quick Start

```bash
# Make script executable
chmod +x deploy-ubuntu.sh

# Deploy (uses default settings)
./deploy-ubuntu.sh

# Or with custom options
./deploy-ubuntu.sh --project-id my-project --zone us-east1-b --vm-name my-vm
```

## What Gets Installed

The deployment script automatically installs and configures:

- **Ubuntu 22.04 LTS** - Latest stable Ubuntu
- **Python 3.11** - Python runtime
- **PostgreSQL** - Database server (pre-configured)
- **Nginx** - Web server and reverse proxy
- **Supervisor** - Process manager for the application
- **System dependencies** - All required libraries

## Step-by-Step Deployment

### 1. Prerequisites

```bash
# Install Google Cloud SDK (if not installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Run Deployment Script

```bash
chmod +x deploy-ubuntu.sh
./deploy-ubuntu.sh
```

The script will:
1. Check prerequisites
2. Enable required APIs
3. Create firewall rules
4. Create VM with startup script
5. Display connection information

### 3. SSH into VM

```bash
# Get VM name and zone from script output
gcloud compute ssh travel-inbound-ubuntu --zone=us-central1-a
```

### 4. Upload Application Code

**Option A: Using gcloud scp (from your local machine)**
```bash
gcloud compute scp --recurse . travel-inbound-ubuntu:/opt/travel-inbound --zone=us-central1-a
```

**Option B: Using Git (from inside VM)**
```bash
cd /opt/travel-inbound
git clone https://github.com/your-username/your-repo.git .
```

**Option C: Using rsync (from your local machine)**
```bash
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
  ./ travel-inbound-ubuntu:/opt/travel-inbound/
```

### 5. Install Python Dependencies

```bash
cd /opt/travel-inbound
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Configure Environment Variables

```bash
# Create .env file
sudo nano /opt/travel-inbound/.env
```

Add:
```env
DATABASE_URL=postgresql://travel_user:change_this_password_in_production@localhost/travel_inbound
SESSION_SECRET=your-random-secret-key-here
SESSION_COOKIE_SECURE=false
PORT=5000
```

**Important**: Change the PostgreSQL password!

```bash
# Update PostgreSQL password
sudo -u postgres psql
ALTER USER travel_user WITH PASSWORD 'your_new_secure_password';
\q

# Update .env file with new password
```

### 7. Initialize Database

```bash
cd /opt/travel-inbound
source venv/bin/activate

# Update DATABASE_URL in .env first, then:
python init_db.py
```

### 8. Restart Application

```bash
sudo supervisorctl restart travel-inbound
```

### 9. Check Status

```bash
# Check if app is running
sudo supervisorctl status travel-inbound

# View logs
sudo tail -f /var/log/travel-inbound.out.log
```

### 10. Access Your Application

Visit: `http://YOUR_VM_EXTERNAL_IP`

Get IP address:
```bash
gcloud compute instances describe travel-inbound-ubuntu --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

## Configuration Files

### Application Directory
```
/opt/travel-inbound/
├── venv/              # Python virtual environment
├── app/              # Your application code
├── requirements.txt  # Python dependencies
├── main.py           # Application entry point
└── .env              # Environment variables
```

### Nginx Configuration
```
/etc/nginx/sites-available/travel-inbound
```

### Supervisor Configuration
```
/etc/supervisor/conf.d/travel-inbound.conf
```

### Logs
```
/var/log/travel-inbound.out.log    # Application stdout
/var/log/travel-inbound.err.log    # Application stderr
/var/log/travel-inbound-startup.log # Startup script log
/var/log/nginx/access.log          # Nginx access log
/var/log/nginx/error.log           # Nginx error log
```

## Useful Commands

### Application Management
```bash
# Start application
sudo supervisorctl start travel-inbound

# Stop application
sudo supervisorctl stop travel-inbound

# Restart application
sudo supervisorctl restart travel-inbound

# Check status
sudo supervisorctl status travel-inbound

# View logs
sudo tail -f /var/log/travel-inbound.out.log
sudo tail -f /var/log/travel-inbound.err.log
```

### Nginx Management
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# View logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Management
```bash
# Connect to PostgreSQL
sudo -u postgres psql travel_inbound

# Or as travel_user
psql -U travel_user -d travel_inbound -h localhost

# Backup database
pg_dump -U travel_user travel_inbound > backup_$(date +%Y%m%d).sql

# Restore database
psql -U travel_user travel_inbound < backup_20240118.sql
```

### System Updates
```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade

# Update application code
cd /opt/travel-inbound
git pull  # or upload new code
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart travel-inbound
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

### Using Cloud Load Balancer

1. Create static IP: `gcloud compute addresses create travel-inbound-ip --global`
2. Create Cloud Load Balancer with SSL certificate
3. Point domain to load balancer IP

## Monitoring

### Enable Cloud Monitoring Agent
```bash
curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
sudo bash add-monitoring-agent-repo.sh
sudo apt-get update
sudo apt-get install stackdriver-agent
```

### View Metrics
- Go to Cloud Console → Compute Engine → VM instances
- Click on your VM → Monitoring tab

## Backup Strategy

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

### Upload Backups to Cloud Storage
```bash
# Install gsutil (part of gcloud SDK)
# Upload backup
gsutil cp /opt/backups/*.sql.gz gs://your-bucket/backups/
```

## Troubleshooting

### Application Not Starting
```bash
# Check supervisor logs
sudo supervisorctl tail travel-inbound stderr

# Check if port is in use
sudo netstat -tlnp | grep 5000

# Check application logs
sudo tail -f /var/log/travel-inbound.err.log
```

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U travel_user -d travel_inbound -h localhost

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Nginx Issues
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check if Nginx is running
sudo systemctl status nginx
```

### High Memory Usage
```bash
# Check memory usage
free -h

# Check what's using memory
ps aux --sort=-%mem | head

# Reduce Gunicorn workers in supervisor config
sudo nano /etc/supervisor/conf.d/travel-inbound.conf
# Change --workers 2 to --workers 1
sudo supervisorctl restart travel-inbound
```

## Security Best Practices

1. **Change Default Passwords**
   ```bash
   # Change PostgreSQL password
   sudo -u postgres psql
   ALTER USER travel_user WITH PASSWORD 'strong_password';
   ```

2. **Set Up Firewall Rules**
   ```bash
   # Only allow necessary ports
   gcloud compute firewall-rules create allow-ssh \
       --allow tcp:22 \
       --source-ranges YOUR_IP/32 \
       --target-tags ssh-server
   ```

3. **Enable Automatic Updates**
   ```bash
   sudo apt-get install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

4. **Set Up Fail2Ban**
   ```bash
   sudo apt-get install fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

5. **Use SSH Keys**
   ```bash
   # Generate SSH key pair
   ssh-keygen -t rsa -b 4096
   
   # Add to VM
   gcloud compute instances add-metadata travel-inbound-ubuntu \
       --metadata-from-file ssh-keys=~/.ssh/id_rsa.pub
   ```

## Cost Optimization

- **Use e2-micro** for development/testing (~$6/month)
- **Use e2-small** for light production (~$12/month)
- **Use e2-medium** for moderate traffic (~$24/month)
- **Enable preemptible instances** for dev (60-80% savings)
- **Set up auto-shutdown** for non-production VMs

## Scaling

### Vertical Scaling (Upgrade VM)
```bash
# Stop VM
gcloud compute instances stop travel-inbound-ubuntu --zone=us-central1-a

# Change machine type
gcloud compute instances set-machine-type travel-inbound-ubuntu \
    --machine-type e2-standard-4 \
    --zone=us-central1-a

# Start VM
gcloud compute instances start travel-inbound-ubuntu --zone=us-central1-a
```

### Horizontal Scaling (Multiple VMs)
- Use Cloud Load Balancer
- Set up instance group
- Configure auto-scaling

## Next Steps

1. ✅ Set up custom domain
2. ✅ Configure SSL certificate
3. ✅ Set up monitoring and alerts
4. ✅ Configure automated backups
5. ✅ Set up CI/CD pipeline
6. ✅ Implement log aggregation

## Support

For issues:
- Check logs: `/var/log/travel-inbound-*.log`
- Check supervisor: `sudo supervisorctl status`
- Check Nginx: `sudo nginx -t && sudo systemctl status nginx`
- Check PostgreSQL: `sudo systemctl status postgresql`
