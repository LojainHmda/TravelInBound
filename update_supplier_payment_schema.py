"""
Update the supplier_payment table to add the missing service_confirmation_id column
"""
from sqlalchemy import create_engine, MetaData, Table, text
import os

def main():
    """Add the service_confirmation_id column to the supplier_payment table"""
    # Connect to the database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    # Create a metadata object
    metadata = MetaData()
    
    # Define the supplier_payment table
    supplier_payment = Table('supplier_payment', metadata, autoload_with=engine)
    
    # Check if the column already exists
    if 'service_confirmation_id' not in supplier_payment.columns:
        # Add the column
        print("Adding service_confirmation_id column to supplier_payment table...")
        
        # Execute the ALTER TABLE statement
        with engine.connect() as conn:
            conn.execute(text(
                'ALTER TABLE supplier_payment ADD COLUMN service_confirmation_id INTEGER, '
                'ADD CONSTRAINT fk_service_confirmation '
                'FOREIGN KEY (service_confirmation_id) REFERENCES service_confirmation(id)'
            ))
            conn.commit()
        
        print("Column added successfully.")
    else:
        print("Column service_confirmation_id already exists in supplier_payment table.")

    # Check if payment_reference column exists
    if 'payment_reference' not in supplier_payment.columns:
        print("Adding payment_reference column to supplier_payment table...")
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE supplier_payment ADD COLUMN payment_reference VARCHAR(100)'))
            conn.commit()
        print("Payment reference column added successfully.")
    else:
        print("Column payment_reference already exists in supplier_payment table.")
    
    # Check if created_at column exists
    if 'created_at' not in supplier_payment.columns:
        print("Adding created_at column to supplier_payment table...")
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE supplier_payment ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
            conn.commit()
        print("Created_at column added successfully.")
    else:
        print("Column created_at already exists in supplier_payment table.")

if __name__ == "__main__":
    main()