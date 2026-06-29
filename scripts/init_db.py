"""
Initialize the database with all tables and initial data
"""
from app import create_app, db

def main():
    """Create all database tables and initial data"""
    app = create_app()
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        from app.models import (
            User, Agent, Booking, Payment,
            Supplier, SupplierService, SupplierPayment, SupplierPrepaymentLine,
            Customer, CustomerDocument,
            ServiceConfirmation, ServiceItem, Document,
            OAuth,
            ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric
        )
        
        print("Creating all database tables...")
        db.create_all()
        print("Database tables created successfully.")
        
        # Create test data if needed
        from app.models.user import create_test_data
        print("Creating initial test data...")
        create_test_data()
        print("Initial data created successfully.")
        
        # Print table information
        print("\nDatabase tables created:")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        for table_name in inspector.get_table_names():
            print(f"- {table_name}")

if __name__ == "__main__":
    main()