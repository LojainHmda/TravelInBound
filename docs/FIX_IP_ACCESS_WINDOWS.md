# Fix: Server Accessible by IP (Windows Instructions)

## Problem
Server works on `localhost` but not accessible by external IP address.

## Solution: Fix Nginx Configuration

### Step 1: Connect to Your VM

**Open PowerShell on Windows and run:**

```powershell
# Replace 'your-vm-name' and 'us-central1-a' with your actual values
gcloud compute ssh your-vm-name --zone=us-central1-a
```

**After this command, you'll be INSIDE the Ubuntu VM!**

### Step 2: Fix Nginx Configuration

**Once inside the VM, run these commands:**

```bash
# Edit the Nginx configuration file
sudo nano /etc/nginx/sites-available/travel-inbound
```

**In the nano editor:**
1. Find the line that says: `listen 80;`
2. Change it to: `listen 0.0.0.0:80;`
3. Add this line right after: `listen [::]:80;`

**It should look like this:**
```
server {
    listen 0.0.0.0:80;
    listen [::]:80;
    server_name _;
    ...
}
```

**To save and exit nano:**
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

### Step 3: Test and Restart Nginx

```bash
# Test the configuration
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx

# Verify it's running
sudo systemctl status nginx
```

### Step 4: Verify Port is Listening

```bash
# Check if port 80 is listening on all interfaces
sudo netstat -tlnp | grep :80
```

**You should see `0.0.0.0:80` (not `127.0.0.1:80`)**

### Step 5: Test Access

**Get your external IP:**
```bash
curl ifconfig.me
```

**Test from inside VM:**
```bash
curl http://YOUR-EXTERNAL-IP
```

**Then test from your Windows browser:**
```
http://YOUR-EXTERNAL-IP
```

---

## Alternative: Use the Fix Script

### Step 1: Upload Fix Script from Windows

**In PowerShell (on Windows):**
```powershell
gcloud compute scp fix-ip-access.sh your-vm-name:/tmp/ --zone=us-central1-a
```

### Step 2: SSH into VM

```powershell
gcloud compute ssh your-vm-name --zone=us-central1-a
```

### Step 3: Run Fix Script (Inside VM)

```bash
sudo bash /tmp/fix-ip-access.sh
```

The script will automatically fix everything!

---

## Quick One-Liner Fix (If You're Already in VM)

If you're already SSH'd into the VM, run this:

```bash
sudo sed -i 's/listen 80;/listen 0.0.0.0:80;\n    listen [::]:80;/' /etc/nginx/sites-available/travel-inbound && sudo nginx -t && sudo systemctl restart nginx
```

---

## Verify It's Fixed

**From Windows PowerShell (after fixing):**

```powershell
# Get your VM's external IP
gcloud compute instances describe your-vm-name --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

**Then open that IP in your browser:**
```
http://YOUR-EXTERNAL-IP
```

---

## Troubleshooting

### If Nginx won't start:

```bash
# Check for errors
sudo nginx -t

# View error log
sudo tail -20 /var/log/nginx/error.log
```

### If you see "502 Bad Gateway":

```bash
# Restart the application
sudo supervisorctl restart travel-inbound

# Check application status
sudo supervisorctl status travel-inbound
```

### If still not working:

```bash
# Check what's listening on port 80
sudo netstat -tlnp | grep :80

# Should show: 0.0.0.0:80
# If it shows 127.0.0.1:80, the fix didn't work
```

---

## Summary

**The Problem:** Nginx was only listening on `localhost` (127.0.0.1) instead of all interfaces (0.0.0.0).

**The Fix:** Change `listen 80;` to `listen 0.0.0.0:80;` in Nginx config.

**Quickest Way:** Use the fix script or the one-liner command above!
