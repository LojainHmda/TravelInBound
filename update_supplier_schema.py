"""
Add missing code column to supplier table
"""
from app import db, create_app
from sqlalchemy import text

def main():
    """Add the code column to the supplier table"""
    app = create_app()
    with app.app_context():
        print("Starting supplier table update...")
        
        # Check if column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('supplier')]
        
        if 'code' in columns:
            print("Column 'code' already exists in supplier table. No action taken.")
            return
        
        # Add the column
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE supplier ADD COLUMN code VARCHAR(20)"))
            
            # Add default values - using the supplier ID as a default code
            conn.execute(text("UPDATE supplier SET code = 'SUP-' || id::text WHERE code IS NULL"))
            
            # Make the column not nullable and unique
            conn.execute(text("ALTER TABLE supplier ALTER COLUMN code SET NOT NULL"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS supplier_code_idx ON supplier (code)"))
            
            # Commit the transaction
            conn.commit()
        
        print("Column 'code' successfully added to supplier table.")

if __name__ == "__main__":
    main()