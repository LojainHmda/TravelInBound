"""
Migration script to add notes column to departure_batch table
Run this script once to add the notes column to the database
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('departure_batch')]
        
        if 'notes' not in columns:
            # Add the notes column using modern SQLAlchemy API
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE departure_batch ADD COLUMN notes TEXT'))
                conn.commit()
            print("[OK] Successfully added 'notes' column to departure_batch table")
        else:
            print("[OK] Column 'notes' already exists in departure_batch table")
    except Exception as e:
        print(f"Error: {e}")
        print("If the column already exists, you can ignore this error")
        import traceback
        traceback.print_exc()
