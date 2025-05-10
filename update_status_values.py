"""
Script to update existing status values in the database to use the new status flow.
Old statuses:
- REQUEST -> PLANNED
- BOOKED -> PREPAID
- IN_PROGRESS -> PROCESSING
- FULFILLED -> CONFIRMED
- COMPLETED -> CLOSED
"""
from app import create_app, db
from app.models import Booking, ServiceItem
from app.models import (
    STATUS_PLANNED, STATUS_PREPAID, STATUS_QUEUED, STATUS_PROCESSING, 
    STATUS_CONFIRMED, STATUS_CLOSED
)

# Create the Flask application
app = create_app()

# Map old statuses to new statuses
status_mapping = {
    'REQUEST': STATUS_PLANNED,
    'INVOICE': STATUS_PLANNED,  # Handling edge case for 'INVOICE' status
    'BOOKED': STATUS_PREPAID,
    'IN_PROGRESS': STATUS_PROCESSING,
    'FULFILLED': STATUS_CONFIRMED,
    'COMPLETED': STATUS_CLOSED
}

def update_booking_statuses():
    """Update all booking statuses to use the new constants"""
    with app.app_context():
        bookings = Booking.query.all()
        updated_count = 0
        
        print(f"Found {len(bookings)} bookings to update")
        
        for booking in bookings:
            if booking.status in status_mapping:
                old_status = booking.status
                new_status = status_mapping[old_status]
                booking.status = new_status
                updated_count += 1
                print(f"Booking {booking.reference_number}: {old_status} -> {new_status}")
            
        db.session.commit()
        print(f"Updated {updated_count} booking status values")

def update_service_item_statuses():
    """Update all service item statuses to use the new constants"""
    with app.app_context():
        service_items = ServiceItem.query.all()
        updated_count = 0
        
        print(f"Found {len(service_items)} service items to update")
        
        for item in service_items:
            if item.status in status_mapping:
                old_status = item.status
                new_status = status_mapping[old_status]
                item.status = new_status
                updated_count += 1
                print(f"Service item {item.id} ({item.service_type}): {old_status} -> {new_status}")
            
        db.session.commit()
        print(f"Updated {updated_count} service item status values")

if __name__ == "__main__":
    update_booking_statuses()
    update_service_item_statuses()