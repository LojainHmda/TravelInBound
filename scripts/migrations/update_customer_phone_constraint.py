"""
Add unique constraint and not null to customer phone field
"""
from app import create_app, db
from sqlalchemy import text

def main():
    """Update the customer table to make phone field required and unique"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Updating customer table schema...")
            
            # First, update any NULL phone values to empty string to avoid constraint violation
            result = db.session.execute(text("UPDATE customer SET phone = '' WHERE phone IS NULL"))
            print(f"Updated {result.rowcount} customers with NULL phone numbers")
            
            # Add NOT NULL constraint
            db.session.execute(text("ALTER TABLE customer ALTER COLUMN phone SET NOT NULL"))
            print("Added NOT NULL constraint to phone field")
            
            # Add unique constraint
            db.session.execute(text("ALTER TABLE customer ADD CONSTRAINT uq_customer_phone UNIQUE (phone)"))
            print("Added unique constraint to phone field")
            
            db.session.commit()
            print("Schema update completed successfully!")
            
        except Exception as e:
            print(f"Error updating schema: {e}")
            db.session.rollback()
            
            # If we get constraint errors, it means there are duplicate phone numbers
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                print("\nFound duplicate phone numbers. Checking for duplicates...")
                
                # Find duplicate phone numbers
                result = db.session.execute(text("""
                    SELECT phone, COUNT(*) as count 
                    FROM customer 
                    WHERE phone IS NOT NULL AND phone != ''
                    GROUP BY phone 
                    HAVING COUNT(*) > 1
                """))
                
                duplicates = result.fetchall()
                if duplicates:
                    print("Duplicate phone numbers found:")
                    for phone, count in duplicates:
                        print(f"  {phone}: {count} customers")
                    
                    print("\nPlease manually resolve these duplicates before running the migration.")
                    print("You can query customers with duplicate phones using:")
                    print("SELECT * FROM customer WHERE phone IN (SELECT phone FROM customer GROUP BY phone HAVING COUNT(*) > 1) ORDER BY phone;")
                else:
                    print("No duplicates found. Trying alternative approach...")
                    
                    # Try to recreate the table if it's a different constraint issue
                    try:
                        db.session.execute(text("DROP INDEX IF EXISTS uq_customer_phone"))
                        db.session.execute(text("CREATE UNIQUE INDEX uq_customer_phone ON customer (phone)"))
                        db.session.commit()
                        print("Successfully added unique constraint using index approach")
                    except Exception as e2:
                        print(f"Alternative approach also failed: {e2}")

if __name__ == '__main__':
    main()