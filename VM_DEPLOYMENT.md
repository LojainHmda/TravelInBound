# Google Compute Engine VM Deployment Guide

This guide helps you deploy the Travel Inbound application to a Google Compute Engine VM.

## Quick Start

### Windows (PowerShell):
```powershell
.\deploy-vm.ps1
```

### Linux/macOS (Bash):
```bash
chmod +x deploy-vm.sh
./deploy-vm.sh
```

## Prerequisites

1. **Google Cloud SDK** installed
2. **Billing enabled** on your GCP project
3. **Compute Engine API** enabled

## Deployment Steps

### 1. Create VM Instance

The script will:
- Create a VM with Ubuntu 22.04
- Install Python 3.11, Nginx, Supervisor
- Set up basic configuration
- Configure firewall rules

### 2. SSH into VM

```bash
gcloud compute ssh travel-inbound-vm --zone=us-central1-a
```

### 3. Upload Application Code

**Option A: Using gcloud (from your local machine):**
```bash
gcloud compute scp --recurse . travel-inbound-vm:/opt/travel-inbound --zone=us-central1-a
```

**Option B: Using Git (from inside VM):**
```bash
cd /opt/travel-inbound
git clone YOUR_REPO_URL .
```

**Option C: Using rsync:**
```bash
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' ./ travel-inbound-vm:/opt/travel-inbound/
```

### 4. Install Dependencies

```bash
cd /opt/travel-inbound
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
sudo nano /opt/travel-inbound/.env
```

Add:
```
DATABASE_URL=postgresql://user:password@localhost/travel_inbound
SESSION_SECRET=your-secret-key
SESSION_COOKIE_SECURE=false
```

### 6. Set Up Database

**Option A: Install PostgreSQL on VM:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb travel_inbound
sudo -u postgres createuser travel_user
```

**Option B: Use Cloud SQL:**
- Create Cloud SQL instance
- Use Cloud SQL Proxy on VM

### 7. Initialize Database

```bash
cd /opt/travel-inbound
source venv/bin/activate
python init_db.py
```

### 8. Restart Services

```bash
sudo supervisorctl restart travel-inbound
sudo systemctl restart nginx
```

### 9. Configure Firewall

```bash
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags https-server
```

## Configuration Files

### Nginx Configuration
Located at: `/etc/nginx/sites-available/travel-inbound`

### Supervisor Configuration
Located at: `/etc/supervisor/conf.d/travel-inbound.conf`

### Application Directory
Located at: `/opt/travel-inbound`

## Useful Commands

### View Application Logs
```bash
sudo tail -f /var/log/travel-inbound.out.log
sudo tail -f /var/log/travel-inbound.err.log
```

### Restart Application
```bash
sudo supervisorctl restart travel-inbound
```

### Check Application Status
```bash
sudo supervisorctl status travel-inbound
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring

### Enable Cloud Monitoring
```bash
curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
sudo bash add-monitoring-agent-repo.sh
sudo apt-get update
sudo apt-get install stackdriver-agent
```

## Backup Strategy

### Database Backup
```bash
# PostgreSQL backup
pg_dump -U travel_user travel_inbound > backup_$(date +%Y%m%d).sql

# Upload to Cloud Storage
gsutil cp backup_*.sql gs://your-bucket/backups/
```

### Application Backup
```bash
# Backup application directory
tar -czf app_backup_$(date +%Y%m%d).tar.gz /opt/travel-inbound
gsutil cp app_backup_*.tar.gz gs://your-bucket/backups/
```

## Cost Optimization

- Use **e2-micro** or **e2-small** for development
- Use **e2-medium** or higher for production
- Enable **preemptible instances** for cost savings (dev only)
- Set up **auto-shutdown** for non-production VMs

## Security Best Practices

1. **Firewall Rules**: Only allow necessary ports
2. **SSH Keys**: Use SSH keys instead of passwords
3. **Regular Updates**: `sudo apt-get update && sudo apt-get upgrade`
4. **Fail2Ban**: Install for SSH protection
5. **SSL**: Always use HTTPS in production
6. **Secrets**: Use Secret Manager or environment variables

## Troubleshooting

### Application Not Starting
```bash
# Check supervisor logs
sudo supervisorctl tail -f travel-inbound stderr

# Check if port is in use
sudo netstat -tlnp | grep 5000
```

### Nginx Not Working
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -U travel_user -d travel_inbound -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

## Comparison: Cloud Run vs VM

| Feature | Cloud Run | VM |
|---------|-----------|-----|
| **Setup** | Easy | Moderate |
| **Scaling** | Automatic | Manual/Auto-scaling groups |
| **Cost** | Pay per request | Pay per hour |
| **Maintenance** | Managed | Self-managed |
| **Flexibility** | Limited | Full control |
| **Best For** | Serverless, auto-scaling | Full control, custom setup |

## Next Steps

1. Set up **automated backups**
2. Configure **monitoring and alerts**
3. Set up **CI/CD pipeline**
4. Configure **custom domain**
5. Set up **SSL certificate**
