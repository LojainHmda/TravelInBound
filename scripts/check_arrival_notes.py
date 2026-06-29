"""
Diagnostic script to check arrival notes in the database
Run this to verify notes are being saved correctly
"""
import sqlite3
import os
import sys

# Find the database file
db_path = os.path.join('instance', 'app.db')
if not os.path.exists(db_path):
    db_path = 'app.db'
    if not os.path.exists(db_path):
        print("Error: Could not find database file")
        sys.exit(1)

print(f"Connecting to database: {db_path}\n")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if notes column exists
    cursor.execute("PRAGMA table_info(arrival_batch)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'notes' not in columns:
        print("ERROR: 'notes' column does NOT exist in arrival_batch table!")
        print(f"Current columns: {', '.join(columns)}")
        sys.exit(1)
    else:
        print("[OK] 'notes' column exists in arrival_batch table")
    
    # Get all arrival batches with their notes
    cursor.execute("""
        SELECT id, request_id, arrival_date, arrival_point, notes, 
               CASE WHEN notes IS NULL THEN 'NULL' 
                    WHEN notes = '' THEN 'EMPTY STRING'
                    ELSE 'HAS VALUE'
               END as notes_status
        FROM arrival_batch 
        ORDER BY id DESC 
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("\nNo arrival batches found in database")
    else:
        print(f"\nFound {len(rows)} recent arrival batch(es):\n")
        print(f"{'ID':<6} {'Request ID':<12} {'Date':<12} {'Point':<30} {'Notes Status':<15} {'Notes Value'}")
        print("-" * 100)
        
        for row in rows:
            arrival_id, request_id, arrival_date, arrival_point, notes, notes_status = row
            notes_display = notes if notes else '(empty)'
            if len(notes_display) > 40:
                notes_display = notes_display[:37] + "..."
            print(f"{arrival_id:<6} {request_id:<12} {str(arrival_date):<12} {(arrival_point or '-')[:28]:<30} {notes_status:<15} {notes_display}")
        
        # Check specific arrival if ID provided
        if len(sys.argv) > 1:
            arrival_id = sys.argv[1]
            cursor.execute("SELECT notes FROM arrival_batch WHERE id = ?", (arrival_id,))
            result = cursor.fetchone()
            if result:
                notes_value = result[0]
                print(f"\n=== Details for Arrival ID {arrival_id} ===")
                print(f"Notes value: {repr(notes_value)}")
                print(f"Notes type: {type(notes_value)}")
                print(f"Notes length: {len(notes_value) if notes_value else 0}")
            else:
                print(f"\nArrival ID {arrival_id} not found")
    
    conn.close()
    print("\n[OK] Database check completed")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
