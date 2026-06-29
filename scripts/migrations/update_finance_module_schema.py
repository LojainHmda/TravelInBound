"""
Initialize the finance module schema with necessary tables and seed data
"""
import sys
from datetime import datetime, timedelta
from app import create_app, db
from app.models.finance import (
    ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric,
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES, EXPENSE_CATEGORY_SALARIES,
    EXPENSE_CATEGORY_MARKETING, EXPENSE_CATEGORY_INSURANCE, EXPENSE_CATEGORY_SUPPLIES,
    EXPENSE_CATEGORY_TRAVEL, EXPENSE_CATEGORY_TAXES, EXPENSE_CATEGORY_SOFTWARE,
    EXPENSE_CATEGORY_TELECOM, EXPENSE_CATEGORY_MAINTENANCE, EXPENSE_CATEGORY_OTHER
)

def create_expense_categories():
    """Create default expense categories"""
    categories = [
        {'name': 'Office Rent', 'code': EXPENSE_CATEGORY_RENT, 'description': 'Office space rental costs'},
        {'name': 'Utilities', 'code': EXPENSE_CATEGORY_UTILITIES, 'description': 'Electricity, water, gas bills'},
        {'name': 'Salaries', 'code': EXPENSE_CATEGORY_SALARIES, 'description': 'Staff salaries and wages'},
        {'name': 'Marketing', 'code': EXPENSE_CATEGORY_MARKETING, 'description': 'Advertising and promotion costs'},
        {'name': 'Insurance', 'code': EXPENSE_CATEGORY_INSURANCE, 'description': 'Business insurance premiums'},
        {'name': 'Office Supplies', 'code': EXPENSE_CATEGORY_SUPPLIES, 'description': 'Stationery and office materials'},
        {'name': 'Business Travel', 'code': EXPENSE_CATEGORY_TRAVEL, 'description': 'Travel for business purposes'},
        {'name': 'Taxes & Fees', 'code': EXPENSE_CATEGORY_TAXES, 'description': 'Government and regulatory fees'},
        {'name': 'Software Subscriptions', 'code': EXPENSE_CATEGORY_SOFTWARE, 'description': 'Business software licenses'},
        {'name': 'Telecommunications', 'code': EXPENSE_CATEGORY_TELECOM, 'description': 'Phone and internet services'},
        {'name': 'Maintenance', 'code': EXPENSE_CATEGORY_MAINTENANCE, 'description': 'Office repairs and maintenance'},
        {'name': 'Other Expenses', 'code': EXPENSE_CATEGORY_OTHER, 'description': 'Miscellaneous business expenses'}
    ]
    
    # Add the categories if they don't exist already
    for category_data in categories:
        existing = ExpenseCategory.query.filter_by(code=category_data['code']).first()
        if not existing:
            category = ExpenseCategory(**category_data)
            db.session.add(category)
            print(f"Added expense category: {category_data['name']}", file=sys.stderr)
        else:
            print(f"Expense category already exists: {category_data['name']}", file=sys.stderr)
    
    db.session.commit()

def main():
    """Initialize the finance module schema"""
    print("Creating finance module database schema...", file=sys.stderr)
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Seed expense categories
        create_expense_categories()
        
        print("Finance module schema creation completed.", file=sys.stderr)

if __name__ == "__main__":
    main()