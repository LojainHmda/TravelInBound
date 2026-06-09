#!/usr/bin/env python
import sys
from sqlalchemy import text, inspect
from app import create_app, db

# All columns that should exist in supplier table
EXPECTED_COLUMNS = {
    'id': 'INTEGER PRIMARY KEY',
    'name': 'VARCHAR(255)',
    'code': 'VARCHAR(50)',
    'supplier_type': 'VARCHAR(50)',
    'entity_type': 'VARCHAR(20)',
    'email': 'VARCHAR(255)',
    'phone': 'VARCHAR(20)',
    'website': 'VARCHAR(255)',
    'contact_person': 'VARCHAR(255)',
    'address': 'TEXT',
    'city': 'VARCHAR(100)',
    'country': 'VARCHAR(100)',
    'payment_terms': 'VARCHAR(100)',
    'payment_method': 'VARCHAR(50)',
    'default_currency': 'VARCHAR(10)',
    'bank_name': 'VARCHAR(255)',
    'bank_account': 'VARCHAR(50)',
    'bank_iban': 'VARCHAR(100)',
    'tax_number': 'VARCHAR(50)',
    'notes': 'TEXT',
    'languages': 'VARCHAR(255)',
    'created_at': 'DATETIME',
    'updated_at': 'DATETIME',
    'is_active': 'BOOLEAN',
}

try:
    app = create_app()
    with app.app_context():
        # Get existing columns
        inspector = inspect(db.engine)
        existing_columns = {col['name']: col for col in inspector.get_columns('supplier')}

        # Determine which columns to add
        columns_to_add = []
        for col_name in EXPECTED_COLUMNS:
            if col_name not in existing_columns and col_name != 'id':
                columns_to_add.append(col_name)

        if columns_to_add:
            print(f"Adding {len(columns_to_add)} missing columns...")
            for col_name in columns_to_add:
                try:
                    # Determine default based on column name
                    if 'date' in col_name or 'created' in col_name or 'updated' in col_name:
                        sql = f'ALTER TABLE supplier ADD COLUMN {col_name} DATETIME DEFAULT CURRENT_TIMESTAMP'
                    elif 'is_' in col_name or col_name == 'is_active':
                        sql = f'ALTER TABLE supplier ADD COLUMN {col_name} BOOLEAN DEFAULT 1'
                    else:
                        sql = f'ALTER TABLE supplier ADD COLUMN {col_name} TEXT DEFAULT ""'

                    db.session.execute(text(sql))
                    print(f"  Added: {col_name}")
                except Exception as e:
                    print(f"  Error adding {col_name}: {e}")

            db.session.commit()
            print("Success: All missing columns added")
        else:
            print("Success: All columns exist")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
