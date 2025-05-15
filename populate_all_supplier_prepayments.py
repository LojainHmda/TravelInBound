"""
Create prepayment lines for ALL supplier payments
This will associate each supplier payment with a booking through prepayment lines
"""
from app import db
from app.models import SupplierPayment, Booking, SupplierPrepaymentLine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def execute():
    # Get all bookings - we'll cycle through them to associate payments
    bookings = Booking.query.all()
    
    if not bookings:
        logging.info("No bookings found in the database. Cannot create prepayment lines.")
        return
    
    # Get all supplier payments without prepayment lines
    payments = SupplierPayment.query.filter(
        ~SupplierPayment.prepayment_lines.any()
    ).all()
    
    logging.info(f"Found {len(payments)} supplier payments without prepayment lines")
    
    # Counter to cycle through bookings
    booking_idx = 0
    booking_count = len(bookings)
    
    for payment in payments:
        # Get the next booking in rotation
        booking = bookings[booking_idx % booking_count]
        booking_idx += 1
        
        # Create prepayment line linking this payment to the booking
        prepayment = SupplierPrepaymentLine(
            supplier_payment_id=payment.id,
            booking_id=booking.id,
            amount=payment.amount,
            notes=f"Association created by data migration script"
        )
        
        db.session.add(prepayment)
        logging.info(f"Created prepayment line: Payment {payment.id} -> Booking {booking.reference_number}")
    
    # Commit all the changes
    db.session.commit()
    logging.info(f"Successfully created {len(payments)} prepayment lines")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        execute()