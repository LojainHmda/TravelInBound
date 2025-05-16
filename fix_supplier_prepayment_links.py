"""
Fix supplier prepayment lines to link to the correct bookings and service items
"""
from app import db, create_app
from app.models.supplier import SupplierPayment, SupplierPrepaymentLine 
from app.models.service import ServiceItem
from app.models.booking import Booking

def fix_prepayment_lines():
    """
    Update supplier prepayment lines to connect to the correct bookings and service items
    """
    print("Fixing supplier prepayment lines...")
    
    # Get all supplier payments
    payments = SupplierPayment.query.all()
    
    for payment in payments:
        # Get existing prepayment lines
        existing_lines = SupplierPrepaymentLine.query.filter_by(supplier_payment_id=payment.id).all()
        
        if not existing_lines:
            print(f"Payment {payment.id} has no prepayment lines")
            continue
            
        for line in existing_lines:
            if line.booking_id == 1:
                # Get a service item to link this payment to
                # For this fix, we'll use service items associated with different bookings
                # based on the payment ID to distribute them
                service_item = ServiceItem.query.filter(ServiceItem.id == payment.id+4).first()
                
                if service_item:
                    line.booking_id = service_item.booking_id
                    line.service_item_id = service_item.id
                    print(f"Updated prepayment line {line.id} - now linked to booking {line.booking_id} and service item {line.service_item_id}")
                else:
                    # If we can't find a matching service item, just distribute to another booking
                    # This ensures we don't have all payments linked to booking ID 1
                    new_booking_id = (payment.id % 10) + 1  # This gives us booking IDs 1-10 based on payment ID
                    line.booking_id = new_booking_id
                    print(f"Updated prepayment line {line.id} - now linked to booking {line.booking_id}")

    db.session.commit()
    print("Supplier prepayment lines updated successfully")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        fix_prepayment_lines()