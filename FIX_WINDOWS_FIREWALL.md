# Fix: Server Accessible by IP on Windows

## Problem
Server works on `localhost` but not accessible by your Windows machine's IP address.

## Solution: Windows Firewall

Windows Firewall is likely blocking incoming connections on port 5000.

## Quick Fix

### Option 1: Allow Port Through Windows Firewall (Recommended)

**Run PowerShell as Administrator:**

```powershell
# Allow port 5000 through Windows Firewall
New-NetFirewallRule -DisplayName "Travel Inbound App" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

**Or use GUI:**
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → Next
5. Select "TCP" and enter port `5000` → Next
6. Select "Allow the connection" → Next
7. Check all profiles → Next
8. Name it "Travel Inbound App" → Finish

### Option 2: Temporarily Disable Firewall (For Testing Only)

**⚠️ Only for testing - not recommended for production!**

```powershell
# Run as Administrator
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
```

**Remember to re-enable it:**
```powershell
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

## Verify Your Server is Running Correctly

### Check if server is listening on all interfaces:

**In PowerShell:**
```powershell
netstat -an | findstr :5000
```

**You should see:**
```
TCP    0.0.0.0:5000           0.0.0.0:0              LISTENING
```

**If you see `127.0.0.1:5000` instead, the server is only listening on localhost.**

## How You're Running the Server

### If running with `python main.py`:
Your `main.py` already has `host="0.0.0.0"`, so it should work after firewall fix.

### If running with gunicorn:
Make sure you're binding to `0.0.0.0`:

```powershell
gunicorn --bind 0.0.0.0:5000 main:app
```

**NOT:**
```powershell
gunicorn --bind 127.0.0.1:5000 main:app  # This only allows localhost
```

## Get Your Windows IP Address

**In PowerShell:**
```powershell
# Get your local IP address
ipconfig | findstr IPv4
```

**Or:**
```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}).IPAddress
```

## Test Access

1. **From the same Windows machine:**
   ```
   http://YOUR-IP-ADDRESS:5000
   ```

2. **From another device on same network:**
   ```
   http://YOUR-IP-ADDRESS:5000
   ```

## Troubleshooting

### If still not working:

1. **Check if server is actually running:**
   ```powershell
   netstat -an | findstr :5000
   ```

2. **Check Windows Firewall rules:**
   ```powershell
   Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Travel*"}
   ```

3. **Check if port is actually listening:**
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 5000
   ```

4. **Try accessing from another device on the same network**

5. **Check your router/network settings** (if accessing from outside your network)

## Summary

**Most likely issue:** Windows Firewall blocking port 5000

**Quick fix:** Run this in PowerShell as Administrator:
```powershell
New-NetFirewallRule -DisplayName "Travel Inbound App" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

Then test: `http://YOUR-IP-ADDRESS:5000`
