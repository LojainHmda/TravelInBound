from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models.booking import Booking
from app.models.service import ServiceItem
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_FULFILLED

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page showing recent bookings"""
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('index.html', bookings=recent_bookings)

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard showing booking statistics and status"""
    # Get counts for various statuses
    request_count = Booking.query.filter_by(status=STATUS_REQUEST).count()
    booked_count = Booking.query.filter_by(status=STATUS_BOOKED).count()
    in_progress_count = Booking.query.filter_by(status=STATUS_IN_PROGRESS).count()
    completed_count = Booking.query.filter_by(status=STATUS_FULFILLED).count()
    
    # Get all recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    # Get recent service items by type
    flight_items = ServiceItem.query.filter_by(service_type='FLIGHT').order_by(ServiceItem.created_at.desc()).limit(5).all()
    hotel_items = ServiceItem.query.filter_by(service_type='HOTEL').order_by(ServiceItem.created_at.desc()).limit(5).all()
    transport_items = ServiceItem.query.filter_by(service_type='TRANSPORT').order_by(ServiceItem.created_at.desc()).limit(5).all()
    visa_items = ServiceItem.query.filter_by(service_type='VISA').order_by(ServiceItem.created_at.desc()).limit(5).all()
    insurance_items = ServiceItem.query.filter_by(service_type='INSURANCE').order_by(ServiceItem.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard_redesigned.html',
        request_count=request_count,
        booked_count=booked_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        recent_bookings=recent_bookings,
        flight_items=flight_items,
        hotel_items=hotel_items,
        transport_items=transport_items,
        visa_items=visa_items,
        insurance_items=insurance_items
    )