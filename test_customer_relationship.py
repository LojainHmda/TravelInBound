#!/usr/bin/env python3
"""
Test script to verify customer-booking relationship works
"""
from app import app, db
from models import Customer, Booking, User

def test_customer_relationship():
    with app.app_context():
        # Create a test customer
        customer = Customer(
            name="Ahmed Al-Rashid",
            email="ahmed@example.com",
            phone="+970-599-123456"
        )
        db.session.add(customer)
        db.session.commit()
        
        # Get an existing booking and link it to customer
        booking = Booking.query.first()
        if booking:
            booking.customer_id = customer.id
            db.session.commit()
            
            # Test the relationship
            print(f"Booking: {booking.reference_number}")
            print(f"Customer: {booking.customer.name if booking.customer else 'No customer linked'}")
            print(f"Requester: {booking.requester.username if booking.requester else 'No requester'}")
        else:
            print("No bookings found to test")

if __name__ == "__main__":
    test_customer_relationship()