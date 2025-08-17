#!/usr/bin/env python3
"""
Simple script to create initial users for the application
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
import sqlite3

def create_users():
    """Create initial users in the database"""
    
    # Use SQLite database
    database_file = 'travel_booking.db'
    
    try:
        # Connect to database
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user'
        """)
        
        if not cursor.fetchone():
            print("ERROR: Users table does not exist. Please run create_tables.py first.")
            return False
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"Found {user_count} existing users in database")
            cursor.execute("SELECT username, email FROM user")
            existing_users = cursor.fetchall()
            print("Existing users:")
            for username, email in existing_users:
                print(f"  - {username} ({email})")
            return True
        
        # Create new users
        users_to_create = [
            ('admin', 'admin@windowsofjordan.com', 'admin123'),
            ('user', 'user@windowsofjordan.com', 'user123'),
            ('manager', 'manager@windowsofjordan.com', 'manager123')
        ]
        
        for username, email, password in users_to_create:
            password_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO user (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))
            
            print(f"Created user: {username} / {password}")
        
        # Commit changes
        conn.commit()
        print("\nUsers created successfully!")
        print("\nLogin credentials:")
        print("Username: admin / Password: admin123")
        print("Username: user / Password: user123") 
        print("Username: manager / Password: manager123")
        
        return True
        
    except Exception as e:
        print(f"ERROR creating users: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_users()
    sys.exit(0 if success else 1)