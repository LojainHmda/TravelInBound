#!/usr/bin/env python
import sys
from sqlalchemy import text
from app import create_app, db

try:
    app = create_app()
    with app.app_context():
        # Check if column exists
        result = db.session.execute(text("PRAGMA table_info(supplier)"))
        columns = [row[1] for row in result]

        if 'entity_type' not in columns:
            print("Adding missing entity_type column...")
            db.session.execute(text('ALTER TABLE supplier ADD COLUMN entity_type VARCHAR(20) DEFAULT "COMPANY"'))
            db.session.commit()
            print("Success: Added entity_type column")
        else:
            print("Success: entity_type column already exists")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
