"""
Simple script to verify the database connection and populate minimal test data
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys

# Create minimal Flask app
app = Flask(__name__)

# Configure database connection
database_url = os.environ.get("DATABASE_URL")
print(f"Using database URL: {database_url.split('@')[0].split(':')[0]}:***@{database_url.split('@')[1]}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define minimal User model for testing
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)

def main():
    """Check database connection and add a test user"""
    with app.app_context():
        try:
            # Try creating tables
            print("Creating tables...")
            db.create_all()
            print("Tables created successfully!")
            
            # Check if User table exists and has data
            user_count = User.query.count()
            print(f"Found {user_count} users in the database")
            
            # Add a test user if none exist
            if user_count == 0:
                print("Adding a test user...")
                test_user = User(username="testuser", email="test@example.com")
                db.session.add(test_user)
                db.session.commit()
                print("Test user added successfully!")
                
            # List all users
            print("\nUsers in database:")
            for user in User.query.all():
                print(f"- {user.username} ({user.email})")
                
            # List all tables in the database
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            print("\nTables in database:")
            for table_name in inspector.get_table_names():
                print(f"- {table_name}")
                
            return True
            
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nDatabase connection successful!")
    else:
        print("\nDatabase connection failed!")
        sys.exit(1)