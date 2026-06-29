"""
Simple migration script to add notes column to arrival_batch table
Uses direct SQLite connection to avoid Flask app import issues
"""
import sqlite3
import os

# Find the database file
db_path = os.path.join('instance', 'app.db')
if not os.path.exists(db_path):
    # Try alternative locations
    db_path = 'app.db'
    if not os.path.exists(db_path):
        print("Error: Could not find database file")
        print("Please specify the database path manually")
        exit(1)

print(f"Connecting to database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(arrival_batch)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'notes' in columns:
        print("[OK] Column 'notes' already exists in arrival_batch table")
    else:
        # Add the notes column
        cursor.execute("ALTER TABLE arrival_batch ADD COLUMN notes TEXT")
        conn.commit()
        print("[OK] Successfully added 'notes' column to arrival_batch table")
    
    # Verify the column was added
    cursor.execute("PRAGMA table_info(arrival_batch)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in arrival_batch: {', '.join(columns)}")
    
    conn.close()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
