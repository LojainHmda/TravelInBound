from app import db
from datetime import datetime

class Invoice(db.Model):
    """Invoice model to store both regular invoices and credit memos"""
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    is_credit_memo = db.Column(db.Boolean, default=False)
    referenced_invoice = db.Column(db.String(30), nullable=True)
    
    # Relationships
    booking = db.relationship('Booking', backref='invoices', foreign_keys=[booking_id])
    
    def __repr__(self):
        return f'<{"Credit Memo" if self.is_credit_memo else "Invoice"} {self.invoice_number}>'