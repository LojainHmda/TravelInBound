#!/usr/bin/env python
"""Test script to run Flask app with verbose output"""

import sys
import traceback
import os

os.chdir(r'C:\Users\user\TravelInBound-main')
sys.path.insert(0, r'C:\Users\user\TravelInBound-main')

print("Starting app creation...", flush=True)

try:
    from app import create_app
    print("App module imported successfully", flush=True)

    app = create_app()
    print("App created successfully", flush=True)
    print("Starting Flask server on 127.0.0.1:5000...", flush=True)

    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
