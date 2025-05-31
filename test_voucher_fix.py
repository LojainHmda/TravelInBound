#!/usr/bin/env python3
"""
Test voucher generation to fix the confirmed services issue
"""
import os
import sys
sys.path.append('.')

# Set database URL if not set
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost/db'

try:
    from main import app
    from app import db
    from models import Booking, ServiceItem
    
    print("Testing voucher status filtering...")
    
    with app.app_context():
        # Get a booking with services
        booking = Booking.query.filter(Booking.service_items.any()).first()
        
        if booking:
            print(f"Booking: {booking.reference_number}")
            print("All services:")
            for service in booking.service_items:
                print(f"  - {service.service_type}: {service.status}")
            
            confirmed_services = [s for s in booking.service_items if s.status == 'CONFIRMED']
            print(f"\nConfirmed services: {len(confirmed_services)}")
            for service in confirmed_services:
                print(f"  - {service.service_type}: {service.description} (${service.amount})")
                
            if confirmed_services:
                print("\nVoucher should show these confirmed services only")
            else:
                print("\nNo confirmed services found - voucher will be empty")
        else:
            print("No bookings with services found")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()