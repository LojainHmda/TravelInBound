#!/usr/bin/env python3
"""
Link existing bookings to customer records
This script creates customer records and links them to existing bookings
"""
import sys
sys.path.append('.')
from main import app
from app import db
from models import Customer, Booking

def link_customers():
    with app.app_context():
        # Create sample customers for existing bookings
        customers_data = [
            {
                'name': 'Ahmed Al-Rashid',
                'email': 'ahmed.rashid@email.com',
                'phone': '+970-599-123456',
                'address': 'Ramallah, Palestine',
                'customer_type': 'Individual'
            },
            {
                'name': 'Fatima Hassan',
                'email': 'fatima.hassan@email.com', 
                'phone': '+970-598-987654',
                'address': 'Gaza, Palestine',
                'customer_type': 'Individual'
            },
            {
                'name': 'Omar Khalil',
                'email': 'omar.khalil@company.com',
                'phone': '+970-567-456789',
                'address': 'Bethlehem, Palestine',
                'customer_type': 'Corporate',
                'company_name': 'Khalil Trading Co.',
                'tax_number': 'TAX-2024-001'
            }
        ]
        
        # Create customers
        customers = []
        for data in customers_data:
            customer = Customer(**data)
            db.session.add(customer)
            customers.append(customer)
        
        db.session.commit()
        print(f"Created {len(customers)} customers")
        
        # Link bookings to customers
        bookings = Booking.query.all()
        for i, booking in enumerate(bookings):
            if i < len(customers):
                booking.customer_id = customers[i].id
                print(f"Linked booking {booking.reference_number} to customer {customers[i].name}")
        
        db.session.commit()
        
        # Verify the relationships
        print("\nVerification:")
        for booking in Booking.query.all():
            customer_name = booking.customer.name if booking.customer else "No customer"
            print(f"Booking {booking.reference_number}: {customer_name}")

if __name__ == "__main__":
    link_customers()