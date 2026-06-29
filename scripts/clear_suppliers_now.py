"""
Direct script to clear ALL suppliers from the database
This will ensure the dropdown shows no options
"""
from app import create_app, db
from app.models.supplier import Supplier, SupplierService, SupplierPayment, SupplierPrepaymentLine
from sqlalchemy import text

def main():
    """Clear all supplier data"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("Clearing ALL suppliers from database...")
        print("=" * 60)
        
        try:
            # Count before
            supplier_count_before = Supplier.query.count()
            print(f"\nSuppliers before: {supplier_count_before}")
            
            if supplier_count_before == 0:
                print("No suppliers found. Database is already empty.")
                return
            
            # Use direct SQL to ensure deletion
            with db.engine.connect() as conn:
                # First, clear foreign key references
                print("\n1. Clearing foreign key references...")
                conn.execute(text("UPDATE service_confirmation SET supplier_id = NULL WHERE supplier_id IS NOT NULL"))
                conn.execute(text("UPDATE arrival_batch SET supplier_id = NULL WHERE supplier_id IS NOT NULL"))
                conn.execute(text("UPDATE departure_batch SET supplier_id = NULL WHERE supplier_id IS NOT NULL"))
                
                # Delete prepayment lines
                print("2. Deleting prepayment lines...")
                prepayment_result = conn.execute(text("DELETE FROM supplier_prepayment_line"))
                prepayment_deleted = prepayment_result.rowcount
                print(f"   Deleted {prepayment_deleted} prepayment lines")
                
                # Delete supplier payments
                print("3. Deleting supplier payments...")
                payment_result = conn.execute(text("DELETE FROM supplier_payment"))
                payment_deleted = payment_result.rowcount
                print(f"   Deleted {payment_deleted} supplier payments")
                
                # Delete supplier services
                print("4. Deleting supplier services...")
                service_result = conn.execute(text("DELETE FROM supplier_service"))
                service_deleted = service_result.rowcount
                print(f"   Deleted {service_deleted} supplier services")
                
                # Finally, delete all suppliers
                print("5. Deleting all suppliers...")
                supplier_result = conn.execute(text("DELETE FROM supplier"))
                supplier_deleted = supplier_result.rowcount
                print(f"   Deleted {supplier_deleted} suppliers")
                
                # Commit all changes
                conn.commit()
            
            # Verify deletion - use direct SQL to avoid schema issues
            with db.engine.connect() as conn:
                supplier_result = conn.execute(text("SELECT COUNT(*) FROM supplier"))
                supplier_count_after = supplier_result.scalar()
                
                service_result = conn.execute(text("SELECT COUNT(*) FROM supplier_service"))
                service_count_after = service_result.scalar()
                
                payment_result = conn.execute(text("SELECT COUNT(*) FROM supplier_payment"))
                payment_count_after = payment_result.scalar()
                
                prepayment_result = conn.execute(text("SELECT COUNT(*) FROM supplier_prepayment_line"))
                prepayment_count_after = prepayment_result.scalar()
            
            print("\n" + "=" * 60)
            print("DELETION COMPLETE!")
            print("=" * 60)
            print(f"\nRemaining records:")
            print(f"  Suppliers: {supplier_count_after}")
            print(f"  Supplier Services: {service_count_after}")
            print(f"  Supplier Payments: {payment_count_after}")
            print(f"  Prepayment Lines: {prepayment_count_after}")
            
            if supplier_count_after == 0:
                print("\nSUCCESS: All suppliers have been deleted!")
                print("  The dropdown should now show no options.")
                print("  Please refresh your browser page to see the changes.")
            else:
                print(f"\nWARNING: {supplier_count_after} suppliers still remain!")
                
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            # Don't rollback - the deletion might have succeeded before the error

if __name__ == "__main__":
    main()
