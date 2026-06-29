#!/usr/bin/env python3
"""Fix all PostgreSQL sequences - run when you get 'Key (id)=X already exists'"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

database_uri = os.environ.get("DATABASE_URL", "")
if not database_uri.startswith(("postgresql://", "postgres://")):
    print("Set DATABASE_URL to your PostgreSQL connection string")
    exit(1)

from sqlalchemy import create_engine, text
engine = create_engine(database_uri)

# All tables with id sequences that can get out of sync
tables = [
    'inbound_request', 'itinerary_row', 'inbound_hotel', 'hotel_room',
    'inbound_transport', 'inbound_meal', 'inbound_guide', 'inbound_cash_expense',
    'arrival_departure', 'arrival_batch', 'departure_batch', 'inbound_representative',
    'inbound_optional', 'inbound_quotation', 'inbound_quotation_item',
    'quotation_attachment', 'inbound_document', 'supplier', 'supplier_service',
    'supplier_payment', 'booking', 'service_item', 'customer', 'user', 'invoice',
]
with engine.connect() as conn:
    for tbl in tables:
        try:
            # Quote table name for reserved words (e.g. "user")
            q = f'"{tbl}"' if tbl == 'user' else tbl
            conn.execute(text(f"""
                SELECT setval(
                    pg_get_serial_sequence('{q}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {q}), 1)
                )
            """))
            conn.commit()
            print(f"Fixed {tbl}")
        except Exception as e:
            err = str(e).lower()
            if "does not exist" not in err and "null" not in err and "sequence" not in err:
                print(f"  {tbl}: {e}")
print("Done. All sequences synced.")
