#!/usr/bin/env python3
"""
Start the Flask application with SQLite database override
"""
import os
import sys

# Override all database environment variables to force SQLite usage
os.environ.pop('DATABASE_URL', None)
os.environ.pop('PGPORT', None)
os.environ.pop('PGUSER', None)
os.environ.pop('PGPASSWORD', None)
os.environ.pop('PGDATABASE', None)
os.environ.pop('PGHOST', None)

# Force SQLite database URL
os.environ['DATABASE_URL'] = 'sqlite:///travel_booking.db'

# Now import and run the Flask app
from app import app

if __name__ == "__main__":
    print("Starting with SQLite database...")
    print(f"Database URL: {os.environ.get('DATABASE_URL')}")
    app.run(host="0.0.0.0", port=5000, debug=True)