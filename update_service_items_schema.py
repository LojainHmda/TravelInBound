import sys
from app import db
import sqlalchemy as sa
from sqlalchemy import inspect

def main():
    """Update the ServiceItem table schema to include cancellation and credit memo fields"""
    
    print("Checking database schema for ServiceItem table...", file=sys.stderr)
    
    # Get inspector to check existing columns
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('service_item')]
    
    # Manual SQL statements for column adds
    statements = []
    
    # Check if each column exists and add it if it doesn't
    if 'invoice_number' not in columns:
        statements.append("ALTER TABLE service_item ADD COLUMN invoice_number VARCHAR(20)")
        
    if 'invoice_date' not in columns:
        statements.append("ALTER TABLE service_item ADD COLUMN invoice_date TIMESTAMP WITHOUT TIME ZONE")
        
    if 'is_invoiced' not in columns:
        statements.append("ALTER TABLE service_item ADD COLUMN is_invoiced BOOLEAN DEFAULT FALSE")
        
    if 'is_cancelled' not in columns:
        statements.append("ALTER TABLE service_item ADD COLUMN is_cancelled BOOLEAN DEFAULT FALSE")
        
    if 'credit_memo_number' not in columns:
        statements.append("ALTER TABLE service_item ADD COLUMN credit_memo_number VARCHAR(20)")
    
    # Execute the SQL statements
    if statements:
        conn = db.engine.connect()
        for stmt in statements:
            print(f"Executing: {stmt}", file=sys.stderr)
            conn.execute(sa.text(stmt))
        conn.commit()
        print("Schema update completed successfully!", file=sys.stderr)
    else:
        print("All required columns already exist in the schema!", file=sys.stderr)

if __name__ == "__main__":
    from main import app
    with app.app_context():
        main()