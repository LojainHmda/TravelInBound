from datetime import datetime
from app import db

# Status constants
STATUS_REQUEST = 'REQUEST'
STATUS_INVOICE = 'INVOICE'
STATUS_IN_PROGRESS = 'IN-PROGRESS'
STATUS_COMPLETED = 'COMPLETED'

# Service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # Relationship with bookings
    bookings = db.relationship('Booking', backref='requester', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialty = db.Column(db.String(50))  # e.g., flights, hotels, etc.
    
    # Relationship with service items
    service_items = db.relationship('ServiceItem', backref='assigned_agent', lazy=True)
    
    def __repr__(self):
        return f'<Agent {self.name} - {self.specialty}>'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    
    # Relationship with service items
    service_items = db.relationship('ServiceItem', backref='booking', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Booking {self.reference_number}>'
    
    def calculate_total(self):
        """Calculate the total amount for this booking"""
        total = sum(item.amount for item in self.service_items)
        self.total_amount = total
        return total
    
    def can_complete(self):
        """Check if all service items are fulfilled"""
        return all(item.status == STATUS_COMPLETED for item in self.service_items)

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
