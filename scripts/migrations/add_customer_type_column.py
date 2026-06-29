#!/usr/bin/env python3

"""
Migration script to add customer_type column to inbound_request table
"""

import sys
from app import app, db
from sqlalchemy import text

def add_customer_type_column():
    """Add customer_type column to inbound_request table"""
    
    with app.app_context():
        try:
            # Check if column already exists
            check_query = text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'inbound_request' 
                AND column_name = 'customer_type'
            """)
            
            result = db.session.execute(check_query).scalar()
            
            if result > 0:
                print("✓ customer_type column already exists in inbound_request table")
                return True
                
            # Add the customer_type column
            alter_query = text("""
                ALTER TABLE inbound_request 
                ADD COLUMN customer_type VARCHAR(20) NOT NULL DEFAULT 'AGENCY'
            """)
            
            db.session.execute(alter_query)
            db.session.commit()
            
            print("✓ Successfully added customer_type column to inbound_request table")
            print("  - Column: customer_type VARCHAR(20) NOT NULL DEFAULT 'AGENCY'")
            
            return True
            
        except Exception as e:
            print(f"✗ Error adding customer_type column: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("Adding customer_type column to inbound_request table...")
    success = add_customer_type_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("The inbound request form now supports customer type selection:")
        print("- Agency")
        print("- Group") 
        print("- Company")
        print("- Corporate")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)