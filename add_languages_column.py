"""
Migration script to add languages column to supplier table
Run this script to add the languages field for GUIDE suppliers

Usage:
    python add_languages_column.py
"""
import os
import sys
from app import create_app, db

def add_languages_column():
    """Add languages column to supplier table"""
    app = create_app()
    
    with app.app_context():
        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        
        # Check if using SQLite or PostgreSQL
        if database_uri.startswith(("postgresql://", "postgres://")):
            # PostgreSQL migration
            print("Detected PostgreSQL database")
            try:
                from sqlalchemy import text
                # Check if column already exists
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='supplier' AND column_name='languages'
                """))
                if result.fetchone():
                    print("[OK] Column 'languages' already exists in supplier table")
                    return
                
                # Add the column
                db.session.execute(text("ALTER TABLE supplier ADD COLUMN languages TEXT"))
                db.session.commit()
                print("[OK] Successfully added 'languages' column to supplier table")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error adding column: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            # SQLite migration
            print("Detected SQLite database")
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(db.engine)
                
                # Get all columns in supplier table
                columns = [col['name'] for col in inspector.get_columns('supplier')]
                
                if 'languages' in columns:
                    print("[OK] Column 'languages' already exists in supplier table")
                    return
                
                # Add the column
                db.session.execute(text("ALTER TABLE supplier ADD COLUMN languages TEXT"))
                db.session.commit()
                print("[OK] Successfully added 'languages' column to supplier table")
                
            except Exception as e:
                db.session.rollback()
                error_msg = str(e).lower()
                if 'duplicate column name' in error_msg or 'already exists' in error_msg:
                    print("[OK] Column 'languages' already exists in supplier table")
                else:
                    print(f"[ERROR] Error adding column: {e}")
                    import traceback
                    traceback.print_exc()
                    sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Adding 'languages' column to supplier table")
    print("=" * 60)
    add_languages_column()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
