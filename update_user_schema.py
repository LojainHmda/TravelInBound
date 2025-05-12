"""
Update the user table for Replit Auth integration
"""
import os
import sys
from datetime import datetime
from sqlalchemy import Column, String, DateTime, text, MetaData, Table, Integer

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def main():
    """Update the User table schema to handle Replit Auth"""
    # Get Flask app and create application context
    app = create_app()
    with app.app_context():
        try:
            # Connect to database
            conn = db.engine.connect()
            
            # Check if user table exists and if it has the required columns
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            # Begin transaction
            trans = conn.begin()
            
            # Change id type if needed
            if 'id' in columns:
                print("Altering id column type to String...")
                # Using direct SQL for migration
                conn.execute(text("ALTER TABLE \"user\" ALTER COLUMN id TYPE VARCHAR;"))
            
            # Add first_name column if it doesn't exist
            if 'first_name' not in columns:
                print("Adding first_name column...")
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN first_name VARCHAR;"))
            
            # Add last_name column if it doesn't exist
            if 'last_name' not in columns:
                print("Adding last_name column...")
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN last_name VARCHAR;"))
            
            # Add profile_image_url column if it doesn't exist
            if 'profile_image_url' not in columns:
                print("Adding profile_image_url column...")
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN profile_image_url VARCHAR;"))
            
            # Add created_at column if it doesn't exist
            if 'created_at' not in columns:
                print("Adding created_at column...")
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            
            # Add updated_at column if it doesn't exist
            if 'updated_at' not in columns:
                print("Adding updated_at column...")
                conn.execute(text(
                    "ALTER TABLE \"user\" ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
                ))
            
            # Create OAuth table
            if not inspector.has_table('oauth'):
                print("Creating OAuth table...")
                conn.execute(text("""
                    CREATE TABLE oauth (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR REFERENCES "user" (id),
                        token JSON NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        browser_session_key VARCHAR NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uq_user_browser_session_key_provider UNIQUE (user_id, browser_session_key, provider)
                    );
                """))
            
            # Commit transaction
            trans.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            if 'trans' in locals():
                trans.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    main()