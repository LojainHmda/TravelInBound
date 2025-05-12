from datetime import datetime
from app import db

# Status constants
STATUS_REQUEST = 'REQUEST'     # Initial booking request state
STATUS_BOOKED = 'BOOKED'       # Confirmed booking (after invoice/payment)
STATUS_IN_PROGRESS = 'IN-PROGRESS'  # Operations started
STATUS_CONFIRMED = 'CONFIRMED'      # All services confirmed
STATUS_COMPLETED = STATUS_CONFIRMED  # Alias for backward compatibility

# Service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

# Import finance constants from app.models.finance
from app.models.finance import (
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES, EXPENSE_CATEGORY_SALARIES,
    EXPENSE_CATEGORY_MARKETING, EXPENSE_CATEGORY_INSURANCE, EXPENSE_CATEGORY_SUPPLIES,
    EXPENSE_CATEGORY_TRAVEL, EXPENSE_CATEGORY_TAXES, EXPENSE_CATEGORY_SOFTWARE,
    EXPENSE_CATEGORY_TELECOM, EXPENSE_CATEGORY_MAINTENANCE, EXPENSE_CATEGORY_OTHER,
    PAYMENT_METHOD_CASH, PAYMENT_METHOD_CREDIT_CARD, PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_CHECK, PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_OTHER,
    RECURRENCE_NONE, RECURRENCE_DAILY, RECURRENCE_WEEKLY, RECURRENCE_MONTHLY,
    RECURRENCE_QUARTERLY, RECURRENCE_YEARLY
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # Relationship with bookings
    bookings = db.relationship('Booking', backref='requester', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialty = db.Column(db.String(50))  # e.g., flights, hotels, etc.
    
    # Relationship with service items
    service_items = db.relationship('ServiceItem', backref='assigned_agent', lazy=True)
    
    def __repr__(self):
        return f'<Agent {self.name} - {self.specialty}>'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    
    # Invoice and payment tracking
    invoice_number = db.Column(db.String(20), nullable=True)
    invoice_date = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(db.String(20), default='NONE')  # NONE, PARTIAL, FULL
    payment_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    service_items = db.relationship('ServiceItem', backref='booking', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='booking', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Booking {self.reference_number}>'
    
    def calculate_total(self):
        """Calculate the total amount for this booking"""
        total = sum(item.amount for item in self.service_items)
        self.total_amount = total
        return total
    
    def can_complete(self):
        """Check if all service items are confirmed"""
        return all(item.status == STATUS_CONFIRMED for item in self.service_items)
        
    def update_payment_status(self):
        """Update payment status based on payments received"""
        import sys
        print(f"Updating payment status for booking #{self.id} - {self.reference_number}", file=sys.stderr)
        
        if not self.payments:
            print(f"  No payments found - setting status to NONE", file=sys.stderr)
            self.payment_status = 'NONE'
            return
        
        total_paid = sum(payment.amount for payment in self.payments)
        print(f"  Total paid: ${total_paid}, Total amount: ${self.total_amount}", file=sys.stderr)
        
        if total_paid >= self.total_amount:
            print(f"  Payment is FULL (${total_paid} >= ${self.total_amount})", file=sys.stderr)
            self.payment_status = 'FULL'
        elif total_paid > 0:
            print(f"  Payment is PARTIAL (${total_paid} < ${self.total_amount})", file=sys.stderr)
            self.payment_status = 'PARTIAL'
        else:
            print(f"  Payment is NONE (${total_paid})", file=sys.stderr)
            self.payment_status = 'NONE'
        
        print(f"  Updated payment_status to: {self.payment_status}", file=sys.stderr)
            
    def generate_invoice_number(self):
        """Generate a unique invoice number"""
        if not self.invoice_number:
            year = datetime.utcnow().strftime('%y')
            count = db.session.query(Booking).filter(
                Booking.invoice_number.isnot(None)
            ).count()
            self.invoice_number = f"INV-{year}-{count+1:04d}"
            self.invoice_date = datetime.utcnow()
        return self.invoice_number
        
    def generate_credit_memo_number(self):
        """Generate a unique credit memo number"""
        year = datetime.utcnow().strftime('%y')
        count = db.session.query(Booking).filter(
            Booking.invoice_number.isnot(None)
        ).count()
        return f"CM-{year}-{count+1:04d}"
        
    def generate_separate_invoice_for_items(self, service_items):
        """
        Generate a separate invoice number for specific service items
        and mark them as invoiced
        """
        # First, make sure we have service items to invoice
        if not service_items or len(service_items) == 0:
            return None
            
        # Generate a new invoice number  
        year = datetime.utcnow().strftime('%y')
        count = db.session.query(Booking).filter(
            Booking.invoice_number.isnot(None)
        ).count()
        invoice_number = f"INV-{year}-{count+1:04d}"
        invoice_date = datetime.utcnow()
        
        # Update each service item
        for item in service_items:
            item.invoice_number = invoice_number
            item.invoice_date = invoice_date
            item.is_invoiced = True
            
        return invoice_number

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Invoice related fields
    invoice_number = db.Column(db.String(20), nullable=True)
    invoice_date = db.Column(db.DateTime, nullable=True)
    is_invoiced = db.Column(db.Boolean, default=False)
    is_cancelled = db.Column(db.Boolean, default=False)
    credit_memo_number = db.Column(db.String(20), nullable=True)
    
    # Documents/confirmations for this service item
    documents = db.relationship('Document', backref='service_item', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ServiceItem {self.service_type} for Booking {self.booking_id}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # e.g., ticket, confirmation, visa
    file_path = db.Column(db.String(255))
    document_number = db.Column(db.String(100))  # e.g., ticket number, confirmation code
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Document {self.document_type} for Service {self.service_item_id}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Payment ${self.amount} for Booking {self.booking_id}>'

# Finance Module Models
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

class SupplierPayment(db.Model):
    """
    Model for tracking payments made to suppliers
    """
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, nullable=False)  # Link to supplier (assumes supplier model exists)
    service_confirmation_id = db.Column(db.Integer, nullable=True)  # For linking to service confirmations
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True)  # Payment reference 
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PAID, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SupplierPayment ${self.amount} to Supplier {self.supplier_id}>'
