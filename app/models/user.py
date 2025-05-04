from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # Relationships
    bookings = db.relationship('Booking', backref='requester', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialty = db.Column(db.String(50))  # e.g., flights, hotels, etc.
    
    # Relationships
    service_items = db.relationship('ServiceItem', backref='assigned_agent', lazy=True)
    
    def __repr__(self):
        return f'<Agent {self.name}>'

def create_test_data():
    """Create test data for development"""
    # Check if we already have users
    if User.query.count() > 0:
        return
    
    # Create test users
    test_user = User(username='testuser', email='test@example.com')
    test_user.set_password('password')
    
    admin_user = User(username='admin', email='admin@example.com')
    admin_user.set_password('password')
    
    # Create agents
    flight_agent = Agent(
        name='Flight Specialist',
        email='flights@example.com',
        specialty='FLIGHT'
    )
    
    hotel_agent = Agent(
        name='Hotel Specialist',
        email='hotels@example.com',
        specialty='HOTEL'
    )
    
    transport_agent = Agent(
        name='Transport Specialist',
        email='transport@example.com',
        specialty='TRANSPORT'
    )
    
    visa_agent = Agent(
        name='Visa Specialist',
        email='visa@example.com',
        specialty='VISA'
    )
    
    insurance_agent = Agent(
        name='Insurance Specialist',
        email='insurance@example.com',
        specialty='INSURANCE'
    )
    
    db.session.add_all([
        test_user, admin_user,
        flight_agent, hotel_agent, transport_agent, visa_agent, insurance_agent
    ])
    
    db.session.commit()