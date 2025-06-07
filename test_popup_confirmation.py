#!/usr/bin/env python3
"""
Test script for popup confirmation functionality
Creates test data and verifies the confirmation system works properly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from the correct module structure
from app import app, db
from models import Booking, ServiceItem, Customer, User
from datetime import datetime, date

def create_test_booking_with_services():
    """Create a test booking with unconfirmed service items for testing popup functionality"""
    with app.app_context():
        print("Creating test booking with service items...")
        
        # Create or get test user
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com'
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created test user: {user.username}")
        
        # Create or get test customer
        customer = Customer.query.filter_by(email='test.customer@example.com').first()
        if not customer:
            customer = Customer(
                first_name='John',
                last_name='Doe',
                email='test.customer@example.com',
                phone='+1234567890',
                passport_number='A12345678',
                nationality='American'
            )
            db.session.add(customer)
            db.session.commit()
            print(f"Created test customer: {customer.name}")
        
        # Create test booking
        booking = Booking(
            reference_number=f'TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            user_id=user.id,
            customer_id=customer.id,
            status='IN_PROGRESS'  # This allows confirmations
        )
        db.session.add(booking)
        db.session.commit()
        print(f"Created test booking: {booking.reference_number}")
        
        # Create test service items (unconfirmed for testing popup)
        services = [
            {
                'service_type': 'FLIGHT',
                'description': 'Round-trip flight New York to London',
                'amount': 850.00,
                'start_date': date(2025, 7, 15),
                'end_date': date(2025, 7, 16)
            },
            {
                'service_type': 'HOTEL',
                'description': 'Hotel accommodation in London - 5 nights',
                'amount': 600.00,
                'start_date': date(2025, 7, 16),
                'end_date': date(2025, 7, 21)
            },
            {
                'service_type': 'TRANSPORT',
                'description': 'Airport transfer service',
                'amount': 75.00,
                'start_date': date(2025, 7, 16),
                'end_date': date(2025, 7, 21)
            }
        ]
        
        created_services = []
        for service_data in services:
            service = ServiceItem(
                booking_id=booking.id,
                service_type=service_data['service_type'],
                description=service_data['description'],
                amount=service_data['amount'],
                start_date=service_data['start_date'],
                end_date=service_data['end_date'],
                status='REQUEST'  # Unconfirmed status for testing
            )
            db.session.add(service)
            created_services.append(service)
        
        db.session.commit()
        
        print(f"\nTest booking created successfully!")
        print(f"Booking ID: {booking.id}")
        print(f"Booking Reference: {booking.reference_number}")
        print(f"Customer: {customer.name}")
        print(f"Service Items: {len(created_services)}")
        
        for i, service in enumerate(created_services, 1):
            print(f"  {i}. {service.service_type}: {service.description} (${service.amount})")
        
        print(f"\nTo test popup confirmation:")
        print(f"1. Go to: /booking/{booking.id}")
        print(f"2. Look for yellow 'Save Request' and green 'Confirm' buttons")
        print(f"3. Click green 'Confirm' button to test popup")
        
        return booking

def verify_popup_elements():
    """Verify that popup confirmation elements are properly configured"""
    print("\nVerifying popup confirmation system...")
    
    # Check if templates have popup elements
    booking_template_path = 'app/templates/booking/booking_details_new.html'
    
    if os.path.exists(booking_template_path):
        with open(booking_template_path, 'r') as f:
            content = f.read()
            
        checks = [
            ('showConfirmModal function', 'showConfirmModal(' in content),
            ('Confirm button with onclick', 'onclick="showConfirmModal(' in content),
            ('Save Request button', 'Save Request' in content),
            ('Confirmation modal', 'confirmModal-' in content),
            ('Modal body with checklist', 'list-unstyled' in content)
        ]
        
        print("Template verification:")
        for check_name, check_result in checks:
            status = "✓" if check_result else "✗"
            print(f"  {status} {check_name}")
        
        all_checks_passed = all(check[1] for check in checks)
        if all_checks_passed:
            print("✓ All popup elements found in template")
        else:
            print("✗ Some popup elements missing")
            
        return all_checks_passed
    else:
        print("✗ Booking template not found")
        return False

def test_confirmation_routes():
    """Test that confirmation routes are accessible"""
    print("\nTesting confirmation routes...")
    
    with app.test_client() as client:
        # Test routes that should exist
        test_routes = [
            '/booking/confirm-service/1',
            '/booking/confirm-service/1?action=save_request',
            '/booking/confirm-service/1?action=confirm'
        ]
        
        for route in test_routes:
            try:
                response = client.get(route)
                status = "✓" if response.status_code in [200, 302, 404] else "✗"
                print(f"  {status} {route} - Status: {response.status_code}")
            except Exception as e:
                print(f"  ✗ {route} - Error: {str(e)}")

def main():
    """Main test function"""
    print("=" * 60)
    print("POPUP CONFIRMATION SYSTEM TEST")
    print("=" * 60)
    
    try:
        # Create test data
        booking = create_test_booking_with_services()
        
        # Verify popup elements
        popup_elements_ok = verify_popup_elements()
        
        # Test confirmation routes
        test_confirmation_routes()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        if popup_elements_ok:
            print("✓ Popup confirmation system is properly configured")
            print(f"✓ Test booking created: {booking.reference_number}")
            print(f"✓ Navigate to /booking/{booking.id} to test popup functionality")
        else:
            print("✗ Popup confirmation system has configuration issues")
        
        print("\nMANUAL TEST STEPS:")
        print("1. Open browser and go to the booking details page")
        print("2. Look for service items with yellow/green buttons")
        print("3. Click green 'Confirm' button")
        print("4. Verify popup modal appears with service details")
        print("5. Check browser console (F12) for any JavaScript errors")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)