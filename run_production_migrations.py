#!/usr/bin/env python3
"""
Run schema migrations on production database.
Usage:
  # Local (uses .env or sqlite default):
  python run_production_migrations.py

  # Production (set DATABASE_URL first):
  set DATABASE_URL=postgresql://user:pass@host/db
  python run_production_migrations.py

  # Or inline:
  DATABASE_URL=postgresql://... python run_production_migrations.py
"""
import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

database_uri = os.environ.get("DATABASE_URL", "sqlite:///app.db")
is_pg = database_uri.startswith(("postgresql://", "postgres://"))

# Mask password in output
def _mask_uri(uri):
    if "@" in uri and ":" in uri:
        parts = uri.split("@", 1)
        user_part = parts[0].rsplit("://", 1)[-1]
        if ":" in user_part:
            user = user_part.split(":")[0]
            return uri.split("://")[0] + "://" + user + ":****@" + parts[1]
    return uri

print(f"Database: {_mask_uri(database_uri)}")
print(f"Type: {'PostgreSQL' if is_pg else 'SQLite'}")
print()

from sqlalchemy import create_engine, text, inspect

engine = create_engine(database_uri)
inspector = inspect(engine)
tables = [t.lower() if is_pg else t for t in inspector.get_table_names()]

if "inbound_request" in tables:
    req_columns = [c["name"] for c in inspector.get_columns("inbound_request")]
    required = [
        ("restaurant_voucher_note", "TEXT"),
        ("hotel_voucher_note", "TEXT"),
        ("advance_expense_sheet_data", "TEXT"),
        ("closing_guide_payment_sheet_data", "TEXT"),
        ("pending_invoice_queue", "BOOLEAN NOT NULL DEFAULT FALSE" if is_pg else "BOOLEAN DEFAULT 0"),
        ("deleted_reason", "TEXT"),
        ("parent_request_id", "INTEGER"),
        ("link_type", "VARCHAR(20)"),
        ("link_note", "TEXT"),
    ]

    added = []
    for col_name, col_type in required:
        if col_name not in req_columns:
            if is_pg:
                sql = f'ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS {col_name} {col_type}'
            else:
                sql = f'ALTER TABLE inbound_request ADD COLUMN {col_name} {col_type}'
            try:
                with engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()
                added.append(col_name)
                print(f"  Added: {col_name}")
            except Exception as e:
                print(f"  FAILED {col_name}: {e}")
                sys.exit(1)
        else:
            print(f"  OK (exists): {col_name}")

    # Fix PostgreSQL sequence if out of sync (fixes "Key (id)=X already exists" on new insert)
    if is_pg:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    SELECT setval(
                        pg_get_serial_sequence('inbound_request', 'id'),
                        COALESCE((SELECT MAX(id) FROM inbound_request), 1)
                    )
                """))
                conn.commit()
            print("\n  Fixed inbound_request id sequence")
        except Exception as e:
            print(f"\n  Sequence fix (non-fatal): {e}")

    if added:
        print(f"\nDone. Added {len(added)} column(s) on inbound_request.")
    else:
        print("\ninbound_request schema already up to date.")
else:
    print("WARNING: inbound_request table not found — skipping inbound_request migrations.")

# --- Migration 015: arrival/departure batch needs_transport + transport flight links ---
print("\n--- arrival_batch / departure_batch / inbound_transport ---")

def _table_columns(table_name):
    try:
        return [c["name"] for c in inspector.get_columns(table_name)]
    except Exception:
        return []


def _add_column_safe(table, col_name, sql_pg, sql_sqlite):
    cols = _table_columns(table)
    if col_name in cols:
        print(f"  OK (exists): {table}.{col_name}")
        return False
    sql = sql_pg if is_pg else sql_sqlite
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print(f"  Added: {table}.{col_name}")
        return True
    except Exception as e:
        print(f"  FAILED {table}.{col_name}: {e}")
        sys.exit(1)


added_batch = []
if "arrival_batch" in tables:
    if _add_column_safe(
        "arrival_batch",
        "needs_transport",
        "ALTER TABLE arrival_batch ADD COLUMN IF NOT EXISTS needs_transport BOOLEAN DEFAULT TRUE",
        "ALTER TABLE arrival_batch ADD COLUMN needs_transport BOOLEAN DEFAULT 1",
    ):
        added_batch.append("arrival_batch.needs_transport")
else:
    print("  (skip) arrival_batch table not found")

if "departure_batch" in tables:
    if _add_column_safe(
        "departure_batch",
        "needs_transport",
        "ALTER TABLE departure_batch ADD COLUMN IF NOT EXISTS needs_transport BOOLEAN DEFAULT TRUE",
        "ALTER TABLE departure_batch ADD COLUMN needs_transport BOOLEAN DEFAULT 1",
    ):
        added_batch.append("departure_batch.needs_transport")
else:
    print("  (skip) departure_batch table not found")

if "inbound_transport" in tables:
    it_cols = _table_columns("inbound_transport")
    if "source_arrival_batch_id" not in it_cols:
        sql = (
            "ALTER TABLE inbound_transport ADD COLUMN IF NOT EXISTS source_arrival_batch_id INTEGER REFERENCES arrival_batch(id)"
            if is_pg
            else "ALTER TABLE inbound_transport ADD COLUMN source_arrival_batch_id INTEGER REFERENCES arrival_batch(id)"
        )
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("  Added: inbound_transport.source_arrival_batch_id")
            added_batch.append("inbound_transport.source_arrival_batch_id")
        except Exception as e:
            print(f"  FAILED inbound_transport.source_arrival_batch_id: {e}")
            sys.exit(1)
    else:
        print("  OK (exists): inbound_transport.source_arrival_batch_id")

    it_cols = _table_columns("inbound_transport")
    if "source_departure_batch_id" not in it_cols:
        sql = (
            "ALTER TABLE inbound_transport ADD COLUMN IF NOT EXISTS source_departure_batch_id INTEGER REFERENCES departure_batch(id)"
            if is_pg
            else "ALTER TABLE inbound_transport ADD COLUMN source_departure_batch_id INTEGER REFERENCES departure_batch(id)"
        )
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("  Added: inbound_transport.source_departure_batch_id")
            added_batch.append("inbound_transport.source_departure_batch_id")
        except Exception as e:
            print(f"  FAILED inbound_transport.source_departure_batch_id: {e}")
            sys.exit(1)
    else:
        print("  OK (exists): inbound_transport.source_departure_batch_id")
else:
    print("  (skip) inbound_transport table not found")

if added_batch:
    print(f"\nDone. Added {len(added_batch)} column(s) for batch/transport links.")
else:
    print("\nBatch/transport columns already up to date.")

print("\n--- customer.payment_terms ---")
if "customer" in tables:
    if _add_column_safe(
        "customer",
        "payment_terms",
        "ALTER TABLE customer ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(100)",
        "ALTER TABLE customer ADD COLUMN payment_terms VARCHAR(100)",
    ):
        print("\nDone. Added customer.payment_terms.")
else:
    print("  (skip) customer table not found")

print("\n--- customer bank / Cliq ---")
if "customer" in tables:
    _add_column_safe(
        "customer",
        "bank_name",
        "ALTER TABLE customer ADD COLUMN IF NOT EXISTS bank_name VARCHAR(120)",
        "ALTER TABLE customer ADD COLUMN bank_name VARCHAR(120)",
    )
    _add_column_safe(
        "customer",
        "bank_account",
        "ALTER TABLE customer ADD COLUMN IF NOT EXISTS bank_account VARCHAR(255)",
        "ALTER TABLE customer ADD COLUMN bank_account VARCHAR(255)",
    )
    _add_column_safe(
        "customer",
        "cliq_alias",
        "ALTER TABLE customer ADD COLUMN IF NOT EXISTS cliq_alias VARCHAR(255)",
        "ALTER TABLE customer ADD COLUMN cliq_alias VARCHAR(255)",
    )
else:
    print("  (skip) customer table not found")
