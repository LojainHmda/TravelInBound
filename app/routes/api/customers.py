from flask import Blueprint, jsonify, request
from app.models.customer import Customer
from app.models.booking import Booking
from app import db
from sqlalchemy import func

# Create customers API blueprint
customers_api_bp = Blueprint('customers_api', __name__)

@customers_api_bp.route('/customers')

def get_customers():
    """Get all customers with booking stats for selection modal"""
    try:
        # Get customers with booking count
        customers_query = db.session.query(
            Customer,
            func.count(Booking.id).label('booking_count')
        ).outerjoin(Booking, Customer.id == Booking.customer_id)\
         .group_by(Customer.id)\
         .order_by(Customer.first_name, Customer.last_name)
        
        customers_data = []
        for customer, booking_count in customers_query.all():
            customers_data.append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company_name,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'booking_count': booking_count or 0
            })
        
        return jsonify({
            'success': True,
            'customers': customers_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_api_bp.route('/customers/<int:customer_id>')

def get_customer(customer_id):
    """Get single customer details"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Get booking count
        booking_count = Booking.query.filter_by(customer_id=customer.id).count()
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company_name,
                'address': customer.address,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'booking_count': booking_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500