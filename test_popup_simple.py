#!/usr/bin/env python3
"""
Simple test to create test booking with unconfirmed services for popup testing
"""

import sqlite3
from datetime import datetime, date

def create_test_data():
    """Create test booking with unconfirmed service items"""
    
    # Connect to database
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    
    try:
        # Create test user if not exists
        cursor.execute("SELECT id FROM user WHERE username = 'testuser'")
        user = cursor.fetchone()
        if not user:
            cursor.execute("""
                INSERT INTO user (username, email) 
                VALUES ('testuser', 'test@example.com')
            """)
            user_id = cursor.lastrowid
        else:
            user_id = user[0]
        
        # Create test customer if not exists
        cursor.execute("SELECT id FROM customer WHERE email = 'test.customer@example.com'")
        customer = cursor.fetchone()
        if not customer:
            cursor.execute("""
                INSERT INTO customer (first_name, last_name, email, phone, created_at, updated_at) 
                VALUES ('John', 'Doe', 'test.customer@example.com', '+1234567890', ?, ?)
            """, (datetime.now(), datetime.now()))
            customer_id = cursor.lastrowid
        else:
            customer_id = customer[0]
        
        # Create test booking
        ref_number = f'TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
        cursor.execute("""
            INSERT INTO booking (reference_number, user_id, customer_id, status, created_at, updated_at) 
            VALUES (?, ?, ?, 'IN_PROGRESS', ?, ?)
        """, (ref_number, user_id, customer_id, datetime.now(), datetime.now()))
        booking_id = cursor.lastrowid
        
        # Create unconfirmed service items for testing
        services = [
            ('FLIGHT', 'Test flight for popup confirmation', 850.00),
            ('HOTEL', 'Test hotel for popup confirmation', 600.00),
            ('TRANSPORT', 'Test transport for popup confirmation', 75.00)
        ]
        
        for service_type, description, amount in services:
            cursor.execute("""
                INSERT INTO service_item 
                (booking_id, service_type, description, amount, start_date, end_date, status, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, 'REQUEST', ?, ?)
            """, (
                booking_id, service_type, description, amount,
                date(2025, 7, 15), date(2025, 7, 16),
                datetime.now(), datetime.now()
            ))
        
        conn.commit()
        
        print(f"Test booking created successfully!")
        print(f"Booking ID: {booking_id}")
        print(f"Reference: {ref_number}")
        print(f"Customer: John Doe")
        print(f"Service Items: {len(services)} unconfirmed services")
        print(f"\nTo test popup confirmation:")
        print(f"1. Go to: /booking/{booking_id}")
        print(f"2. Look for yellow 'Save Request' and green 'Confirm' buttons")
        print(f"3. Click green 'Confirm' button to test popup")
        
        return booking_id
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating test data: {e}")
        return None
    finally:
        conn.close()

def check_popup_elements():
    """Check if popup elements exist in template"""
    template_path = 'app/templates/booking/booking_details_new.html'
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        checks = [
            ('showConfirmModal function', 'showConfirmModal(' in content),
            ('Save Request button', 'Save Request' in content),
            ('Confirm button with onclick', 'onclick="showConfirmModal(' in content),
            ('Confirmation modal', 'confirmModal-' in content),
            ('Modal with checklist', 'list-unstyled' in content),
            ('JavaScript functions', 'confirmServiceFromModal' in content)
        ]
        
        print("Popup system verification:")
        all_ok = True
        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
            if not result:
                all_ok = False
        
        return all_ok
        
    except FileNotFoundError:
        print("✗ Template file not found")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("POPUP CONFIRMATION TEST")
    print("=" * 50)
    
    # Check popup elements
    popup_ok = check_popup_elements()
    
    if popup_ok:
        print("\n✓ Popup system is properly configured")
        
        # Create test data
        booking_id = create_test_data()
        
        if booking_id:
            print(f"\n✓ Test data created successfully")
            print(f"Navigate to the booking details page to test popup")
        else:
            print("\n✗ Failed to create test data")
    else:
        print("\n✗ Popup system configuration issues found")