"""Add pax_count column to inbound_meal table if it doesn't exist"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_pax_count_column():
    app = create_app()
    with app.app_context():
        try:
            # Try to add the column - will fail silently if it exists (SQLite)
            db.session.execute(text("""
                ALTER TABLE inbound_meal ADD COLUMN pax_count INTEGER DEFAULT 0
            """))
            db.session.commit()
            print("Added pax_count column to inbound_meal")
        except Exception as e:
            if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                print("Column pax_count already exists in inbound_meal")
            else:
                print(f"Note: {e}")
                print("If using MySQL/Postgres, you may need to run: ALTER TABLE inbound_meal ADD COLUMN pax_count INTEGER DEFAULT 0;")
            db.session.rollback()

if __name__ == '__main__':
    add_pax_count_column()
