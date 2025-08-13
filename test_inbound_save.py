#!/usr/bin/env python
"""Test inbound itinerary save functionality"""

import sys
sys.path.insert(0, '/home/runner/workspace')

from main import app
from models import db, User
from app.models.inbound import InboundRequest, ItineraryRow
from datetime import datetime, date

def test_save_itinerary():
    with app.app_context():
        # Get a test user
        user = User.query.first()
        if not user:
            print("No user found")
            return
        
        # Create a test inbound request if needed
        request_obj = InboundRequest.query.first()
        if not request_obj:
            request_obj = InboundRequest(
                request_number=InboundRequest.generate_request_number(),
                from_date=date(2025, 1, 1),
                to_date=date(2025, 1, 5),
                no_of_days=5,
                agent="Test Agent",
                contact_name="Test Contact",
                nationality="American",
                pax=2,
                user_id=user.id,
                total_currency='USD'
            )
            db.session.add(request_obj)
            db.session.commit()
            print(f"Created test request: {request_obj.request_number}")
        
        print(f"Testing with request: {request_obj.request_number}")
        
        # Try to save an itinerary row
        try:
            # Clear existing rows
            ItineraryRow.query.filter_by(request_id=request_obj.id).delete()
            
            # Add a test row
            row = ItineraryRow(
                request_id=request_obj.id,
                date=date(2025, 1, 1),
                description="Test activity",
                base_cost=100.0,
                cost_unit='PER_PERSON',
                currency='USD',
                flag_hotel=True
            )
            db.session.add(row)
            db.session.flush()
            
            # Try to call the auto-generate services function
            from app.routes.inbound import _auto_generate_services
            _auto_generate_services(request_obj, row)
            
            # Calculate total
            request_obj.calculate_total()
            
            db.session.commit()
            print("✓ Save successful!")
            print(f"  Total calculated: ${request_obj.total_amount}")
            
        except Exception as e:
            print(f"✗ Error saving: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    test_save_itinerary()