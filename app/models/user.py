from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)
    
    # Role-based access control
    role = db.Column(db.String(50), nullable=False, default='ops_manager')  # admin, ops_manager
    active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='requester', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
        
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        role_permissions = {
            'admin': ['all'],
            'ops_manager': ['bookings', 'customers', 'suppliers', 'operations', 'dashboard']
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return 'all' in user_permissions or permission in user_permissions
    
    def can_access_finance(self):
        """Check if user can access finance dashboard"""
        return self.role == 'admin'
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

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
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@arabtravelgroup.com',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    admin_user.set_password('admin123')
    
    # Create ops manager user
    ops_user = User(
        username='opsmanager',
        email='ops@arabtravelgroup.com',
        first_name='Operations',
        last_name='Manager',
        role='ops_manager'
    )
    ops_user.set_password('ops123')
    
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
        admin_user, ops_user,
        flight_agent, hotel_agent, transport_agent, visa_agent, insurance_agent
    ])
    
    db.session.commit()