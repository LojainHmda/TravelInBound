"""
Fix invoice table sequence (PostgreSQL) - run when getting "duplicate key value violates unique constraint invoice_pkey"
Usage: Set DATABASE_URL in .env or: $env:DATABASE_URL="postgresql://..."; python fix_invoice_sequence.py
"""
import os
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db_uri = os.environ.get("DATABASE_URL", "")
    if not db_uri.startswith(("postgresql://", "postgres://")):
        print("DATABASE_URL (PostgreSQL) required. Set in .env or environment.")
        exit(1)
    try:
        with db.engine.connect() as conn:
            conn.execute(text("""
                SELECT setval(pg_get_serial_sequence('invoice', 'id'),
                    COALESCE((SELECT MAX(id) FROM invoice), 1))
            """))
            conn.commit()
        print("Invoice sequence synced successfully.")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
