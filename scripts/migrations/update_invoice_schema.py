import sys
from app import db
import sqlalchemy as sa
from sqlalchemy import inspect

def main():
    """Add the Invoice table to the database schema"""
    
    print("Checking database for Invoice table...", file=sys.stderr)
    
    # Get inspector to check existing tables
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    # Check if the invoice table exists
    if 'invoice' in tables:
        print("Invoice table already exists!", file=sys.stderr)
        return
    
    print("Creating Invoice table...", file=sys.stderr)
    
    # Create the invoice table
    conn = db.engine.connect()
    
    # SQL statement to create the invoice table
    create_invoice_table = """
    CREATE TABLE invoice (
        id SERIAL PRIMARY KEY,
        booking_id INTEGER NOT NULL REFERENCES booking(id),
        invoice_number VARCHAR(30) UNIQUE NOT NULL,
        invoice_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
        total_amount FLOAT NOT NULL,
        notes TEXT,
        is_credit_memo BOOLEAN DEFAULT FALSE,
        referenced_invoice VARCHAR(30)
    );
    """
    
    try:
        conn.execute(sa.text(create_invoice_table))
        conn.commit()
        print("Invoice table created successfully!", file=sys.stderr)
    except Exception as e:
        print(f"Error creating Invoice table: {e}", file=sys.stderr)
        conn.rollback()
    
    # Also check if we need to migrate existing invoice data
    # For each booking that has an invoice_number, create a corresponding invoice record
    try:
        print("Migrating existing invoice data...", file=sys.stderr)
        # Get all bookings with an invoice number
        result = conn.execute(sa.text("""
            SELECT id, invoice_number, invoice_date, total_amount
            FROM booking
            WHERE invoice_number IS NOT NULL
        """))
        
        bookings_with_invoices = result.fetchall()
        
        if bookings_with_invoices:
            for booking in bookings_with_invoices:
                booking_id = booking[0]
                invoice_number = booking[1]
                invoice_date = booking[2]
                total_amount = booking[3]
                
                # Insert a new invoice record
                conn.execute(sa.text("""
                    INSERT INTO invoice 
                    (booking_id, invoice_number, invoice_date, total_amount, notes, is_credit_memo)
                    VALUES (:booking_id, :invoice_number, :invoice_date, :total_amount, 'Migrated from booking', false)
                """), {
                    'booking_id': booking_id,
                    'invoice_number': invoice_number,
                    'invoice_date': invoice_date,
                    'total_amount': total_amount
                })
            
            conn.commit()
            print(f"Migrated {len(bookings_with_invoices)} existing invoices", file=sys.stderr)
        else:
            print("No existing invoices to migrate", file=sys.stderr)
            
    except Exception as e:
        print(f"Error migrating invoice data: {e}", file=sys.stderr)
        conn.rollback()

if __name__ == "__main__":
    from main import app
    with app.app_context():
        main()