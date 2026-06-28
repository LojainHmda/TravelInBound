from app.extensions import db
from datetime import datetime
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED, STATUS_COMPLETED

# Payment status constants
PAYMENT_NONE = 'NONE'
PAYMENT_PARTIAL = 'PARTIAL'
PAYMENT_FULL = 'FULL'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # Link to customer
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    
    # Payment tracking
    deposit_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default=PAYMENT_NONE)
    invoice_number = db.Column(db.String(20), nullable=True)
    invoice_date = db.Column(db.DateTime, nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    service_items = db.relationship('ServiceItem', backref='booking', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='booking', lazy=True, cascade="all, delete-orphan")
    # Removed supplier_prepayment_lines relationship to fix conflict
    
    def __repr__(self):
        return f'<Booking {self.reference_number}>'
    
    def calculate_total(self):
        """Calculate the total amount for this booking"""
        total = sum(item.amount for item in self.service_items)
        self.total_amount = total
        return total
    
    def can_complete(self):
        """Check if all service items are confirmed"""
        if not self.service_items:
            return False
        
        return all(item.status == STATUS_CONFIRMED for item in self.service_items)
    
    def update_payment_status(self):
        """Update payment status based on payments received"""
        total_paid = sum(payment.amount for payment in self.payments)
        
        if total_paid <= 0:
            self.payment_status = PAYMENT_NONE
        elif total_paid >= self.total_amount:
            self.payment_status = PAYMENT_FULL
            # If payment is complete and status is BOOKED, automatically move to IN_PROGRESS
            if self.status == STATUS_BOOKED:
                self.status = STATUS_IN_PROGRESS
        else:
            self.payment_status = PAYMENT_PARTIAL
        
        return self.payment_status
    
    def generate_invoice_number(self):
        """Generate a unique invoice number"""
        if not self.invoice_number:
            prefix = "INV"
            year = datetime.utcnow().strftime("%y")
            # Use the booking ID to ensure uniqueness
            self.invoice_number = f"{prefix}-{year}-{self.id:04d}"
            self.invoice_date = datetime.utcnow()
        return self.invoice_number
    
    # Credit memo generation moved to Invoice model - no need for duplicate tracking
    
    def get_total_credits(self):
        """Get total credit memo amount for this booking"""
        from app.models.invoice import Invoice
        credit_memos = Invoice.query.filter_by(booking_id=self.id, is_credit_memo=True).all()
        return sum(abs(memo.total_amount) for memo in credit_memos)
    
    def get_credit_memos(self):
        """Get all credit memos for this booking"""
        from app.models.invoice import Invoice
        return Invoice.query.filter_by(booking_id=self.id, is_credit_memo=True).all()
    
    def generate_credit_memo_number(self):
        """Generate a unique credit memo number"""
        from datetime import datetime
        year = datetime.now().year % 100  # Last two digits of year
        booking_id = str(self.id).zfill(4)  # Pad booking ID to 4 digits
        random_suffix = str(hash(f"{self.id}-{datetime.now().isoformat()}"))[-6:]
        return f"CM-{year}-{booking_id}-{random_suffix}"


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Payment {self.id} for Booking {self.booking_id}>'