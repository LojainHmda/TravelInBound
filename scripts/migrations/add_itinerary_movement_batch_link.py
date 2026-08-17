#!/usr/bin/env python3
"""Add source_arrival_batch_id / source_departure_batch_id to itinerary_row and
backfill existing movement rows.

Why: arrival/departure "movement" rows in the Itinerary were previously stored as
standalone ItineraryRow copies with no link to the ArrivalBatch/DepartureBatch
they came from, so deleting a batch left the itinerary row orphaned. These
columns restore the link; the backfill matches pre-existing rows to batches by
date so old data stays in sync too.

Idempotent and non-destructive:
  * columns are only added if missing
  * backfill only sets NULL links (never deletes, never overwrites an existing link)

Runs against every configured database it can find (DATABASE_URL and
DATABASE_URL_TEST) so both production and the dev/test DB get the change.
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, text, inspect


def _add_column_if_missing(engine, is_pg, table, column, ddl_type):
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns(table)]
    if column in columns:
        print(f"  [OK] (exists): {table}.{column}")
        return
    if is_pg:
        sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl_type}"
    else:
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(f"  [OK] Added: {table}.{column}")


def _backfill(engine, movement_prefix, desc_col_link, batch_table, batch_date_col):
    """Match unlinked movement rows to batches by (request_id, date), in id order."""
    updated = 0
    with engine.connect() as conn:
        # Unlinked movement rows for this movement type
        rows = conn.execute(text(
            f"""
            SELECT id, request_id, date
            FROM itinerary_row
            WHERE {desc_col_link} IS NULL
              AND lower(description) LIKE :prefix
            ORDER BY request_id, date, id
            """
        ), {"prefix": movement_prefix + " -%"}).fetchall()

        # Batches keyed by (request_id, date) -> queue of batch ids (id order)
        batch_rows = conn.execute(text(
            f"""
            SELECT id, request_id, {batch_date_col} AS bdate
            FROM {batch_table}
            WHERE {batch_date_col} IS NOT NULL
            ORDER BY request_id, {batch_date_col}, id
            """
        )).fetchall()

        buckets = {}
        for b in batch_rows:
            buckets.setdefault((b.request_id, str(b.bdate)), []).append(b.id)

        for r in rows:
            key = (r.request_id, str(r.date))
            queue = buckets.get(key)
            if queue:
                batch_id = queue.pop(0)
                conn.execute(text(
                    f"UPDATE itinerary_row SET {desc_col_link} = :bid WHERE id = :rid"
                ), {"bid": batch_id, "rid": r.id})
                updated += 1
        conn.commit()
    return updated


def migrate(database_uri):
    is_pg = database_uri.startswith(("postgresql://", "postgres://"))
    print(f"\nDatabase: {database_uri.split('@')[-1] if '@' in database_uri else database_uri}")
    print(f"Type: {'PostgreSQL' if is_pg else 'SQLite'}")

    engine = create_engine(database_uri)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "itinerary_row" not in tables:
        print("  [SKIP] itinerary_row table not found in this database")
        return

    _add_column_if_missing(engine, is_pg, "itinerary_row", "source_arrival_batch_id", "INTEGER")
    _add_column_if_missing(engine, is_pg, "itinerary_row", "source_departure_batch_id", "INTEGER")

    arr = _backfill(engine, "arrival", "source_arrival_batch_id", "arrival_batch", "arrival_date")
    dep = _backfill(engine, "departure", "source_departure_batch_id", "departure_batch", "departure_date")
    print(f"  [OK] Backfilled links -> arrivals: {arr}, departures: {dep}")


def main():
    uris = []
    for var in ("DATABASE_URL", "DATABASE_URL_TEST"):
        val = os.environ.get(var)
        if val and val not in uris:
            uris.append(val)

    if not uris:
        print("[ERROR] Neither DATABASE_URL nor DATABASE_URL_TEST is set")
        sys.exit(1)

    any_failed = False
    for uri in uris:
        try:
            migrate(uri)
        except Exception as e:
            any_failed = True
            print(f"  [FAILED] {e}")

    if any_failed:
        print("\n[DONE] Completed with errors — review output above.")
        sys.exit(1)
    print("\n[SUCCESS] Migration applied successfully!")


if __name__ == "__main__":
    main()
