"""
Migration script to add admin_invoice_data and customer_invoice_data columns to inbound_request table.
Run this script once to add the columns.
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('inbound_request')]

        for col_name in ('admin_invoice_data', 'customer_invoice_data'):
            if col_name not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text(f'ALTER TABLE inbound_request ADD COLUMN {col_name} TEXT'))
                    conn.commit()
                print(f"Successfully added '{col_name}' column")
            else:
                print(f"Column '{col_name}' already exists")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
