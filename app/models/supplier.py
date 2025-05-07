from datetime import datetime
from app import db
from app.models.service import ServiceConfirmation

class Supplier(db.Model):
    """Model for suppliers that provide services."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    website = db.Column(db.String(255))
    payment_terms = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    tax_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with service confirmations
    service_confirmations = db.relationship('ServiceConfirmation', backref='supplier', lazy=True)
    
    # Relationship with documents
    documents = db.relationship('SupplierDocument', backref='supplier', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Supplier {self.name}>'
    
    def get_balance(self):
        """Calculate the total balance (amount owed to supplier)"""
        from sqlalchemy import func
        total_amount = db.session.query(func.sum(ServiceConfirmation.cost_amount)).filter(
            ServiceConfirmation.supplier_id == self.id,
            ServiceConfirmation.is_paid == False
        ).scalar() or 0
        return total_amount

class SupplierDocument(db.Model):
    """Documents related to suppliers such as contracts, payment confirmations, etc."""
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # e.g., contract, agreement, invoice
    file_path = db.Column(db.String(255))
    document_number = db.Column(db.String(100))  # e.g., contract number
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<SupplierDocument {self.document_type} for Supplier {self.supplier_id}>'