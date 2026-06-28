from app.extensions import db
from datetime import datetime
from sqlalchemy import CheckConstraint

class Invoice(db.Model):
    """Invoice model to store both regular invoices and credit memos"""
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)  # Made nullable to support inbound requests
    inbound_request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=True)  # New field for inbound requests
    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    is_credit_memo = db.Column(db.Boolean, default=False)
    referenced_invoice = db.Column(db.String(30), nullable=True)

    # Relationships
    booking = db.relationship('Booking', backref='invoices', foreign_keys=[booking_id])
    inbound_request = db.relationship('InboundRequest', backref='invoices', foreign_keys=[inbound_request_id])

    # Table constraint to ensure at least one of booking_id or inbound_request_id is set
    __table_args__ = (
        CheckConstraint('(booking_id IS NOT NULL) OR (inbound_request_id IS NOT NULL)', name='invoice_has_source'),
    )

    def __repr__(self):
        source = 'Booking' if self.booking_id else 'InboundRequest' if self.inbound_request_id else 'Unknown'
        return f'<{"Credit Memo" if self.is_credit_memo else "Invoice"} {self.invoice_number} ({source})>'