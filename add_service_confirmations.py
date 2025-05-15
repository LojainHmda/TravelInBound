"""
Create test service confirmations to link supplier payments with bookings
"""
from datetime import datetime, date, timedelta
import random
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add the current directory to the path so we can import app modules
sys.path.append(os.getcwd())

from app import create_app
from app.models.service import ServiceItem, ServiceConfirmation
from app.models.supplier import Supplier, SupplierPayment

def main():
    """Create sample service confirmations for existing service items"""
    from app import create_app
    from app.models.service import ServiceItem, ServiceConfirmation
    from app.models.supplier import Supplier, SupplierPayment
    from app import db
    
    app = create_app()
    with app.app_context():
        from app import db
        
        # Get all service items without confirmations
        service_items = ServiceItem.query.outerjoin(
            ServiceConfirmation,
            ServiceItem.id == ServiceConfirmation.service_item_id
        ).filter(
            ServiceConfirmation.id == None
        ).all()
        
        if not service_items:
            print("No service items found without confirmations.")
            return
            
        print(f"Found {len(service_items)} service items without confirmations")
        
        # Get available suppliers
        suppliers = Supplier.query.all()
        if not suppliers:
            # Create a test supplier if none exists
            test_supplier = Supplier(
                name="Test Travel Agency",
                code="TTA",
                supplier_type="AIRLINE",
                email="test@example.com",
                phone="+1234567890",
                payment_terms="NET 30",
                default_currency="USD"
            )
            db.session.add(test_supplier)
            db.session.commit()
            suppliers = [test_supplier]
            print("Created a test supplier")
        
        # Create confirmations for each service item
        created_count = 0
        for item in service_items:
            supplier = random.choice(suppliers)
            
            # Create a confirmation record
            confirmation = ServiceConfirmation(
                service_item_id=item.id,
                supplier_id=supplier.id,
                confirmation_reference=f"CONF-{random.randint(10000, 99999)}",
                cost_amount=item.amount * 0.7,  # 70% of selling price is cost
                cost_currency="USD",
                payment_due_date=date.today() + timedelta(days=30),
                selling_amount=item.amount,
                selling_currency="USD",
                confirmation_date=datetime.now(),
                notes=f"Auto-generated confirmation for {item.service_type}"
            )
            db.session.add(confirmation)
            created_count += 1
            
            # Create a supplier payment record linked to this confirmation
            payment = SupplierPayment(
                supplier_id=supplier.id,
                service_confirmation_id=confirmation.id,
                amount=confirmation.cost_amount,
                payment_date=date.today(),
                payment_reference=f"PAY-{random.randint(10000, 99999)}",
                payment_method="BANK_TRANSFER",
                notes=f"Auto-generated payment for {item.service_type}",
                invoice_number=f"INV-{random.randint(10000, 99999)}",
                invoice_date=date.today() - timedelta(days=5),
                due_date=confirmation.payment_due_date,
                status='PENDING'
            )
            db.session.add(payment)
            
        db.session.commit()
        print(f"Successfully created {created_count} service confirmations with payments")

if __name__ == "__main__":
    main()