"""
Add supplier services to allow suppliers to offer multiple service types
This will make suppliers appear in confirmation lists for all their service types
"""

from app import create_app
from app.models.supplier import Supplier, SupplierService
from app import db

def add_supplier_services():
    """Add sample supplier services to existing suppliers"""
    app = create_app()
    
    with app.app_context():
        print("Adding supplier services...")
        
        # Get all existing suppliers
        suppliers = Supplier.query.all()
        
        if not suppliers:
            print("No suppliers found. Please add suppliers first.")
            return
        
        # Sample service configurations for different suppliers
        supplier_services_config = [
            {
                'name_contains': 'Qatar',
                'services': [
                    {'type': 'FLIGHT', 'name': 'International Flights', 'commission': 5.0},
                    {'type': 'HOTEL', 'name': 'Hotel Bookings', 'commission': 10.0},
                ]
            },
            {
                'name_contains': 'Emirates',
                'services': [
                    {'type': 'FLIGHT', 'name': 'Premium Flights', 'commission': 7.0},
                    {'type': 'TRANSPORT', 'name': 'Airport Transfers', 'commission': 15.0},
                ]
            },
            {
                'name_contains': 'Etihad',
                'services': [
                    {'type': 'FLIGHT', 'name': 'Regional Flights', 'commission': 6.0},
                    {'type': 'VISA', 'name': 'Visa Services', 'commission': 20.0},
                ]
            },
            {
                'name_contains': 'Barcelo',
                'services': [
                    {'type': 'HOTEL', 'name': 'Luxury Hotels', 'commission': 12.0},
                    {'type': 'TRANSPORT', 'name': 'Hotel Transfers', 'commission': 10.0},
                ]
            },
            {
                'name_contains': 'Jumeirah',
                'services': [
                    {'type': 'HOTEL', 'name': 'Resort Accommodations', 'commission': 15.0},
                    {'type': 'TRANSPORT', 'name': 'Luxury Transfers', 'commission': 20.0},
                ]
            },
        ]
        
        services_added = 0
        
        for supplier in suppliers:
            # Check if this supplier matches any configuration
            matching_config = None
            for config in supplier_services_config:
                if config['name_contains'].lower() in supplier.name.lower():
                    matching_config = config
                    break
            
            if matching_config:
                # Add configured services
                for service_config in matching_config['services']:
                    # Check if service already exists
                    existing_service = SupplierService.query.filter_by(
                        supplier_id=supplier.id,
                        service_type=service_config['type']
                    ).first()
                    
                    if not existing_service:
                        new_service = SupplierService(
                            supplier_id=supplier.id,
                            service_type=service_config['type'],
                            service_name=service_config['name'],
                            description=f"{service_config['name']} provided by {supplier.name}",
                            commission_rate=service_config['commission'],
                            currency='USD'
                        )
                        db.session.add(new_service)
                        services_added += 1
                        print(f"Added {service_config['type']} service for {supplier.name}")
            else:
                # Add default service based on supplier type
                if supplier.supplier_type and not supplier.services:
                    default_service = SupplierService(
                        supplier_id=supplier.id,
                        service_type=supplier.supplier_type,
                        service_name=f"{supplier.supplier_type.title()} Services",
                        description=f"Primary {supplier.supplier_type.lower()} services",
                        commission_rate=10.0,
                        currency='USD'
                    )
                    db.session.add(default_service)
                    services_added += 1
                    print(f"Added default {supplier.supplier_type} service for {supplier.name}")
        
        # Also add some multi-service suppliers
        multi_service_suppliers = [
            {
                'name': 'Global Travel Solutions',
                'code': 'GTS',
                'supplier_type': 'TRAVEL_AGENCY',
                'services': [
                    {'type': 'FLIGHT', 'name': 'Flight Bookings', 'commission': 5.0},
                    {'type': 'HOTEL', 'name': 'Hotel Reservations', 'commission': 10.0},
                    {'type': 'TRANSPORT', 'name': 'Ground Transportation', 'commission': 15.0},
                    {'type': 'VISA', 'name': 'Visa Processing', 'commission': 25.0},
                    {'type': 'INSURANCE', 'name': 'Travel Insurance', 'commission': 30.0},
                ]
            },
            {
                'name': 'Middle East Travel Hub',
                'code': 'METH',
                'supplier_type': 'TRAVEL_AGENCY',
                'services': [
                    {'type': 'FLIGHT', 'name': 'Regional Flights', 'commission': 4.0},
                    {'type': 'HOTEL', 'name': 'Business Hotels', 'commission': 8.0},
                    {'type': 'TRANSPORT', 'name': 'Corporate Transport', 'commission': 12.0},
                ]
            }
        ]
        
        for supplier_config in multi_service_suppliers:
            # Check if supplier already exists
            existing_supplier = Supplier.query.filter_by(code=supplier_config['code']).first()
            
            if not existing_supplier:
                # Create the supplier
                new_supplier = Supplier(
                    name=supplier_config['name'],
                    code=supplier_config['code'],
                    supplier_type=supplier_config['supplier_type'],
                    email=f"info@{supplier_config['code'].lower()}.com",
                    phone="+970-2-XXX-XXXX",
                    payment_terms="NET 30",
                    default_currency="USD",
                    notes="Multi-service travel supplier",
                    is_active=True
                )
                db.session.add(new_supplier)
                db.session.flush()  # Get the ID
                
                # Add all services
                for service_config in supplier_config['services']:
                    new_service = SupplierService(
                        supplier_id=new_supplier.id,
                        service_type=service_config['type'],
                        service_name=service_config['name'],
                        description=f"{service_config['name']} by {supplier_config['name']}",
                        commission_rate=service_config['commission'],
                        currency='USD'
                    )
                    db.session.add(new_service)
                    services_added += 1
                
                print(f"Created multi-service supplier: {supplier_config['name']}")
        
        try:
            db.session.commit()
            print(f"Successfully added {services_added} supplier services!")
            
            # Print summary
            print("\nSupplier Services Summary:")
            all_suppliers = Supplier.query.all()
            for supplier in all_suppliers:
                if supplier.services:
                    service_types = [s.service_type for s in supplier.services]
                    print(f"- {supplier.name}: {', '.join(service_types)}")
                else:
                    print(f"- {supplier.name}: No services configured")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding supplier services: {str(e)}")

if __name__ == '__main__':
    add_supplier_services()