#!/usr/bin/env python3
"""
Add hotel room distribution columns to itinerary_row table
"""

import os
import sys
from app import app, db

def add_room_distribution_columns():
    """Add room distribution columns to itinerary_row table"""
    
    with app.app_context():
        try:
            # Add the new columns
            print("Adding hotel room distribution columns...")
            
            db.engine.execute("""
                ALTER TABLE itinerary_row 
                ADD COLUMN IF NOT EXISTS hotel_single_rooms INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS hotel_double_rooms INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS hotel_triple_rooms INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS hotel_other_rooms INTEGER DEFAULT 0
            """)
            
            print("✓ Successfully added room distribution columns to itinerary_row table")
            return True
            
        except Exception as e:
            print(f"Error adding columns: {e}")
            return False

if __name__ == "__main__":
    success = add_room_distribution_columns()
    sys.exit(0 if success else 1)