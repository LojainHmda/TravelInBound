from datetime import datetime
from app import db

# Constants for service item status
STATUS_REQUEST = 'REQUEST'
STATUS_BOOKED = 'BOOKED'
STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_CONFIRMED = 'CONFIRMED'  # New standard term
STATUS_COMPLETED = 'COMPLETED'  # Consider deprecating in favor of STATUS_CONFIRMED

# Service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

class ServiceItem(db.Model):
    """Service items for bookings"""
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
    """Document attachments for service items"""
    id = db.Column(db.Integer, primary_key=True)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # e.g., ticket, confirmation, visa
    file_path = db.Column(db.String(255))
    document_number = db.Column(db.String(100))  # e.g., ticket number, confirmation code
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Document {self.document_type} for ServiceItem {self.service_item_id}>'

class ServiceConfirmation(db.Model):
    """Confirmation records for service bookings with supplier details and costs"""
    id = db.Column(db.Integer, primary_key=True)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    confirmation_reference = db.Column(db.String(100), nullable=False)  # Supplier booking reference
    
    # Cost information (what we pay to the supplier)
    cost_amount = db.Column(db.Float, nullable=False)
    cost_currency = db.Column(db.String(3), default='USD')
    payment_due_date = db.Column(db.Date)
    is_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.Date)
    
    # Internal information
    selling_amount = db.Column(db.Float, nullable=True)  # Service item amount (what we charge the customer)
    selling_currency = db.Column(db.String(3), default='USD')
    confirmation_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to service item
    service_item = db.relationship('ServiceItem', backref='confirmation', uselist=False)
    
    def __repr__(self):
        return f'<ServiceConfirmation {self.confirmation_reference} for service #{self.service_item_id}>'
    
    @property
    def margin(self):
        """Calculate margin between selling price and cost"""
        if self.cost_amount and self.cost_amount > 0 and self.selling_amount:
            return self.selling_amount - self.cost_amount
        return 0
    
    @property
    def margin_percentage(self):
        """Calculate margin as percentage of cost"""
        if self.cost_amount and self.cost_amount > 0 and self.selling_amount:
            return ((self.selling_amount - self.cost_amount) / self.cost_amount) * 100
        return 0
    
    @property
    def payment_status_text(self):
        """Return human-readable payment status"""
        if self.is_paid:
            return f"Paid on {self.payment_date.strftime('%d %b %Y')}"
        elif self.payment_due_date:
            days_to_due = (self.payment_due_date - datetime.utcnow().date()).days
            if days_to_due < 0:
                return f"Overdue by {abs(days_to_due)} days"
            elif days_to_due == 0:
                return "Due today"
            else:
                return f"Due in {days_to_due} days"
        else:
            return "Not paid"