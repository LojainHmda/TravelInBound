from datetime import datetime
from app import db
from sqlalchemy import func, desc, or_

class SupplierPrepaymentLine(db.Model):
    """Links supplier payments to specific bookings and services"""
    __tablename__ = 'supplier_prepayment_line'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_payment_id = db.Column(db.Integer, db.ForeignKey('supplier_payment.id'), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New fields added for direct cost tracking
    confirmation_reference = db.Column(db.String(100), nullable=True)
    supplier_name = db.Column(db.String(100), nullable=True)
    service_type = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(20), default='PENDING')
    invoice_reference = db.Column(db.String(100), nullable=True)
    
    # Only one relationship to avoid circular dependencies
    service_item = db.relationship('ServiceItem', backref='prepayment_lines', lazy='joined')
    
    def __repr__(self):
        return f'<SupplierPrepaymentLine {self.id}: ${self.amount:.2f} for Booking #{self.booking_id}>'

class Supplier(db.Model):
    """Supplier model for tracking vendors of travel services"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)  # Short supplier code like "BA" for British Airways
    supplier_type = db.Column(db.String(20))  # AIRLINE, HOTEL, TRANSPORT, VISA, INSURANCE
    entity_type = db.Column(db.String(20), default='COMPANY')  # COMPANY or FREELANCER

    # Contact information
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))

    # Address
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))

    # Payment information
    payment_terms = db.Column(db.String(100))  # e.g., "NET 30", "Prepaid"
    payment_method = db.Column(db.String(50))  # Payment method for freelancers
    default_currency = db.Column(db.String(3), default='USD')
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(100))
    bank_iban = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))

    # Additional information
    notes = db.Column(db.Text)
    languages = db.Column(db.Text)  # Comma-separated languages (for GUIDE suppliers)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    services = db.relationship('SupplierService', backref='supplier', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('SupplierPayment', backref='supplier', lazy=True, cascade="all, delete-orphan")
    service_confirmations = db.relationship('ServiceConfirmation', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name} ({self.code})>'
    
    def get_full_address(self):
        """Return formatted full address"""
        address_parts = [part for part in [self.address, self.city, self.country] if part]
        return ', '.join(address_parts) if address_parts else 'No address provided'
    
    def get_unpaid_balance(self):
        """Calculate outstanding balance for this supplier"""
        # Sum of all confirmation costs
        from app.models.service import ServiceConfirmation
        costs = db.session.query(func.sum(ServiceConfirmation.cost_amount)).filter(
            ServiceConfirmation.supplier_id == self.id,
            ServiceConfirmation.is_paid == False
        ).scalar() or 0

        # Sum of payments not directly linked to confirmations
        general_payments = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.supplier_id == self.id,
            SupplierPayment.service_confirmation_id == None
        ).scalar() or 0

        return costs - general_payments

    @property
    def accommodation_category(self):
        """Extract accommodation category from notes, showing only predefined values"""
        VALID_CATEGORIES = ['5-Star', '4-Star', '3-Star', 'Boutique', 'Camp', 'Airbnb', 'Other']

        if not self.notes:
            return ''

        for line in self.notes.split('\n'):
            if line.startswith('Category: '):
                value = line[len('Category: '):].strip()
                # Return if it's a valid predefined category
                if value in VALID_CATEGORIES:
                    return value
                # If value exists but is not predefined, return "Other"
                elif value:
                    return 'Other'

        return ''


class SupplierService(db.Model):
    """Services offered by a supplier"""
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    service_type = db.Column(db.String(20), nullable=False)  # FLIGHT, HOTEL, etc.
    service_name = db.Column(db.String(100), nullable=False)  # e.g. "Economy Flights", "Business Hotels"
    description = db.Column(db.Text)
    commission_rate = db.Column(db.Float)  # Percentage
    currency = db.Column(db.String(3), default='USD')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        try:
            supplier_name = self.supplier.name
        except:
            supplier_name = "Unknown"
        return f'<SupplierService {self.service_name} for {supplier_name}>'


class SupplierPayment(db.Model):
    """Payments made to suppliers"""
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    service_confirmation_id = db.Column(db.Integer, db.ForeignKey('service_confirmation.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date())
    payment_reference = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))  # BANK_TRANSFER, CREDIT_CARD, etc.
    notes = db.Column(db.Text)
    invoice_number = db.Column(db.String(100))  # Supplier invoice number
    invoice_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)  # Payment due date
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PAID, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_confirmation = db.relationship('ServiceConfirmation', backref='payments', lazy='joined')
    prepayment_lines = db.relationship('SupplierPrepaymentLine', backref='payment', lazy='joined', cascade="all, delete-orphan")
    
    @property
    def get_confirmation_cost(self):
        """Get the confirmation cost from the related service confirmation"""
        if self.service_confirmation:
            return self.service_confirmation.cost_amount
        return self.amount
        
    @property
    def service_type(self):
        """Get the service type from the related service item"""
        if self.service_confirmation and self.service_confirmation.service_item:
            return self.service_confirmation.service_item.service_type
        return None
        
    @property
    def booking(self):
        """Get the booking from the related service item"""
        if self.service_confirmation and self.service_confirmation.service_item:
            return self.service_confirmation.service_item.booking
        return None
        
    @property
    def booking_reference(self):
        """Get the booking reference from the related booking"""
        if self.booking:
            return self.booking.reference_number
        return None
    
    @property
    def get_payment_status(self):
        """Get a formatted payment status"""
        if self.status == 'PAID':
            return f"Paid on {self.payment_date.strftime('%d %b %Y')}"
        elif self.status == 'CANCELLED':
            return "Cancelled"
        elif self.due_date:
            days_to_due = (self.due_date - datetime.utcnow().date()).days
            if days_to_due < 0:
                return f"Overdue by {abs(days_to_due)} days"
            elif days_to_due == 0:
                return "Due today"
            else:
                return f"Due in {days_to_due} days"
        return "Pending"
    
    def __repr__(self):
        try:
            supplier_name = self.supplier.name
        except:
            supplier_name = "Unknown"
        return f'<SupplierPayment ${self.amount:.2f} to {supplier_name}>'