from datetime import datetime
from app import db
from app.models.user import User, Agent
from app.models.customer import Customer
from app.models.booking import Booking

# Status constants
STATUS_REQUEST = 'REQUEST'     # Initial booking request state
STATUS_BOOKED = 'BOOKED'       # Confirmed booking (after invoice/payment)
STATUS_IN_PROGRESS = 'IN-PROGRESS'  # Operations started
STATUS_CONFIRMED = 'CONFIRMED'      # All services confirmed
STATUS_COMPLETED = STATUS_CONFIRMED  # Alias for backward compatibility

# Service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

# Import finance constants from app.models.finance
from app.models.finance import (
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES, EXPENSE_CATEGORY_SALARIES,
    EXPENSE_CATEGORY_MARKETING, EXPENSE_CATEGORY_INSURANCE, EXPENSE_CATEGORY_SUPPLIES,
    EXPENSE_CATEGORY_TRAVEL, EXPENSE_CATEGORY_TAXES, EXPENSE_CATEGORY_SOFTWARE,
    EXPENSE_CATEGORY_TELECOM, EXPENSE_CATEGORY_MAINTENANCE, EXPENSE_CATEGORY_OTHER,
    PAYMENT_METHOD_CASH, PAYMENT_METHOD_CREDIT_CARD, PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_CHECK, PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_OTHER,
    RECURRENCE_NONE, RECURRENCE_DAILY, RECURRENCE_WEEKLY, RECURRENCE_MONTHLY,
    RECURRENCE_QUARTERLY, RECURRENCE_YEARLY
)

# User model is now imported from app.models.user to avoid conflicts

# Agent model is now imported from app.models.user to avoid conflicts

# Customer model is now imported from app.models.customer to avoid conflicts

# Booking model is now imported from app.models.booking to avoid conflicts

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

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Payment ${self.amount} for Booking {self.booking_id}>'

# Import finance models
from app.models.finance import (
    ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric
)
