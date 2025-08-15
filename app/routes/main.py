from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.models.booking import Booking
from app.models import STATUS_REQUEST, STATUS_IN_PROGRESS, STATUS_CONFIRMED, STATUS_BOOKED
from app.models import ServiceItem
from app.models.user import User

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/supplier/<int:supplier_id>')
@login_required
def supplier_redirect(supplier_id):
    """Redirect /supplier/X to /finance/supplier/X"""
    return redirect(url_for('finance.supplier_details', supplier_id=supplier_id))

@main_bp.route('/')
@login_required
def index():
    """Home page showing recent inbound requests and workflow indicators"""
    try:
        from app.models.inbound import InboundRequest
        from sqlalchemy import func
        
        # Get recent inbound requests for the current user
        recent_requests = InboundRequest.query.filter_by(user_id=current_user.id)\
            .order_by(InboundRequest.created_at.desc()).limit(8).all()
        
        # Get status counts for workflow indicators
        status_counts = db.session.query(
            InboundRequest.status,
            func.count(InboundRequest.id)
        ).filter_by(user_id=current_user.id).group_by(InboundRequest.status).all()
        
        # Convert to dictionary for easy access
        counts = {status: count for status, count in status_counts}
        workflow_counts = {
            'REQUEST': counts.get(STATUS_REQUEST, 0),
            'BOOKED': counts.get(STATUS_BOOKED, 0),
            'IN_PROGRESS': counts.get(STATUS_IN_PROGRESS, 0),
            'CONFIRMED': counts.get(STATUS_CONFIRMED, 0)
        }
        
        # Get total amount for current user's requests
        total_amount = db.session.query(func.sum(InboundRequest.total_amount))\
            .filter_by(user_id=current_user.id).scalar() or 0
            
    except Exception as e:
        # Handle database connection issues gracefully
        print(f"Database query error: {e}")
        recent_requests = []
        workflow_counts = {'REQUEST': 0, 'BOOKED': 0, 'IN_PROGRESS': 0, 'CONFIRMED': 0}
        total_amount = 0
        
    return render_template('index.html', 
                         recent_requests=recent_requests,
                         workflow_counts=workflow_counts,
                         total_amount=total_amount)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Advanced Analytics Dashboard - Windows of Jordan Travel Operations"""
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    # Calculate date ranges for analytics
    today = datetime.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    
    # 1. REVENUE ANALYTICS
    # Total revenue from confirmed bookings this month
    current_month_revenue = db.session.query(func.sum(Booking.total_amount)).filter(
        Booking.status.in_([STATUS_CONFIRMED, STATUS_BOOKED]),
        Booking.created_at >= current_month_start
    ).scalar() or Decimal('0')
    
    # Last month revenue for comparison
    last_month_revenue = db.session.query(func.sum(Booking.total_amount)).filter(
        Booking.status.in_([STATUS_CONFIRMED, STATUS_BOOKED]),
        Booking.created_at >= last_month_start,
        Booking.created_at <= last_month_end
    ).scalar() or Decimal('0')
    
    # Calculate revenue growth percentage
    revenue_growth = 0
    if last_month_revenue > 0:
        revenue_growth = float(((current_month_revenue - last_month_revenue) / last_month_revenue) * 100)
    
    # 2. BOOKING STATISTICS
    # Active bookings in pipeline
    active_bookings = db.session.query(func.count(Booking.id)).filter(
        Booking.status.in_([STATUS_REQUEST, STATUS_IN_PROGRESS, STATUS_BOOKED])
    ).scalar() or 0
    
    # Monthly booking trends
    monthly_bookings = db.session.query(func.count(Booking.id)).filter(
        Booking.created_at >= current_month_start
    ).scalar() or 0
    
    last_month_bookings = db.session.query(func.count(Booking.id)).filter(
        Booking.created_at >= last_month_start,
        Booking.created_at <= last_month_end
    ).scalar() or 0
    
    booking_growth = 0
    if last_month_bookings > 0:
        booking_growth = float(((monthly_bookings - last_month_bookings) / last_month_bookings) * 100)
    
    # 3. OPERATIONAL METRICS
    # Services pending confirmation
    pending_services = db.session.query(func.count(ServiceItem.id)).filter(
        ServiceItem.status == STATUS_IN_PROGRESS
    ).scalar() or 0
    
    # Customer satisfaction metric (based on confirmed vs cancelled)
    total_processed = db.session.query(func.count(Booking.id)).filter(
        Booking.status.in_([STATUS_CONFIRMED, 'CANCELLED'])
    ).scalar() or 1
    
    confirmed_bookings = db.session.query(func.count(Booking.id)).filter(
        Booking.status == STATUS_CONFIRMED
    ).scalar() or 0
    
    success_rate = int((confirmed_bookings / total_processed) * 100) if total_processed > 0 else 0
    
    # 4. SERVICE TYPE BREAKDOWN
    service_breakdown = db.session.query(
        ServiceItem.service_type,
        func.count(ServiceItem.id)
    ).group_by(ServiceItem.service_type).all()
    
    # 5. RECENT ACTIVITY
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    
    # 6. WEEKLY TRENDS (last 4 weeks)
    weekly_data = []
    for i in range(4):
        week_start = today - timedelta(weeks=i+1)
        week_end = today - timedelta(weeks=i)
        week_bookings = db.session.query(func.count(Booking.id)).filter(
            Booking.created_at >= week_start,
            Booking.created_at < week_end
        ).scalar() or 0
        weekly_data.append({
            'week': f'Week {4-i}',
            'bookings': week_bookings
        })
    
    # 7. TOP PERFORMING SERVICES
    top_services = db.session.query(
        ServiceItem.service_type,
        func.count(ServiceItem.id).label('count'),
        func.sum(ServiceItem.amount).label('revenue')
    ).filter(
        ServiceItem.created_at >= current_month_start
    ).group_by(ServiceItem.service_type).order_by(func.count(ServiceItem.id).desc()).all()
    
    return render_template(
        'dashboard_redesigned.html',
        # Revenue metrics
        current_month_revenue=float(current_month_revenue),
        revenue_growth=revenue_growth,
        
        # Booking metrics  
        active_bookings=active_bookings,
        monthly_bookings=monthly_bookings,
        booking_growth=booking_growth,
        
        # Operational metrics
        pending_services=pending_services,
        success_rate=success_rate,
        
        # Activity data
        recent_bookings=recent_bookings,
        service_breakdown=service_breakdown,
        weekly_data=weekly_data,
        top_services=top_services,
        
        # Legacy compatibility
        request_count=active_bookings,
        booked_count=confirmed_bookings,
        in_progress_count=pending_services,
        confirmed_count=confirmed_bookings
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

@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with full system overview"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from sqlalchemy import func
    from app.models.customer import Customer
    from app.models.supplier import Supplier
    
    # Get comprehensive statistics for admin
    stats = {
        'total_bookings': Booking.query.count(),
        'total_customers': Customer.query.count(),
        'total_users': User.query.count(),
        'active_users': User.query.filter(User.active == True).count(),
        'recent_bookings': Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    }
    
    return render_template('admin_dashboard.html', stats=stats)

@main_bp.route('/find-bookings')
@login_required
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

@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    return send_from_directory('static', 'favicon.ico')