from datetime import datetime
from app import db

# Expense categories
EXPENSE_CATEGORY_RENT = 'RENT'                  # Office rent
EXPENSE_CATEGORY_UTILITIES = 'UTILITIES'        # Utilities
EXPENSE_CATEGORY_SALARIES = 'SALARIES'          # Staff salaries
EXPENSE_CATEGORY_MARKETING = 'MARKETING'        # Marketing and advertising
EXPENSE_CATEGORY_INSURANCE = 'INSURANCE'        # Business insurance
EXPENSE_CATEGORY_SUPPLIES = 'SUPPLIES'          # Office supplies
EXPENSE_CATEGORY_TRAVEL = 'TRAVEL'              # Business travel
EXPENSE_CATEGORY_TAXES = 'TAXES'                # Taxes and fees
EXPENSE_CATEGORY_SOFTWARE = 'SOFTWARE'          # Software subscriptions
EXPENSE_CATEGORY_TELECOM = 'TELECOM'            # Phone and internet
EXPENSE_CATEGORY_MAINTENANCE = 'MAINTENANCE'    # Maintenance and repairs
EXPENSE_CATEGORY_OTHER = 'OTHER'                # Miscellaneous expenses

# Expense payment methods
PAYMENT_METHOD_CASH = 'CASH'
PAYMENT_METHOD_CREDIT_CARD = 'CREDIT_CARD'
PAYMENT_METHOD_BANK_TRANSFER = 'BANK_TRANSFER'
PAYMENT_METHOD_CHECK = 'CHECK'
PAYMENT_METHOD_PAYPAL = 'PAYPAL'
PAYMENT_METHOD_OTHER = 'OTHER'

# Expense recurrence types
RECURRENCE_NONE = 'NONE'           # One-time expense
RECURRENCE_DAILY = 'DAILY'
RECURRENCE_WEEKLY = 'WEEKLY'  
RECURRENCE_MONTHLY = 'MONTHLY'
RECURRENCE_QUARTERLY = 'QUARTERLY'
RECURRENCE_YEARLY = 'YEARLY'

class ExpenseCategory(db.Model):
    """
    Model for expense categories to categorize operational expenses
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False, unique=True)  # Category code (e.g., RENT, UTILITIES)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'

class Expense(db.Model):
    """
    Model for tracking operational expenses
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    date_incurred = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)  # Invoice/receipt number
    vendor_name = db.Column(db.String(100), nullable=True)
    is_paid = db.Column(db.Boolean, default=False)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20), default=RECURRENCE_NONE)
    recurrence_ends = db.Column(db.Date, nullable=True)
    parent_expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=True)  # For recurring expenses
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recurring_expenses = db.relationship('Expense', backref=db.backref('parent_expense', remote_side=[id]), lazy=True)
    attachments = db.relationship('ExpenseAttachment', backref='expense', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Expense {self.title} - ${self.amount}>'

class ExpenseAttachment(db.Model):
    """
    Model for storing attachments related to expenses (receipts, invoices, etc.)
    """
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)  # MIME type
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExpenseAttachment {self.file_name} for Expense {self.expense_id}>'

class FinancialMetric(db.Model):
    """
    Model for storing calculated financial metrics for reporting
    """
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FinancialMetric {self.metric_name}: {self.metric_value} ({self.period_start} to {self.period_end})>'