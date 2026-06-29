# Fix: Can't Access VM Web Server by IP

## Most Common Issue: Google Cloud Firewall

Google Cloud blocks all incoming traffic by default. You need to create firewall rules.

## Quick Fix (Run on Your Local Machine)

### Step 1: Create HTTP Firewall Rule

**Windows PowerShell:**
```powershell
gcloud compute firewall-rules create allow-http `
    --allow tcp:80 `
    --source-ranges 0.0.0.0/0 `
    --target-tags http-server `
    --description "Allow HTTP traffic"
```

**Linux/macOS:**
```bash
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server \
    --description "Allow HTTP traffic"
```

### Step 2: Add http-server Tag to Your VM

**Find your VM name first:**
```powershell
gcloud compute instances list
```

**Then add the tag:**
```powershell
# Replace YOUR-VM-NAME and YOUR-ZONE with actual values
gcloud compute instances add-tags YOUR-VM-NAME `
    --tags http-server `
    --zone YOUR-ZONE
```

**Example:**
```powershell
gcloud compute instances add-tags travel-inbound-vm `
    --tags http-server `
    --zone us-central1-a
```

### Step 3: Get Your VM's External IP

```powershell
gcloud compute instances describe YOUR-VM-NAME `
    --zone YOUR-ZONE `
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

**Or list all VMs with IPs:**
```powershell
gcloud compute instances list
```

### Step 4: Test Access

Open your browser and go to:
```
http://YOUR-EXTERNAL-IP
```

---

## Other Common Issues

### Issue 2: Application Not Running

**SSH into VM and check:**
```bash
sudo supervisorctl status travel-inbound
```

**If not running, start it:**
```bash
sudo supervisorctl start travel-inbound
# Or restart
sudo supervisorctl restart travel-inbound
```

### Issue 3: Nginx Not Running

**Check Nginx status:**
```bash
sudo systemctl status nginx
```

**Start Nginx:**
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Issue 4: Wrong IP Address

Make sure you're using the **EXTERNAL IP**, not the internal IP.

**Get external IP:**
```powershell
gcloud compute instances list
```

Look for the "EXTERNAL_IP" column.

### Issue 5: Port Not Listening

**SSH into VM and check:**
```bash
# Check if port 80 is listening
sudo netstat -tlnp | grep :80

# Check if port 5000 is listening (application)
sudo netstat -tlnp | grep :5000
```

**If ports aren't listening:**
- Restart application: `sudo supervisorctl restart travel-inbound`
- Restart Nginx: `sudo systemctl restart nginx`

### Issue 6: UFW Firewall (if enabled on VM)

**SSH into VM:**
```bash
# Check UFW status
sudo ufw status

# Allow HTTP
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Complete Troubleshooting Checklist

Run this on your **local machine** (PowerShell):

```powershell
# 1. List all firewall rules
gcloud compute firewall-rules list

# 2. Check if allow-http exists
gcloud compute firewall-rules describe allow-http

# 3. List all VMs
gcloud compute instances list

# 4. Get VM external IP
gcloud compute instances describe YOUR-VM-NAME --zone YOUR-ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Run this **inside your VM** (after SSH):

```bash
# 1. Check application status
sudo supervisorctl status travel-inbound

# 2. Check Nginx status
sudo systemctl status nginx

# 3. Check if ports are listening
sudo netstat -tlnp | grep -E ":(80|5000)"

# 4. Test locally
curl http://localhost
curl http://localhost:5000

# 5. Check logs
sudo tail -f /var/log/travel-inbound.out.log
sudo tail -f /var/log/nginx/error.log
```

---

## Quick Test Commands

### From Your Local Machine:

```powershell
# Test if port 80 is open
Test-NetConnection -ComputerName YOUR-EXTERNAL-IP -Port 80

# Or use curl (if installed)
curl http://YOUR-EXTERNAL-IP
```

### From Inside VM (after SSH):

```bash
# Test application directly
curl http://localhost:5000

# Test through Nginx
curl http://localhost

# Test from external IP (if VM can reach itself)
curl http://EXTERNAL-IP
```

---

## Most Likely Solution

**90% of the time, it's the firewall rule!**

Run these two commands on your **local machine**:

```powershell
# 1. Create firewall rule
gcloud compute firewall-rules create allow-http --allow tcp:80 --source-ranges 0.0.0.0/0 --target-tags http-server

# 2. Add tag to VM (replace with your VM name and zone)
gcloud compute instances add-tags YOUR-VM-NAME --tags http-server --zone YOUR-ZONE
```

Then wait 30 seconds and try accessing `http://YOUR-EXTERNAL-IP` again!

---

## Still Not Working?

1. **Run the troubleshooting script:**
   ```bash
   # Upload and run on VM
   bash /tmp/troubleshoot-vm-access.sh
   ```

2. **Check Google Cloud Console:**
   - Go to: https://console.cloud.google.com/compute/instances
   - Click on your VM
   - Check "Firewall" section
   - Verify "http-server" tag is present

3. **Verify application is running:**
   - SSH into VM
   - Run: `sudo supervisorctl status travel-inbound`
   - Should show "RUNNING"

4. **Check Nginx:**
   - SSH into VM
   - Run: `sudo systemctl status nginx`
   - Should show "active (running)"
