from datetime import datetime
from app import db

# Status constants
STATUS_PLANNED = 'PLANNED'         # Itinerary shared with customer
STATUS_PREPAID = 'PREPAID'         # Payment received
STATUS_QUEUED = 'QUEUED'           # Waiting to be processed
STATUS_PROCESSING = 'PROCESSING'   # Confirmation in progress
STATUS_CONFIRMED = 'CONFIRMED'     # All components booked
STATUS_CLOSED = 'CLOSED'           # Manually closed

# Legacy status constants (keeping for backward compatibility)
STATUS_REQUEST = 'REQUEST'     # Initial booking request state (now PLANNED)
STATUS_BOOKED = 'BOOKED'       # Confirmed booking (now PREPAID)
STATUS_IN_PROGRESS = 'IN-PROGRESS'  # Operations started (now PROCESSING)
STATUS_COMPLETED = 'COMPLETED'      # All services fulfilled (now CONFIRMED)

# Service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

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
    status = db.Column(db.String(20), default=STATUS_PLANNED)  # Changed from REQUEST to PLANNED
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
            # Update booking status to PREPAID if a payment has been made
            if self.status not in [STATUS_PROCESSING, STATUS_CONFIRMED, STATUS_CLOSED]:
                self.status = STATUS_PREPAID
                print(f"  Automatically updated booking status to {STATUS_PREPAID}", file=sys.stderr)
        elif total_paid > 0:
            print(f"  Payment is PARTIAL (${total_paid} < ${self.total_amount})", file=sys.stderr)
            self.payment_status = 'PARTIAL'
            # Update booking status to PREPAID if a payment has been made
            if self.status not in [STATUS_PROCESSING, STATUS_CONFIRMED, STATUS_CLOSED]:
                self.status = STATUS_PREPAID
                print(f"  Automatically updated booking status to {STATUS_PREPAID}", file=sys.stderr)
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
        
    def can_add_or_cancel_items(self):
        """
        Check if service items can be added or canceled based on booking status
        Returns False if the booking is in CLOSED status
        """
        return self.status != STATUS_CLOSED

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default=STATUS_PLANNED)  # Changed from REQUEST to PLANNED
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
