"""
Create supplier payment records from document confirmation records
This is a one-time migration script to create supplier payments from document confirmations
"""
from app import create_app
from app.models import Document, ServiceItem
from app.models.supplier import SupplierPayment, Supplier
from datetime import datetime
import json

def main():
    """Create supplier payments from document confirmations"""
    app = create_app()
    with app.app_context():
        from app import db
        
        # Get all confirmation documents
        confirmation_docs = Document.query.filter_by(document_type='CONFIRMATION').all()
        created_count = 0
        
        print(f"Found {len(confirmation_docs)} confirmation documents")
        
        for doc in confirmation_docs:
            # Try to parse the notes field as JSON
            try:
                if doc.notes:
                    data = json.loads(doc.notes)
                    
                    # Check if it has cost information
                    if 'cost_amount' in data and data['cost_amount'] > 0:
                        cost_amount = float(data['cost_amount'])
                        
                        # Check if supplier exists or create one
                        supplier_name = data.get('supplier', 'Unknown Supplier')
                        supplier = Supplier.query.filter_by(name=supplier_name).first()
                        
                        if not supplier:
                            # Generate a code from the first letters of each word
                            code = ''.join([word[0].upper() for word in supplier_name.split() if word])
                            if len(code) < 2:
                                code = supplier_name[:3].upper()
                            
                            supplier = Supplier(
                                name=supplier_name,
                                code=code,
                                supplier_type=doc.service_item.service_type,
                                created_at=datetime.now(),
                                updated_at=datetime.now(),
                                is_active=True
                            )
                            db.session.add(supplier)
                            db.session.flush()  # Get ID without committing
                            print(f"Created supplier: {supplier_name} with code {code}")
                        
                        # Check if payment record exists for this document
                        existing_payment = SupplierPayment.query.filter_by(
                            supplier_id=supplier.id,
                            amount=cost_amount,
                            notes=f"Payment for confirmation document #{doc.id}"
                        ).first()
                        
                        if not existing_payment:
                            # Get payment date from the data or use today
                            payment_date = None
                            due_date = None
                            if 'payment_due_date' in data and data['payment_due_date']:
                                try:
                                    due_date = datetime.strptime(data['payment_due_date'], '%Y-%m-%d').date()
                                    payment_date = due_date
                                except ValueError:
                                    payment_date = datetime.now().date()
                                    due_date = payment_date
                            else:
                                payment_date = datetime.now().date()
                                due_date = payment_date
                            
                            # Create payment record
                            payment = SupplierPayment(
                                supplier_id=supplier.id,
                                service_confirmation_id=None,  # No actual confirmation record
                                amount=cost_amount,
                                payment_date=payment_date,
                                due_date=due_date,
                                payment_reference=doc.document_number,
                                payment_method='OTHER',
                                status='PENDING',
                                notes=f"Payment for confirmation document #{doc.id}"
                            )
                            db.session.add(payment)
                            created_count += 1
                            print(f"Created payment of ${cost_amount} for document #{doc.id}, supplier: {supplier_name}")
            except Exception as e:
                print(f"Error processing document #{doc.id}: {str(e)}")
                continue
        
        if created_count > 0:
            db.session.commit()
            print(f"Successfully created {created_count} new supplier payment records")
        else:
            print("No new supplier payment records needed to be created")

if __name__ == "__main__":
    main()