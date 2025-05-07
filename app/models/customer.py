from datetime import datetime
from app import db

class Customer(db.Model):
    """Model for customers who make booking requests."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    passport_number = db.Column(db.String(50))
    passport_expiry = db.Column(db.Date)
    date_of_birth = db.Column(db.Date)
    nationality = db.Column(db.String(50))
    customer_type = db.Column(db.String(20), default="Individual")  # Individual, Corporate, Group
    company_name = db.Column(db.String(100))  # For corporate customers
    tax_number = db.Column(db.String(50))  # For corporate customers
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with documents
    documents = db.relationship('CustomerDocument', backref='customer', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class CustomerDocument(db.Model):
    """Documents related to customers such as passports, ID cards, etc."""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # e.g., passport, visa, ID card
    file_path = db.Column(db.String(255))
    document_number = db.Column(db.String(100))  # e.g., passport number
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    issuing_country = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<CustomerDocument {self.document_type} for Customer {self.customer_id}>'