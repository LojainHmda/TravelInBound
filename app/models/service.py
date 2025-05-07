from datetime import datetime
from app import db
from app.models import STATUS_REQUEST, STATUS_FULFILLED

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

class ServiceConfirmation(db.Model):
    """Model for service confirmations that links service items with suppliers and tracks costs."""
    id = db.Column(db.Integer, primary_key=True)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    confirmation_reference = db.Column(db.String(100), nullable=False)
    confirmation_date = db.Column(db.DateTime, default=datetime.utcnow)
    cost_amount = db.Column(db.Float, default=0.0)  # Amount paid to supplier
    cost_currency = db.Column(db.String(3), default='USD')
    selling_amount = db.Column(db.Float, default=0.0)  # Amount charged to customer (same as service_item.amount)
    selling_currency = db.Column(db.String(3), default='USD')
    margin = db.Column(db.Float, default=0.0)  # selling_amount - cost_amount
    margin_percentage = db.Column(db.Float, default=0.0)  # (selling_amount - cost_amount) / cost_amount * 100
    payment_due_date = db.Column(db.Date)
    is_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.Date)
    payment_reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Detailed confirmation data stored as JSON in Document.notes
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    document = db.relationship('Document', foreign_keys=[document_id])
    
    # Relationship with service item - use uselist=False to make it one-to-one
    service_item = db.relationship('ServiceItem', foreign_keys=[service_item_id], backref=db.backref('service_confirmation', uselist=False))
    
    def __repr__(self):
        return f'<ServiceConfirmation {self.confirmation_reference} for Service {self.service_item_id}>'
    
    def calculate_margin(self):
        """Calculate the margin and margin percentage"""
        if self.cost_amount > 0:
            self.margin = self.selling_amount - self.cost_amount
            self.margin_percentage = (self.margin / self.cost_amount) * 100
        return self.margin