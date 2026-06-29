"""
Create supplier payment directly for document ID 1
"""
from app import create_app, db
from app.models.supplier import SupplierPayment, Supplier
from app.models import Document
from datetime import datetime, date
import json

def main():
    """Create a supplier payment for the confirmation document"""
    app = create_app()
    with app.app_context():
        # Get the document
        doc = Document.query.get(1)
        
        if not doc:
            print("Document #1 not found")
            return
            
        print(f"Processing document #{doc.id} of type {doc.document_type}")
        
        # Try to parse the notes field as JSON
        try:
            if doc.notes:
                data = json.loads(doc.notes)
                
                # Check if it has cost information
                if 'cost_amount' in data and data['cost_amount'] > 0:
                    cost_amount = float(data['cost_amount'])
                    
                    # Get or create the supplier
                    supplier_name = data.get('supplier', 'Airline Direct')
                    supplier = Supplier.query.filter_by(name=supplier_name).first()
                    
                    if not supplier:
                        # Create a new supplier
                        supplier = Supplier(
                            name=supplier_name,
                            code="AD01",
                            supplier_type="FLIGHT",
                            default_currency="USD",
                            is_active=True,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        db.session.add(supplier)
                        db.session.flush()
                        print(f"Created supplier: {supplier_name}")
                    
                    # Create a new supplier payment
                    payment_date = datetime.now().date()
                    due_date = date.today()
                    
                    if 'payment_due_date' in data and data['payment_due_date']:
                        try:
                            due_date = datetime.strptime(data['payment_due_date'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    payment = SupplierPayment(
                        supplier_id=supplier.id,
                        amount=cost_amount,
                        payment_date=payment_date,
                        due_date=due_date,
                        status='PENDING',
                        payment_reference=doc.document_number,
                        payment_method='BANK_TRANSFER',
                        notes=f"Payment for flight confirmation document #{doc.id}"
                    )
                    
                    db.session.add(payment)
                    db.session.commit()
                    
                    print(f"Created supplier payment of ${cost_amount} for {supplier_name}")
                    return True
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            return False
            
        print("No cost information found in document")
        return False

if __name__ == "__main__":
    main()