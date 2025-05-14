"""
Create supplier payment records for existing confirmations
This is a one-time migration script to ensure all service confirmations have corresponding supplier payments
"""
from app import create_app
from app.models import ServiceConfirmation
from app.models.supplier import SupplierPayment
from datetime import datetime

def main():
    """Create supplier payments for all existing confirmations"""
    app = create_app()
    with app.app_context():
        from app import db
        
        # Get all service confirmations
        confirmations = ServiceConfirmation.query.all()
        created_count = 0
        
        print(f"Found {len(confirmations)} service confirmations")
        
        for confirmation in confirmations:
            # Check if a payment record exists
            existing_payment = SupplierPayment.query.filter_by(service_confirmation_id=confirmation.id).first()
            
            if not existing_payment and confirmation.supplier_id and confirmation.cost_amount:
                # Create a new supplier payment record
                supplier_payment = SupplierPayment(
                    supplier_id=confirmation.supplier_id,
                    service_confirmation_id=confirmation.id,
                    amount=confirmation.cost_amount,
                    payment_date=confirmation.payment_due_date or datetime.now().date(),
                    due_date=confirmation.payment_due_date,
                    status='PENDING',
                    notes=f"Auto-generated payment record for confirmation {confirmation.confirmation_reference}"
                )
                db.session.add(supplier_payment)
                created_count += 1
                print(f"Created payment record for confirmation #{confirmation.id}, amount: ${confirmation.cost_amount}")
        
        if created_count > 0:
            db.session.commit()
            print(f"Successfully created {created_count} new supplier payment records")
        else:
            print("No new supplier payment records needed to be created")

if __name__ == "__main__":
    main()