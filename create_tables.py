"""
Simple script to create database tables
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create the db instance
db = SQLAlchemy(model_class=Base)

# Create a minimal Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import models (adjust these imports based on your actual model structure)
from app.models.user import User, Agent
from app.models.booking import Booking, Payment
from app.models.supplier import Supplier, SupplierService, SupplierPayment, SupplierPrepaymentLine
from app.models.customer import Customer, CustomerDocument
from app.models.service import ServiceConfirmation, ServiceItem, Document
from app.models.oauth import OAuth
from app.models.finance import ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric

def main():
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        print("\nTables in database:")
        for table_name in inspector.get_table_names():
            print(f"- {table_name}")

if __name__ == "__main__":
    main()