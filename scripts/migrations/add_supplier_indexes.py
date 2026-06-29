"""
Add database indexes to supplier table for performance optimization
This will speed up queries filtering by supplier_type and is_active
"""
from app import db, create_app
from sqlalchemy import text

def main():
    """Add indexes to supplier table"""
    app = create_app()
    with app.app_context():
        print("Starting supplier table index creation...")
        
        try:
            with db.engine.connect() as conn:
                # Check database type
                db_url = str(db.engine.url)
                is_postgres = db_url.startswith(('postgresql://', 'postgres://'))
                
                if is_postgres:
                    # PostgreSQL indexes
                    print("Creating PostgreSQL indexes...")
                    
                    # Index on supplier_type and is_active (composite index for common queries)
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_supplier_type_active 
                        ON supplier (supplier_type, is_active)
                    """))
                    
                    # Index on supplier_type alone
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_supplier_type 
                        ON supplier (supplier_type)
                    """))
                    
                    # Index on is_active
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_supplier_is_active 
                        ON supplier (is_active)
                    """))
                    
                    # Index on city (for hotel grouping)
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_supplier_city 
                        ON supplier (city)
                    """))
                    
                    # Index on name (for searches)
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_supplier_name 
                        ON supplier (name)
                    """))
                    
                else:
                    # SQLite indexes
                    print("Creating SQLite indexes...")
                    
                    # SQLite doesn't support IF NOT EXISTS for indexes, so we check first
                    inspector = db.inspect(db.engine)
                    existing_indexes = [idx['name'] for idx in inspector.get_indexes('supplier')]
                    
                    if 'idx_supplier_type_active' not in existing_indexes:
                        conn.execute(text("""
                            CREATE INDEX idx_supplier_type_active 
                            ON supplier (supplier_type, is_active)
                        """))
                    
                    if 'idx_supplier_type' not in existing_indexes:
                        conn.execute(text("""
                            CREATE INDEX idx_supplier_type 
                            ON supplier (supplier_type)
                        """))
                    
                    if 'idx_supplier_is_active' not in existing_indexes:
                        conn.execute(text("""
                            CREATE INDEX idx_supplier_is_active 
                            ON supplier (is_active)
                        """))
                    
                    if 'idx_supplier_city' not in existing_indexes:
                        conn.execute(text("""
                            CREATE INDEX idx_supplier_city 
                            ON supplier (city)
                        """))
                    
                    if 'idx_supplier_name' not in existing_indexes:
                        conn.execute(text("""
                            CREATE INDEX idx_supplier_name 
                            ON supplier (name)
                        """))
                
                conn.commit()
                print("Indexes created successfully!")
                
        except Exception as e:
            print(f"Error creating indexes: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSupplier table indexes created successfully!")
    else:
        print("\nFailed to create indexes. Check error messages above.")
