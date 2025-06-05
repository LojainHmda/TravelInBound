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
        'dashboard.html',
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
    """Search and History page for bookings"""
    # Get search parameters
    search_query = request.args.get('search', '')
    customer_query = request.args.get('customer', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    
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
    
    # Order by newest first
    bookings = query.order_by(Booking.created_at.desc()).all()
    
    return render_template('booking/search_and_history.html', bookings=bookings)

@main_bp.route('/find_bookings')
def find_bookings():
    """Find bookings page with smart filters"""
    from app.models.customer import Customer
    from datetime import datetime, timedelta
    
    # Get filter parameters
    search_term = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    service_type_filter = request.args.get('service_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    customer_filter = request.args.get('customer', '')
    amount_min = request.args.get('amount_min', '')
    amount_max = request.args.get('amount_max', '')
    
    # Build base query with joins
    query = Booking.query.join(Customer, Booking.customer_id == Customer.id, isouter=True)
    
    # Apply search filter (reference number, customer name, description)
    if search_term:
        query = query.filter(
            (Booking.reference_number.ilike(f'%{search_term}%')) |
            (Customer.first_name.ilike(f'%{search_term}%')) |
            (Customer.last_name.ilike(f'%{search_term}%')) |
            (Customer.email.ilike(f'%{search_term}%'))
        )
    
    # Apply status filter
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    
    # Apply service type filter
    if service_type_filter:
        query = query.join(ServiceItem).filter(ServiceItem.service_type == service_type_filter)
    
    # Apply date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Booking.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            to_date = to_date + timedelta(days=1)
            query = query.filter(Booking.created_at < to_date)
        except ValueError:
            pass
    
    # Apply customer filter
    if customer_filter:
        try:
            customer_id = int(customer_filter)
            query = query.filter(Booking.customer_id == customer_id)
        except ValueError:
            pass
    
    # Apply amount range filter
    if amount_min:
        try:
            min_amount = float(amount_min)
            query = query.filter(Booking.total_amount >= min_amount)
        except ValueError:
            pass
    
    if amount_max:
        try:
            max_amount = float(amount_max)
            query = query.filter(Booking.total_amount <= max_amount)
        except ValueError:
            pass
    
    # Execute query and get results
    bookings = query.order_by(Booking.created_at.desc()).all()
    
    # Get all customers for dropdown
    customers = Customer.query.order_by(Customer.first_name, Customer.last_name).all()
    
    # Status choices for template
    status_choices = [
        ('REQUEST', 'Request'),
        ('BOOKED', 'Booked'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    # Payment status choices
    payment_status_choices = [
        ('NONE', 'No Payment'),
        ('PARTIAL', 'Partial Payment'),
        ('FULL', 'Fully Paid')
    ]
    
    # Service type choices
    service_type_choices = [
        ('FLIGHT', 'Flight'),
        ('HOTEL', 'Hotel'),
        ('TRANSPORT', 'Transport'),
        ('VISA', 'Visa'),
        ('INSURANCE', 'Insurance')
    ]
    
    return render_template('booking/find_bookings.html', 
                         bookings=bookings, 
                         customers=customers,
                         status_choices=status_choices,
                         payment_status_choices=payment_status_choices,
                         service_type_choices=service_type_choices,
                         filters={
                             'search': search_term,
                             'status': status_filter,
                             'service_type': service_type_filter,
                             'date_from': date_from,
                             'date_to': date_to,
                             'customer': customer_filter,
                             'amount_min': amount_min,
                             'amount_max': amount_max
                         })