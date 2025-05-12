"""
Direct SQL migration to update the database schema for Replit Auth
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def main():
    """Run direct SQL migration to update tables"""
    # Get database connection string from environment
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        return
    
    # Connect to the database
    print(f"Connecting to database: {db_url}")
    conn = psycopg2.connect(db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        cursor = conn.cursor()
        
        # Execute migrations
        print("Running migrations...")
        
        # Instead of changing the User ID type, let's add the additional columns only
        # This avoids breaking foreign key relationships
        
        # 2. Add new columns to user table
        cursor.execute("""
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE "user" ADD COLUMN first_name VARCHAR;
            EXCEPTION
                WHEN duplicate_column THEN RAISE NOTICE 'first_name column already exists';
            END;
            
            BEGIN
                ALTER TABLE "user" ADD COLUMN last_name VARCHAR;
            EXCEPTION
                WHEN duplicate_column THEN RAISE NOTICE 'last_name column already exists';
            END;
            
            BEGIN
                ALTER TABLE "user" ADD COLUMN profile_image_url VARCHAR;
            EXCEPTION
                WHEN duplicate_column THEN RAISE NOTICE 'profile_image_url column already exists';
            END;
            
            BEGIN
                ALTER TABLE "user" ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            EXCEPTION
                WHEN duplicate_column THEN RAISE NOTICE 'created_at column already exists';
            END;
            
            BEGIN
                ALTER TABLE "user" ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            EXCEPTION
                WHEN duplicate_column THEN RAISE NOTICE 'updated_at column already exists';
            END;
        END
        $$;
        """)
        
        # 3. Create oauth table if not exists
        print("Creating oauth table if not exists...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES "user" (id),
            token JSONB NOT NULL,
            provider VARCHAR(50) NOT NULL,
            browser_session_key VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_user_browser_session_key_provider UNIQUE (user_id, browser_session_key, provider)
        );
        """)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()