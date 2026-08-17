"""Start Flask server with better error handling and logging"""
import sys
import os
from app import create_app

# Set environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

print("=" * 60)
print("Starting Travel Inbound Flask Server")
print("=" * 60)

try:
    print("\nInterpreter:", sys.executable)
    print("Project:", os.path.dirname(os.path.abspath(__file__)))

    print("\n[1/3] Creating Flask application...")
    app = create_app()
    print("[OK] Application created successfully")
    
    print("\n[2/3] Testing index route...")
    with app.test_client() as client:
        response = client.get('/')
        if response.status_code == 200:
            print(f"[OK] Index route working (Status: {response.status_code})")
        else:
            print(f"[WARNING] Index route returned status {response.status_code}")
    
    print("\n[3/3] Starting server...")
    print("Server will be available at (this machine only):")
    print("  - http://localhost:5000")
    print("  - http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the server (localhost only — not reachable from LAN / 192.168.x.x)
    # use_reloader=True so form/route/template edits (e.g. CustomerForm.agent_name)
    # are picked up without a manual restart. Set FLASK_USE_RELOADER=0 to disable.
    _reload = os.environ.get("FLASK_USE_RELOADER", "1").lower() not in (
        "0",
        "false",
        "no",
    )
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=True,
        use_reloader=_reload,
        threaded=True,
    )
    
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
    sys.exit(0)
    
except Exception as e:
    print(f"\n[ERROR] Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
