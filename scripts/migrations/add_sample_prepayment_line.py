"""
Add a sample prepayment line for testing
"""
from app import db
from app.models import SupplierPayment, SupplierPrepaymentLine, Booking, ServiceItem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def add_sample_prepayment():
    """Add a sample prepayment line for the first supplier payment without one"""
    # Find a payment without prepayment lines
    payment = SupplierPayment.query.filter(
        ~SupplierPayment.prepayment_lines.any()
    ).first()
    
    if not payment:
        logging.info("No supplier payments without prepayment lines found")
        return
    
    # Find an available booking
    booking = Booking.query.first()
    
    if not booking:
        logging.info("No bookings found")
        return
    
    # Find an available service item
    service_item = ServiceItem.query.filter_by(booking_id=booking.id).first()
    
    # Create the prepayment line
    prepayment = SupplierPrepaymentLine(
        supplier_payment_id=payment.id,
        booking_id=booking.id,
        service_item_id=service_item.id if service_item else None,
        amount=payment.amount,
        notes="Sample prepayment line for testing"
    )
    
    db.session.add(prepayment)
    db.session.commit()
    
    logging.info(f"Created sample prepayment line for payment {payment.id} with booking {booking.id}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        add_sample_prepayment()