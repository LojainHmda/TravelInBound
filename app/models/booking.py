from app import db
from datetime import datetime
from app.models import STATUS_REQUEST, STATUS_COMPLETED

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    
    # Relationships
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
        if not self.service_items:
            return False
        
        return all(item.status == STATUS_COMPLETED for item in self.service_items)