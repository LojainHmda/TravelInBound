from flask import Blueprint, request, jsonify
from app import db
from app.models.booking import Booking
from app.models.customer import Customer
from sqlalchemy import or_, func

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
        
        # Agent filter suggestions: ref, contact, and linked customer names (matches Agent column / search)
        agent_refs = db.session.query(distinct(InboundRequest.agent_ref))\
            .filter(InboundRequest.agent_ref.isnot(None))\
            .filter(InboundRequest.agent_ref != '')\
            .all()
        agent_refs = [a[0] for a in agent_refs if a[0]]

        contact_names = db.session.query(distinct(InboundRequest.contact_name))\
            .filter(InboundRequest.contact_name.isnot(None))\
            .filter(InboundRequest.contact_name != '')\
            .all()
        contact_names = [c[0] for c in contact_names if c[0]]

        cust_display = db.session.query(
            distinct(
                func.trim(
                    func.concat(
                        Customer.first_name,
                        ' ',
                        func.coalesce(Customer.last_name, ''),
                    )
                )
            )
        ).join(InboundRequest, InboundRequest.customer_id == Customer.id).all()
        customer_display_names = [c[0] for c in cust_display if c[0] and str(c[0]).strip()]

        company_names = db.session.query(distinct(Customer.company_name))\
            .join(InboundRequest, InboundRequest.customer_id == Customer.id)\
            .filter(Customer.company_name.isnot(None))\
            .filter(Customer.company_name != '')\
            .all()
        company_names = [c[0] for c in company_names if c[0]]

        agents_set = set(agent_refs) | set(contact_names) | set(customer_display_names) | set(company_names)
        agents = sorted(agents_set, key=lambda s: s.lower())[:500]
        
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
        
        # Extra first/last tokens for other consumers (optional)
        customers = Customer.query.with_entities(
            distinct(Customer.first_name),
            distinct(Customer.last_name)
        ).limit(30).all()

        customer_name_tokens = []
        for customer in customers:
            if customer[0]:
                customer_name_tokens.append(customer[0])
            if customer[1]:
                customer_name_tokens.append(customer[1])

        return jsonify({
            'agents': agents,
            'contactNames': contact_names,
            'requestNumbers': request_numbers,
            'nationalities': nationalities,
            'customerNames': customer_name_tokens,
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