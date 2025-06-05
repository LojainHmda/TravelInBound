from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.booking import Booking
from app.models import STATUS_REQUEST, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from app.models import ServiceItem
from app.models.user import User

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page showing recent bookings"""
    try:
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    except Exception as e:
        # Handle database connection issues gracefully
        print(f"Database query error: {e}")
        recent_bookings = []
    return render_template('index.html', bookings=recent_bookings)

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard showing booking statistics and status - OPTIMIZED"""
    # PERFORMANCE FIX: Use efficient single queries with proper limits
    from sqlalchemy import func
    
    # Get counts for various statuses in a single query
    status_counts = db.session.query(
        Booking.status,
        func.count(Booking.id)
    ).group_by(Booking.status).all()
    
    # Convert to dictionary for easy access
    counts = {status: count for status, count in status_counts}
    request_count = counts.get(STATUS_REQUEST, 0)
    in_progress_count = counts.get(STATUS_IN_PROGRESS, 0)
    confirmed_count = counts.get(STATUS_CONFIRMED, 0)
    booked_count = 0  # Still pass 0 for template compatibility
    
    # PERFORMANCE FIX: Limit recent bookings to reasonable number
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    
    # PERFORMANCE FIX: Get service items efficiently with single query
    service_items = db.session.query(
        ServiceItem.service_type,
        ServiceItem.id,
        ServiceItem.description,
        ServiceItem.created_at,
        ServiceItem.status
    ).order_by(ServiceItem.created_at.desc()).limit(25).all()
    
    # Group service items by type (more efficient than 5 separate queries)
    flight_items = [item for item in service_items if item.service_type == 'FLIGHT'][:5]
    hotel_items = [item for item in service_items if item.service_type == 'HOTEL'][:5]
    transport_items = [item for item in service_items if item.service_type == 'TRANSPORT'][:5]
    visa_items = [item for item in service_items if item.service_type == 'VISA'][:5]
    insurance_items = [item for item in service_items if item.service_type == 'INSURANCE'][:5]
    
    return render_template(
        'dashboard_redesigned.html',
        request_count=request_count,
        booked_count=booked_count,
        in_progress_count=in_progress_count,
        confirmed_count=confirmed_count,
        recent_bookings=recent_bookings,
        flight_items=flight_items,
        hotel_items=hotel_items,
        transport_items=transport_items,
        visa_items=visa_items,
        insurance_items=insurance_items
    )

@main_bp.route('/operations')
def operations_dashboard():
    """View for the travel operations dashboard - OPTIMIZED"""
    from sqlalchemy import func
    
    # PERFORMANCE FIX: Get all service type counts in single query
    service_counts = db.session.query(
        ServiceItem.service_type,
        func.count(ServiceItem.id)
    ).filter_by(status=STATUS_IN_PROGRESS).group_by(ServiceItem.service_type).all()
    
    # Convert to dictionary for easy access
    counts = {service_type: count for service_type, count in service_counts}
    flight_count = counts.get('FLIGHT', 0)
    hotel_count = counts.get('HOTEL', 0)
    transport_count = counts.get('TRANSPORT', 0)
    visa_count = counts.get('VISA', 0)
    insurance_count = counts.get('INSURANCE', 0)
    
    # PERFORMANCE FIX: Limit in-progress bookings to reasonable number
    in_progress_bookings = Booking.query.filter_by(status=STATUS_IN_PROGRESS).order_by(Booking.created_at.desc()).limit(20).all()
    
    return render_template(
        'operations_dashboard.html',
        flight_count=flight_count,
        hotel_count=hotel_count,
        transport_count=transport_count,
        visa_count=visa_count,
        insurance_count=insurance_count,
        recent_bookings=in_progress_bookings
    )

@main_bp.route('/search-history')
def search_and_history():
    """Search and History page for bookings - PERFORMANCE OPTIMIZED"""
    # Get search parameters
    search_query = request.args.get('search', '')
    customer_query = request.args.get('customer', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    
    # PERFORMANCE FIX: Only load data when search parameters are provided
    bookings = []
    has_search_params = any([search_query, customer_query, status_filter, date_from])
    
    if has_search_params:
        # Base query
        query = Booking.query
        
        # Apply filters
        if search_query:
            query = query.filter(Booking.reference_number.ilike(f'%{search_query}%'))
        
        if customer_query:
            # Join with user table for customer search
            query = query.join(User).filter(User.username.ilike(f'%{customer_query}%'))
        
        if status_filter:
            query = query.filter(Booking.status == status_filter)
        
        if date_from:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(Booking.created_at >= date_obj)
            except ValueError:
                pass
        
        # Order by newest first and limit results for performance
        bookings = query.order_by(Booking.created_at.desc()).limit(100).all()
    
    return render_template('booking/search_and_history.html', 
                         bookings=bookings,
                         has_search_params=has_search_params)

@main_bp.route('/find-bookings')
def find_bookings():
    """Find Bookings page with comprehensive filtering - PERFORMANCE OPTIMIZED"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_, or_
    
    # Get filter parameters
    search_term = request.args.get('search', '').strip()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    service_type = request.args.get('service_type')
    amount_from = request.args.get('amount_from')
    amount_to = request.args.get('amount_to')
    customer_search = request.args.get('customer', '').strip()
    
    # PERFORMANCE FIX: Only load data when search parameters are provided
    bookings = []
    total_amount = 0
    total_bookings = 0
    has_search_params = any([search_term, date_from, date_to, status, service_type, 
                            amount_from, amount_to, customer_search])
    
    if has_search_params:
        # Build base query
        query = Booking.query
        
        # Apply filters
        conditions = []
        
        # Search term filter (reference number)
        if search_term:
            conditions.append(Booking.reference_number.ilike(f'%{search_term}%'))
        
        # Customer search filter
        if customer_search:
            try:
                from app.models.customer import Customer
                query = query.join(Customer, Booking.customer_id == Customer.id, isouter=True)
                customer_conditions = [
                    Customer.first_name.ilike(f'%{customer_search}%'),
                    Customer.last_name.ilike(f'%{customer_search}%'),
                    Customer.email.ilike(f'%{customer_search}%')
                ]
                conditions.append(or_(*customer_conditions))
            except:
                # Fallback to user search if Customer model not available
                query = query.join(User, Booking.user_id == User.id, isouter=True)
                conditions.append(User.username.ilike(f'%{customer_search}%'))
        
        # Date range filters
        if date_from:
            try:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                conditions.append(Booking.created_at >= date_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the entire end date
                end_date = datetime.combine(date_obj, datetime.max.time())
                conditions.append(Booking.created_at <= end_date)
            except ValueError:
                pass
        
        # Status filter
        if status:
            conditions.append(Booking.status == status)
        
        # Service type filter
        if service_type:
            from app.models import ServiceItem
            query = query.join(ServiceItem, Booking.id == ServiceItem.booking_id, isouter=True)
            conditions.append(ServiceItem.service_type == service_type)
        
        # Amount range filters
        if amount_from:
            try:
                amount = float(amount_from)
                conditions.append(Booking.total_amount >= amount)
            except ValueError:
                pass
        
        if amount_to:
            try:
                amount = float(amount_to)
                conditions.append(Booking.total_amount <= amount)
            except ValueError:
                pass
        
        # Apply all conditions
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Order by newest first and limit for performance
        bookings = query.order_by(Booking.created_at.desc()).limit(100).all()
        
        # Calculate summary statistics
        total_amount = sum(booking.total_amount or 0 for booking in bookings)
        total_bookings = len(bookings)
    
    return render_template('booking/find_bookings.html', 
                         bookings=bookings,
                         total_amount=total_amount,
                         total_bookings=total_bookings,
                         has_search_params=has_search_params)