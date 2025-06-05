from flask import Blueprint, jsonify, request
from app.models.booking import Booking
from app.models.service import ServiceItem, Document
import json

booking_api_bp = Blueprint('booking_api', __name__, url_prefix='/booking')

@booking_api_bp.route('/<int:booking_id>/details', methods=['GET'])
def get_booking_details(booking_id):
    """API endpoint to get booking details for AJAX loading"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Format service items
    service_items = []
    for item in booking.service_items:
        # Check if this item has confirmation details
        confirmation_doc = Document.query.filter_by(
            service_item_id=item.id, 
            document_type='CONFIRMATION'
        ).first()
        
        confirmation_data = None
        if confirmation_doc:
            confirmation_data = {
                'reference': confirmation_doc.document_number
            }
            
            # Add supplier info if available
            try:
                if confirmation_doc.notes:
                    doc_data = json.loads(confirmation_doc.notes)
                    if 'supplier' in doc_data:
                        confirmation_data['supplier'] = doc_data['supplier']
            except (json.JSONDecodeError, ValueError):
                pass
                
        service_items.append({
            'id': item.id,
            'service_type': item.service_type,
            'start_date': item.start_date.strftime('%d %b'),
            'end_date': item.end_date.strftime('%d %b %Y'),
            'description': item.description,
            'amount': item.amount,
            'status': item.status,
            'confirmation': confirmation_data
        })
    
    # Return JSON response with booking details
    return jsonify({
        'id': booking.id,
        'reference_number': booking.reference_number,
        'status': booking.status,
        'created_at': booking.created_at.strftime('%d %b %Y'),
        'total_amount': booking.total_amount,
        'customer_name': booking.requester.username,
        'customer_email': booking.requester.email,
        'service_items': service_items
    })

@booking_api_bp.route('/service-types', methods=['GET'])
def get_service_types():
    """API endpoint to get list of available service types"""
    service_types = [
        {'id': 'FLIGHT', 'name': 'Flight', 'icon': 'fa-plane'},
        {'id': 'HOTEL', 'name': 'Hotel', 'icon': 'fa-hotel'},
        {'id': 'TRANSPORT', 'name': 'Transport', 'icon': 'fa-taxi'},
        {'id': 'VISA', 'name': 'Visa', 'icon': 'fa-passport'},
        {'id': 'INSURANCE', 'name': 'Insurance', 'icon': 'fa-shield-alt'}
    ]
    return jsonify(service_types)