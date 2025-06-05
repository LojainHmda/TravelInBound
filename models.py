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

class Customer(db.Model):
    """Customer model for tracking individual and corporate customers"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    passport_number = db.Column(db.String(50))
    passport_expiry = db.Column(db.Date)
    date_of_birth = db.Column(db.Date)
    nationality = db.Column(db.String(100))
    customer_type = db.Column(db.String(20), default='Individual')
    company_name = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    
    @property
    def name(self):
        """Get full name by combining first and last name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_full_address(self):
        """Get complete address"""
        parts = [self.address, self.city, self.country]
        return ", ".join([part for part in parts if part]) or "No address provided"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # Link to customer
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
    customer = db.relationship('Customer', backref='bookings', lazy=True)
    
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
        
    def get_credit_memos(self):
        """Get all credit memos for this booking"""
        from app.models.invoice import Invoice
        return Invoice.query.filter_by(booking_id=self.id, is_credit_memo=True).all()
    
    def get_total_credits(self):
        """Calculate total credit memo amount"""
        credit_memos = self.get_credit_memos()
        return sum(abs(memo.total_amount) for memo in credit_memos)
    
    def get_balance_due(self):
        """Calculate balance due considering payments and credit memos"""
        total_paid = sum(payment.amount for payment in self.payments)
        total_credits = self.get_total_credits()
        return self.total_amount - total_paid - total_credits
    
    def update_payment_status(self):
        """Update payment status based on payments received and credit memos"""
        import sys
        print(f"Updating payment status for booking #{self.id} - {self.reference_number}", file=sys.stderr)
        
        total_paid = sum(payment.amount for payment in self.payments)
        total_credits = self.get_total_credits()
        balance_due = self.get_balance_due()
        
        print(f"  Total amount: ${self.total_amount}, Paid: ${total_paid}, Credits: ${total_credits}, Balance due: ${balance_due}", file=sys.stderr)
        
        if balance_due <= 0:
            print(f"  Payment is FULL (balance due: ${balance_due})", file=sys.stderr)
            self.payment_status = 'FULL'
        elif total_paid > 0 or total_credits > 0:
            print(f"  Payment is PARTIAL (balance due: ${balance_due})", file=sys.stderr)
            self.payment_status = 'PARTIAL'
        else:
            print(f"  Payment is NONE", file=sys.stderr)
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

# Import finance models
from app.models.finance import (
    ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric
)
