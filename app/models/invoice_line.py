from datetime import datetime
from app.extensions import db


class InboundInvoiceLine(db.Model):
    """Invoice line item for an inbound request.

    Replaces admin_invoice_data / customer_invoice_data JSON blobs.
    invoice_type: 'admin' or 'customer'
    """
    __tablename__ = 'inbound_invoice_line'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer,
                           db.ForeignKey('inbound_request.id', ondelete='CASCADE'),
                           nullable=False)
    invoice_type = db.Column(db.String(20), nullable=False, default='customer')
    line_order = db.Column(db.Integer, default=0)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    line_total = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(100), nullable=True)  # hotel, transport, guide, etc.
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
