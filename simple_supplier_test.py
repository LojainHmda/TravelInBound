"""
Simple test route to access suppliers without complex relationships
"""
from flask import render_template
from app import app, db
from app.models.supplier import Supplier

@app.route('/test-suppliers')
def test_suppliers():
    """Simple supplier list without complex joins"""
    try:
        suppliers = Supplier.query.all()
        return render_template('finance/suppliers.html', 
                             suppliers=suppliers,
                             title="Suppliers (Test)")
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    with app.app_context():
        suppliers = Supplier.query.all()
        print(f"Found {len(suppliers)} suppliers")
        for supplier in suppliers:
            print(f"- {supplier.name}: {supplier.get_service_types_list()}")