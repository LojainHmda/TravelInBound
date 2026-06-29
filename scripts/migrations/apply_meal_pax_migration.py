#!/usr/bin/env python3
"""Apply migration to add pax_count column to inbound_meal table"""
import os
import sys

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

database_uri = os.environ.get("DATABASE_URL", "sqlite:///app.db")
is_pg = database_uri.startswith(("postgresql://", "postgres://"))

print(f"Database: {database_uri}")
print(f"Type: {'PostgreSQL' if is_pg else 'SQLite'}")
print()

from sqlalchemy import create_engine, text, inspect

engine = create_engine(database_uri)
inspector = inspect(engine)
tables = [t.lower() if is_pg else t for t in inspector.get_table_names()]

if "inbound_meal" in tables:
    print("--- inbound_meal ---")
    columns = [c["name"] for c in inspector.get_columns("inbound_meal")]

    if "pax_count" not in columns:
        if is_pg:
            sql = "ALTER TABLE inbound_meal ADD COLUMN IF NOT EXISTS pax_count INTEGER NULL"
        else:
            sql = "ALTER TABLE inbound_meal ADD COLUMN pax_count INTEGER NULL"

        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("  [OK] Added: inbound_meal.pax_count")
            print("\n[SUCCESS] Migration applied successfully!")
        except Exception as e:
            print(f"  [FAILED] to add pax_count: {e}")
            sys.exit(1)
    else:
        print("  [OK] (exists): pax_count")
        print("\n[SUCCESS] Column already exists - no migration needed!")
else:
    print("[ERROR] inbound_meal table not found")
    sys.exit(1)
