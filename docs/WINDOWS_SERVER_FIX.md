# Fix: Flask Server Accessible by IP on Windows

## Important: This is Flask/Python, Not Node.js

Your application is **Flask (Python)**, not Node.js/Express.

## Current Configuration (Already Correct!)

Your `main.py` already has the correct configuration:

```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

**This is the Flask equivalent of:**
- Node.js: `app.listen(3000, "0.0.0.0")`
- Flask: `app.run(host="0.0.0.0", port=5000)`

✅ **Your server IS configured to listen on all interfaces (0.0.0.0)**

## The Real Problem: Windows Firewall

Windows Firewall is blocking incoming connections on port 5000.

## Solution: Allow Port 5000 Through Windows Firewall

### Step 1: Open PowerShell as Administrator

1. Press `Windows Key + X`
2. Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

### Step 2: Create Firewall Rule

**Run this command:**

```powershell
New-NetFirewallRule -DisplayName "Travel Inbound Flask App" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Step 3: Verify Server is Listening

**Check if server is listening on all interfaces:**

```powershell
netstat -an | findstr :5000
```

**You should see:**
```
TCP    0.0.0.0:5000           0.0.0.0:0              LISTENING
```

**If you see `127.0.0.1:5000`**, restart your server:
```powershell
python main.py
```

### Step 4: Get Your IP Address

```powershell
ipconfig | findstr IPv4
```

**Or get your LAN IP:**
```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"}).IPAddress
```

### Step 5: Test Access

**From the same Windows machine:**
```
http://YOUR-IP-ADDRESS:5000
```

**From another device on the same network:**
```
http://YOUR-IP-ADDRESS:5000
```

## Quick Test Commands

### Test from PowerShell:

```powershell
# Get your IP
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}).IPAddress
Write-Host "Your IP: $ip"

# Test connection (if curl is available)
curl http://$ip:5000

# Or use Invoke-WebRequest
Invoke-WebRequest -Uri "http://$ip:5000" -UseBasicParsing
```

## If Using Gunicorn

If you're running with Gunicorn instead of `python main.py`:

**Make sure to bind to 0.0.0.0:**

```powershell
gunicorn --bind 0.0.0.0:5000 main:app
```

**NOT:**
```powershell
gunicorn --bind 127.0.0.1:5000 main:app  # Wrong - only localhost
```

## Troubleshooting

### Check if firewall rule was created:

```powershell
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Travel*"}
```

### Check if port is open:

```powershell
Test-NetConnection -ComputerName localhost -Port 5000
```

### Check Windows Firewall status:

```powershell
Get-NetFirewallProfile | Select-Object Name, Enabled
```

### If still not working:

1. **Verify server is running:**
   ```powershell
   netstat -an | findstr :5000
   ```

2. **Check server logs** for any errors

3. **Try accessing from another device** on the same network

4. **Check router/network settings** if accessing from outside your network

## Summary

✅ **Your Flask config is correct** (`host="0.0.0.0"`)

❌ **Windows Firewall is blocking port 5000**

🔧 **Fix:** Run the firewall rule command above

🧪 **Test:** `http://YOUR-IP:5000`

---

## Flask vs Node.js Reference

| Node.js/Express | Flask/Python |
|----------------|--------------|
| `app.listen(3000, "0.0.0.0")` | `app.run(host="0.0.0.0", port=5000)` |
| `app.listen(3000)` | `app.run(port=5000)` (defaults to localhost) |
| Port 3000 | Port 5000 (or any port you choose) |

Your Flask app is already configured correctly! The issue is Windows Firewall.
