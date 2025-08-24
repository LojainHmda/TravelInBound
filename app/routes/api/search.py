from flask import Blueprint, request, jsonify
from app import db
from app.models.booking import Booking
from app.models.customer import Customer
from sqlalchemy import or_

search_api = Blueprint('search_api', __name__)

@search_api.route('/api/search')
def quick_search():
    """Quick search API for the floating action button"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400
    
    try:
        # Search bookings by reference number or customer info
        bookings = Booking.query.filter(
            or_(
                Booking.reference_number.ilike(f'%{query}%'),
                # Add more search fields as needed
            )
        ).limit(5).all()
        
        # Search customers by name or email
        customers = Customer.query.filter(
            or_(
                Customer.first_name.ilike(f'%{query}%'),
                Customer.last_name.ilike(f'%{query}%'),
                Customer.email.ilike(f'%{query}%')
            )
        ).limit(5).all()
        
        # Format results
        booking_results = []
        for booking in bookings:
            booking_results.append({
                'id': booking.id,
                'reference_number': booking.reference_number,
                'status': booking.status,
                'total_amount': float(booking.total_amount) if booking.total_amount else 0,
                'customer_name': f"{booking.requester.first_name} {booking.requester.last_name}" if booking.requester else 'Unknown'
            })
        
        customer_results = []
        for customer in customers:
            customer_results.append({
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'email': customer.email,
                'phone': customer.phone
            })
        
        return jsonify({
            'bookings': booking_results,
            'customers': customer_results
        })
        
    except Exception as e:
        return jsonify({'error': 'Search failed'}), 500


@search_api.route('/api/search-suggestions')
def search_suggestions():
    """API endpoint for smart autocomplete suggestions"""
    try:
        from app.models.inbound import InboundRequest
        from sqlalchemy import distinct
        
        # Get unique agent references from inbound requests
        agents = db.session.query(distinct(InboundRequest.agent_ref))\
            .filter(InboundRequest.agent_ref.isnot(None))\
            .filter(InboundRequest.agent_ref != '')\
            .all()
        agents = [agent[0] for agent in agents if agent[0]]
        
        # Get unique contact names from inbound requests
        contact_names = db.session.query(distinct(InboundRequest.contact_name))\
            .filter(InboundRequest.contact_name.isnot(None))\
            .filter(InboundRequest.contact_name != '')\
            .all()
        contact_names = [contact[0] for contact in contact_names if contact[0]]
        
        # Get unique request numbers
        request_numbers = db.session.query(InboundRequest.request_number)\
            .filter(InboundRequest.request_number.isnot(None))\
            .order_by(InboundRequest.created_at.desc())\
            .limit(50).all()
        request_numbers = [req[0] for req in request_numbers if req[0]]
        
        # Get unique nationalities
        nationalities = db.session.query(distinct(InboundRequest.nationality))\
            .filter(InboundRequest.nationality.isnot(None))\
            .filter(InboundRequest.nationality != '')\
            .all()
        nationalities = [nat[0] for nat in nationalities if nat[0]]
        
        # Also get customer data for additional suggestions
        customers = Customer.query.with_entities(
            distinct(Customer.first_name), 
            distinct(Customer.last_name)
        ).limit(30).all()
        
        customer_names = []
        for customer in customers:
            if customer[0]:
                customer_names.append(customer[0])
            if customer[1]:
                customer_names.append(customer[1])
        
        return jsonify({
            'agents': agents,
            'contactNames': contact_names,
            'requestNumbers': request_numbers,
            'nationalities': nationalities,
            'customerNames': customer_names
        })
        
    except Exception as e:
        # Return empty suggestions if there's an error
        return jsonify({
            'agents': [],
            'contactNames': [],
            'requestNumbers': [],
            'nationalities': [],
            'customerNames': []
        })