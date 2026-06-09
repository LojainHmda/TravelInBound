#!/usr/bin/env python
import sys
from sqlalchemy import text, inspect
from app import create_app, db

try:
    app = create_app()
    with app.app_context():
        # Get existing columns
        inspector = inspect(db.engine)
        supplier_columns = [col['name'] for col in inspector.get_columns('supplier')]

        columns_to_add = []

        if 'entity_type' not in supplier_columns:
            columns_to_add.append(('entity_type', 'VARCHAR(20)', 'COMPANY'))

        if 'payment_method' not in supplier_columns:
            columns_to_add.append(('payment_method', 'VARCHAR(50)', 'UNKNOWN'))

        if columns_to_add:
            for col_name, col_type, default in columns_to_add:
                try:
                    sql = f'ALTER TABLE supplier ADD COLUMN {col_name} {col_type} DEFAULT "{default}"'
                    print(f"Adding column: {col_name}")
                    db.session.execute(text(sql))
                except Exception as e:
                    if 'already exists' not in str(e):
                        print(f"  Error adding {col_name}: {e}")

            db.session.commit()
            print("Success: Schema updated")
        else:
            print("Success: All columns exist")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
