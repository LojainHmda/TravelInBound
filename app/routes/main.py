from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models.booking import Booking
from app.models import STATUS_REQUEST, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from app.models import ServiceItem

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page showing recent bookings"""
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
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