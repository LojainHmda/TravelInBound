# Server Startup Guide

## Issue: Server Not Responding

The server at `34.30.19.150:5000` is not responding. Here's how to diagnose and fix:

## Step 1: Check if Server is Running

```powershell
# Check if port 5000 is in use
netstat -an | findstr :5000
```

If you see `LISTENING`, the server is running but may be hanging.

## Step 2: Start/Restart the Server

```powershell
# Navigate to project directory
cd C:\Users\eyad\Desktop\TravelInbound7050126

# Start the server
py main.py
```

## Step 3: Check Server Logs

Look for these errors in the console:
- Database connection errors
- Query timeout errors
- Import errors
- Template errors

## Step 4: Test Locally First

Before accessing via IP, test locally:

```powershell
# Test locally
http://localhost:5000
```

If localhost works but IP doesn't:
- Check Windows Firewall (allow port 5000)
- Check if server is bound to 0.0.0.0 (it should be)

## Step 5: Check Database Connection

The server may be hanging on database queries. Check:

1. Database file exists: `instance/app.db` or `instance/travel_booking.db`
2. Database is not locked by another process
3. Database indexes are created (run `py add_supplier_indexes.py`)

## Step 6: Quick Fixes Applied

We've already applied these optimizations:
- ✅ Added query limits to prevent timeouts
- ✅ Added database indexes for faster queries
- ✅ Improved error handling
- ✅ Reduced connection pool size

## Step 7: If Server Still Hangs

Try starting with minimal configuration:

```python
# Create a minimal test server
from app import create_app
app = create_app()
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
```

## Common Issues

1. **Database Locked**: Close any database viewers/editors
2. **Port Already in Use**: Kill existing process: `taskkill /F /IM python.exe`
3. **Firewall**: Allow port 5000 through Windows Firewall
4. **Database Timeout**: Check database connection string in environment variables

## Emergency: Start with Debug Mode

```powershell
$env:FLASK_DEBUG=1
py main.py
```

This will show detailed error messages.
