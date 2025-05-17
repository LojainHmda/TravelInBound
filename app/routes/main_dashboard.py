from flask import Blueprint, render_template
from app import db
from app.models.booking import Booking
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from app.models.service import ServiceItem
from app.models import SERVICE_FLIGHT, SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_VISA, SERVICE_INSURANCE

# Create blueprint for the yellow card dashboard
yellow_dashboard_bp = Blueprint('yellow_dashboard', __name__)

@yellow_dashboard_bp.route('/')
def index():
    # Get counts for each status
    request_count = Booking.query.filter_by(status=STATUS_REQUEST).count()
    booked_count = Booking.query.filter_by(status=STATUS_BOOKED).count()
    in_progress_count = Booking.query.filter_by(status=STATUS_IN_PROGRESS).count()
    completed_count = Booking.query.filter_by(status=STATUS_CONFIRMED).count()
    
    # Get recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    # Get service items for each service type
    flight_items = ServiceItem.query.filter_by(service_type=SERVICE_FLIGHT).order_by(ServiceItem.created_at.desc()).limit(5).all()
    hotel_items = ServiceItem.query.filter_by(service_type=SERVICE_HOTEL).order_by(ServiceItem.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard_simple.html',
        status_counts={
            'request': request_count,
            'booked': booked_count,
            'in_progress': in_progress_count,
            'completed': completed_count
        },
        recent_bookings=recent_bookings,
        service_items={
            'flight': flight_items,
            'hotel': hotel_items
        }
    )