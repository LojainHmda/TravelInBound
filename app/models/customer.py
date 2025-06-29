from datetime import datetime
from app import db

class Customer(db.Model):
    """Customer model for tracking individual and corporate customers"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    
    # Personal information
    passport_number = db.Column(db.String(50))
    passport_expiry = db.Column(db.Date)
    date_of_birth = db.Column(db.Date)
    nationality = db.Column(db.String(50))
    
    # Business information
    customer_type = db.Column(db.String(20), default='Individual')  # Individual, Corporate, Group
    company_name = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))
    
    # Additional information
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Property to get full name
    @property
    def name(self):
        """Return full name (first + last)"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    # Relationships
    documents = db.relationship('CustomerDocument', backref='customer', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'
    
    def get_full_address(self):
        """Return formatted full address"""
        address_parts = [part for part in [self.address, self.city, self.country] if part]
        return ', '.join(address_parts) if address_parts else 'No address provided'


class CustomerDocument(db.Model):
    """Customer documents like passports, visas, etc."""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # PASSPORT, VISA, ID_CARD, etc.
    document_number = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    issuing_country = db.Column(db.String(50))
    notes = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomerDocument {self.document_type} {self.document_number}>'
    
    @property
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return self.expiry_date < datetime.utcnow().date()
        return False
    
    @property
    def days_to_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            delta = self.expiry_date - datetime.utcnow().date()
            return delta.days
        return None