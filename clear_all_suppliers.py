"""
Script to clear all supplier data from the database
This will delete all suppliers and their related data (services, payments, etc.)
"""
from app import create_app, db
from app.models.supplier import Supplier, SupplierService, SupplierPayment, SupplierPrepaymentLine
from sqlalchemy import text

def main():
    """Clear all supplier data"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("WARNING: This will delete ALL supplier data!")
        print("=" * 60)
        
        # Count existing records
        supplier_count = Supplier.query.count()
        service_count = SupplierService.query.count()
        payment_count = SupplierPayment.query.count()
        prepayment_count = SupplierPrepaymentLine.query.count()
        
        print(f"\nCurrent data:")
        print(f"  Suppliers: {supplier_count}")
        print(f"  Supplier Services: {service_count}")
        print(f"  Supplier Payments: {payment_count}")
        print(f"  Prepayment Lines: {prepayment_count}")
        
        if supplier_count == 0:
            print("\nNo suppliers found. Nothing to delete.")
            return
        
        # Confirm deletion
        confirm = input("\nAre you sure you want to delete ALL supplier data? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled.")
            return
        
        try:
            print("\nStarting deletion...")
            
            # First, handle ServiceConfirmation references (set supplier_id to NULL)
            print("1. Clearing supplier references in service confirmations...")
            with db.engine.connect() as conn:
                conn.execute(text("UPDATE service_confirmation SET supplier_id = NULL WHERE supplier_id IS NOT NULL"))
                conn.commit()
            print("   ✓ Service confirmation references cleared")
            
            # Delete prepayment lines (they reference supplier_payment)
            print("2. Deleting prepayment lines...")
            prepayment_deleted = db.session.query(SupplierPrepaymentLine).delete()
            db.session.commit()
            print(f"   ✓ Deleted {prepayment_deleted} prepayment lines")
            
            # Delete supplier payments (cascade will handle prepayment lines, but we already deleted them)
            print("3. Deleting supplier payments...")
            payment_deleted = db.session.query(SupplierPayment).delete()
            db.session.commit()
            print(f"   ✓ Deleted {payment_deleted} supplier payments")
            
            # Delete supplier services (cascade will handle this, but doing explicitly)
            print("4. Deleting supplier services...")
            service_deleted = db.session.query(SupplierService).delete()
            db.session.commit()
            print(f"   ✓ Deleted {service_deleted} supplier services")
            
            # Finally, delete all suppliers
            print("5. Deleting suppliers...")
            supplier_deleted = db.session.query(Supplier).delete()
            db.session.commit()
            print(f"   ✓ Deleted {supplier_deleted} suppliers")
            
            print("\n" + "=" * 60)
            print("SUCCESS: All supplier data has been deleted!")
            print("=" * 60)
            
            # Verify deletion
            remaining_suppliers = Supplier.query.count()
            remaining_services = SupplierService.query.count()
            remaining_payments = SupplierPayment.query.count()
            remaining_prepayments = SupplierPrepaymentLine.query.count()
            
            print(f"\nRemaining data:")
            print(f"  Suppliers: {remaining_suppliers}")
            print(f"  Supplier Services: {remaining_services}")
            print(f"  Supplier Payments: {remaining_payments}")
            print(f"  Prepayment Lines: {remaining_prepayments}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: Failed to delete supplier data: {e}")
            print("Transaction rolled back. No data was deleted.")
            raise

if __name__ == "__main__":
    main()
