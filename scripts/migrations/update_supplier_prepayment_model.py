"""
Update the supplier payment model to include prepayment lines
"""
from app import create_app
from app.models.service import ServiceItem, ServiceConfirmation
from app.models.supplier import Supplier, SupplierPayment
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    """Add SupplierPrepaymentLine model and update schema"""
    app = create_app()
    with app.app_context():
        from app import db
        
        # Check if the table already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'supplier_prepayment_line' not in inspector.get_table_names():
            # Create the new model class
            class SupplierPrepaymentLine(db.Model):
                """Links supplier payments to specific bookings and services"""
                id = db.Column(db.Integer, primary_key=True)
                supplier_payment_id = db.Column(db.Integer, db.ForeignKey('supplier_payment.id'), nullable=False)
                booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
                service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=True)
                amount = db.Column(db.Float, nullable=False)
                notes = db.Column(db.Text)
                created_at = db.Column(db.DateTime, default=datetime.utcnow)
                updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
                
            # Add the model to the app's models module for future imports
            import importlib
            import sys
            from app import models
            setattr(models, 'SupplierPrepaymentLine', SupplierPrepaymentLine)
            setattr(sys.modules['app.models'], 'SupplierPrepaymentLine', SupplierPrepaymentLine)
            
            # Create the table
            db.create_all()
            logging.info("Created supplier_prepayment_line table")
            
            # Now add the relationship to SupplierPayment model
            from app.models.supplier import SupplierPayment
            if not hasattr(SupplierPayment, 'prepayment_lines'):
                SupplierPayment.prepayment_lines = db.relationship(
                    'SupplierPrepaymentLine', 
                    backref='payment', 
                    lazy='joined',
                    cascade="all, delete-orphan"
                )
                logging.info("Added prepayment_lines relationship to SupplierPayment model")
            
            # Also add a reference to booking model
            from app.models import Booking
            if not hasattr(Booking, 'supplier_prepayment_lines'):
                Booking.supplier_prepayment_lines = db.relationship(
                    'SupplierPrepaymentLine',
                    backref='booking',
                    lazy=True
                )
                logging.info("Added supplier_prepayment_lines relationship to Booking model")
            
            logging.info("Schema update completed")
        else:
            logging.info("SupplierPrepaymentLine table already exists")

if __name__ == "__main__":
    main()