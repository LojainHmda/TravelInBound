from flask import Blueprint, jsonify, request, render_template
from app.models.service import ServiceItem, Document
import json

service_api_bp = Blueprint('service_api', __name__, url_prefix='/service')

@service_api_bp.route('/<int:item_id>/details', methods=['GET'])
def get_service_details(item_id):
    """API endpoint to get service item details including confirmation form HTML"""
    service_item = ServiceItem.query.get_or_404(item_id)
    
    # Get confirmation document if available
    confirmation_doc = Document.query.filter_by(
        service_item_id=service_item.id, 
        document_type='CONFIRMATION'
    ).first()
    
    # Prepare confirmation data
    confirmation_data = {}
    if confirmation_doc:
        try:
            if confirmation_doc.notes:
                confirmation_data = json.loads(confirmation_doc.notes)
                # Add confirmation reference number
                confirmation_data['confirmation_reference'] = confirmation_doc.document_number
        except (json.JSONDecodeError, TypeError) as e:
            confirmation_data = {}
    
    # Determine which form template to use
    if service_item.service_type == 'FLIGHT':
        form_template = 'booking/forms/confirm_flight_form.html'
    elif service_item.service_type == 'HOTEL':
        form_template = 'booking/forms/confirm_hotel_form.html'
    elif service_item.service_type == 'TRANSPORT':
        form_template = 'booking/forms/confirm_transport_form.html'
    elif service_item.service_type == 'VISA':
        form_template = 'booking/forms/confirm_visa_form.html'
    elif service_item.service_type == 'INSURANCE':
        form_template = 'booking/forms/confirm_insurance_form.html'
    else:
        form_template = 'booking/forms/confirm_generic_form.html'
    
    # Render the form template to HTML
    form_html = render_template(
        form_template,
        service_item=service_item,
        confirmation_data=confirmation_data,
        confirmation_doc=confirmation_doc,
        inline_form=True  # Flag to indicate this is for inline display
    )
    
    # Return both the data and the rendered form HTML
    return jsonify({
        'id': service_item.id,
        'booking_id': service_item.booking_id,
        'service_type': service_item.service_type,
        'description': service_item.description,
        'start_date': service_item.start_date.strftime('%Y-%m-%d'),
        'end_date': service_item.end_date.strftime('%Y-%m-%d'),
        'amount': service_item.amount,
        'status': service_item.status,
        'has_confirmation': confirmation_doc is not None,
        'confirmation_reference': confirmation_doc.document_number if confirmation_doc else None,
        'form_html': form_html
    })

@service_api_bp.route('/types/<service_type>/items', methods=['GET'])
def get_service_items_by_type(service_type):
    """API endpoint to get service items by type"""
    items = ServiceItem.query.filter_by(service_type=service_type).all()
    
    result = []
    for item in items:
        result.append({
            'id': item.id,
            'booking_reference': item.booking.reference_number,
            'description': item.description,
            'start_date': item.start_date.strftime('%Y-%m-%d'),
            'end_date': item.end_date.strftime('%Y-%m-%d'),
            'amount': item.amount,
            'status': item.status
        })
    
    return jsonify(result)