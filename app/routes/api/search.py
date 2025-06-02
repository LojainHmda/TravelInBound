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