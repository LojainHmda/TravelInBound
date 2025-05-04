from app import db
from datetime import datetime
from app.models import STATUS_REQUEST, STATUS_INVOICE, STATUS_IN_PROGRESS, STATUS_COMPLETED

# Payment status constants
PAYMENT_NONE = 'NONE'
PAYMENT_PARTIAL = 'PARTIAL'
PAYMENT_FULL = 'FULL'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
    
    def __repr__(self):
        return f'<Booking {self.reference_number}>'
    
    def calculate_total(self):
        """Calculate the total amount for this booking"""
        total = sum(item.amount for item in self.service_items)
        self.total_amount = total
        return total
    
    def can_complete(self):
        """Check if all service items are fulfilled"""
        if not self.service_items:
            return False
        
        return all(item.status == STATUS_COMPLETED for item in self.service_items)
    
    def update_payment_status(self):
        """Update payment status based on payments received"""
        total_paid = sum(payment.amount for payment in self.payments)
        
        if total_paid <= 0:
            self.payment_status = PAYMENT_NONE
        elif total_paid >= self.total_amount:
            self.payment_status = PAYMENT_FULL
            # If payment is complete and status is INVOICE, automatically move to IN_PROGRESS
            if self.status == STATUS_INVOICE:
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