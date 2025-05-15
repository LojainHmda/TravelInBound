"""
Create supplier prepayment lines for existing supplier payments
This script creates prepayment lines to link supplier payments with bookings and service items
"""
from app import create_app
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    """Create supplier prepayment lines for existing supplier payments"""
    app = create_app()
    with app.app_context():
        from app.models import SupplierPayment, SupplierPrepaymentLine, ServiceConfirmation
        from app import db
        
        # Get all supplier payments
        payments = SupplierPayment.query.all()
        logging.info(f"Found {len(payments)} supplier payments")
        
        for payment in payments:
            # Skip if already has prepayment lines
            if payment.prepayment_lines and len(payment.prepayment_lines) > 0:
                logging.info(f"Payment {payment.id} already has prepayment lines, skipping")
                continue
                
            # Case 1: Payment with service confirmation
            if payment.service_confirmation and payment.service_confirmation.service_item:
                booking_id = payment.service_confirmation.service_item.booking_id
                service_item_id = payment.service_confirmation.service_item_id
                
                if booking_id:
                    # Create prepayment line for this confirmation
                    prepayment_line = SupplierPrepaymentLine(
                        supplier_payment_id=payment.id,
                        booking_id=booking_id,
                        service_item_id=service_item_id,
                        amount=payment.amount,
                        notes=f"Auto-created from service confirmation {payment.service_confirmation.id}"
                    )
                    db.session.add(prepayment_line)
                    logging.info(f"Created prepayment line for payment {payment.id} with booking {booking_id}")
            
            # Skip payments without confirmation or booking info
            # These will be handled separately or remain as general payments
            
        # Commit all changes
        db.session.commit()
        logging.info("Completed creating supplier prepayment lines")

if __name__ == "__main__":
    main()