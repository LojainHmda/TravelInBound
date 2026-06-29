"""
Migrate data from local SQLite (instance/app.db) to PostgreSQL (DATABASE_URL).
Run: $env:DATABASE_URL="postgresql://..."; python migrate_sqlite_to_postgres.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_sqlite_path():
    base = os.path.dirname(os.path.abspath(__file__))
    for path in [os.path.join(base, 'instance', 'app.db'), os.path.join(base, 'app.db')]:
        if os.path.exists(path):
            return path
    return os.path.join(base, 'instance', 'app.db')

def main():
    sqlite_path = get_sqlite_path()
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        sys.exit(1)

    pg_url = os.environ.get('DATABASE_URL')
    if not pg_url or not pg_url.startswith(('postgres', 'postgresql')):
        print("ERROR: DATABASE_URL (PostgreSQL) must be set.")
        sys.exit(1)

    if pg_url.startswith('postgres://'):
        pg_url = 'postgresql://' + pg_url[11:]

    sqlite_url = f"sqlite:///{sqlite_path.replace(os.sep, '/')}"
    print(f"Source: {sqlite_url}")
    print(f"Target: {pg_url[:60]}...")

    from sqlalchemy import create_engine, text, inspect

    src_engine = create_engine(sqlite_url)
    dst_engine = create_engine(pg_url)

    src_inspector = inspect(src_engine)
    tables = [t for t in src_inspector.get_table_names() if not t.startswith('sqlite_')]

    priority = ['user', 'agent', 'customer', 'booking', 'supplier', 'payment', 'supplier_service',
                'supplier_payment', 'supplier_prepayment_line', 'customer_document',
                'service_confirmation', 'service_item', 'document', 'oauth',
                'expense_category', 'expense', 'expense_attachment', 'financial_metric',
                'inbound_request', 'itinerary_row',  # Must be before child tables
                'arrival_batch', 'departure_batch', 'arrival_departure',
                'inbound_hotel', 'inbound_hotel_room', 'inbound_transport', 'inbound_meal',
                'inbound_guide', 'inbound_cash_expense', 'inbound_optional',
                'inbound_quotation', 'inbound_quotation_item', 'quotation_attachment',
                'inbound_document', 'invoice', 'invoice_line_item']
    ordered = [t for t in priority if t in tables]
    ordered += [t for t in tables if t not in ordered]

    print(f"\nMigrating {len(ordered)} tables...")

    os.environ['DATABASE_URL'] = pg_url
    from app import create_app, db
    app = create_app()
    with app.app_context():
        # Drop all tables with CASCADE (PostgreSQL requires this for FK dependencies)
        with dst_engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public;"))
            conn.commit()
        db.create_all()

    dst_inspector = inspect(dst_engine)
    for table_name in ordered:
        try:
            dst_cols = [c['name'] for c in dst_inspector.get_columns(table_name)]
            if not dst_cols:
                print(f"  {table_name}: (skipped - not in dest)")
                continue

            with src_engine.connect() as src_conn:
                result = src_conn.execute(text(f'SELECT * FROM "{table_name}"'))
                rows = result.fetchall()
                src_cols = list(result.keys())

            if not rows:
                print(f"  {table_name}: 0 rows")
                continue

            # Only use columns that exist in destination; source may have extra (legacy) columns
            common = [c for c in src_cols if c in dst_cols]
            # Add required dst columns that are missing from source (with defaults)
            extra_defaults = {}
            if table_name == 'user':
                for col in ['role', 'active']:
                    if col in dst_cols and col not in common:
                        common.append(col)
                        extra_defaults[col] = 'ops_manager' if col == 'role' else True
            if not common:
                print(f"  {table_name}: no common columns")
                continue

            col_list = ', '.join(f'"{c}"' for c in common)
            placeholders = ', '.join([f':p{i}' for i in range(len(common))])
            ins_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'

            # Get destination column types for boolean conversion (SQLite stores 0/1 as int)
            dst_col_types = {c['name']: str(c['type']) for c in dst_inspector.get_columns(table_name)}
            def convert_val(col_name, val):
                if val is None:
                    return None
                if 'BOOL' in dst_col_types.get(col_name, '').upper() and isinstance(val, int):
                    return bool(val)
                return val

            migrated = 0
            with dst_engine.connect() as dst_conn:
                for row in rows:
                    row_dict = dict(zip(src_cols, row))
                    params = {}
                    for i, c in enumerate(common):
                        if c in extra_defaults and (c not in row_dict or row_dict.get(c) is None):
                            params[f'p{i}'] = extra_defaults[c]
                        elif c in row_dict:
                            params[f'p{i}'] = convert_val(c, row_dict[c])
                        else:
                            params[f'p{i}'] = None
                    try:
                        dst_conn.execute(text(ins_sql), params)
                        dst_conn.commit()
                        migrated += 1
                    except Exception as e:
                        dst_conn.rollback()
                        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                            migrated += 1
                        else:
                            print(f"    Error: {e}")

            print(f"  {table_name}: {migrated}/{len(rows)} rows")
        except Exception as e:
            print(f"  {table_name}: ERROR - {e}")

    print("\nMigration complete.")

if __name__ == '__main__':
    main()
