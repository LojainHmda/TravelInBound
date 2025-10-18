from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import json

from app import db
from app.models.inbound import (
    InboundRequest, ItineraryRow, InboundHotel, InboundTransport, 
    InboundMeal, InboundGuide, COST_UNIT_PER_PERSON, COST_UNIT_PER_GROUP
)
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from app.models.service import SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_RESTAURANT, SERVICE_GUIDE, ServiceItem
from app.models.booking import Booking
from app.forms.inbound import (
    InboundRequestForm, ItineraryRowForm, InboundHotelForm, 
    InboundTransportForm, InboundMealForm, InboundGuideForm
)

# Create blueprint for inbound tour operator routes
inbound_bp = Blueprint('inbound', __name__, url_prefix='/inbound')

@inbound_bp.route('/')
@login_required
def index():
    """List all inbound requests with filtering"""
    query = InboundRequest.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    request_number = request.args.get('request_number', '')
    if request_number:
        query = query.filter(InboundRequest.request_number.contains(request_number))
    
    agent = request.args.get('agent', '')
    if agent:
        query = query.filter(InboundRequest.agent.contains(agent))
    
    date_from = request.args.get('date_from', '')
    if date_from:
        query = query.filter(InboundRequest.from_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    date_to = request.args.get('date_to', '')
    if date_to:
        query = query.filter(InboundRequest.to_date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    status = request.args.get('status', '')
    if status:
        query = query.filter(InboundRequest.status == status)
    
    # Order by most recent
    requests = query.order_by(InboundRequest.created_at.desc()).all()
    return render_template('inbound/index.html', requests=requests)

@inbound_bp.route('/new')
@login_required
def new_request():
    """Create new inbound request and go directly to itinerary creation"""
    # Create a new request with default values
    request_obj = InboundRequest(
        request_number=InboundRequest.generate_request_number(),
        from_date=datetime.now().date(),
        to_date=(datetime.now() + timedelta(days=3)).date(),
        customer_type='AGENCY',  # Default customer type
        contact_name='TBA',  # Default value
        nationality='TBA',  # Default value to avoid null constraint
        pax=1,
        user_id=current_user.id,
        status=STATUS_REQUEST
    )
    request_obj.calculate_days()
    
    db.session.add(request_obj)
    db.session.commit()
    
    # Redirect to view page which now has unified edit functionality
    flash(f'New inbound request {request_obj.request_number} created. Please fill in the details.', 'info')
    return redirect(url_for('inbound.view_request', id=request_obj.id))

@inbound_bp.route('/<int:id>/edit')
@login_required
def edit_request(id):
    """Edit inbound request with full itinerary interface"""
    request_obj = InboundRequest.query.get_or_404(id)
    
    # Check ownership
    if request_obj.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('inbound.index'))
    
    # Get all customers for selection dropdown
    from app.models.customer import Customer
    customers = Customer.query.all()
    
    return render_template('inbound/edit_request.html', request=request_obj, customers=customers)

@inbound_bp.route('/<int:id>/view')
def view_request(id):
    """View inbound request details with unified edit functionality"""
    request_obj = InboundRequest.query.get_or_404(id)
    
    # Temporarily disabled ownership check for testing
    # Ownership validation removed for voucher access
    
    return render_template('inbound/view_request.html', request=request_obj)

# API Route for updating request details
@inbound_bp.route('/api/<int:request_id>/update', methods=['POST'])
@login_required
def api_update_request(request_id):
    """Update inbound request master details"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        
        # Update master details
        request_obj.customer_id = data.get('customer_id') if data.get('customer_id') else None
        request_obj.customer_type = data.get('customer_type', request_obj.customer_type)
        request_obj.contact_name = data.get('contact_name', request_obj.contact_name)
        request_obj.agent_ref = data.get('agent_ref', request_obj.agent_ref)
        request_obj.nationality = data.get('nationality', request_obj.nationality)
        request_obj.pax = int(data.get('pax', request_obj.pax))
        request_obj.special_note = data.get('special_note', request_obj.special_note)
        
        # Update dates
        from_date_str = data.get('from_date')
        to_date_str = data.get('to_date')
        if from_date_str:
            request_obj.from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        if to_date_str:
            request_obj.to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        
        # Recalculate days if dates changed
        if from_date_str or to_date_str:
            request_obj.calculate_days()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Request updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# API Route for saving itinerary
@inbound_bp.route('/api/<int:request_id>/save-itinerary', methods=['POST'])
@login_required
def api_save_itinerary(request_id):
    """Save itinerary data for inbound request - auto-generates days if empty"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        rows_data = data.get('rows', [])
        
        print(f"DEBUG: Saving itinerary for request {request_id}")
        print(f"DEBUG: Received {len(rows_data)} rows")
        
        # Auto-generate days if no rows provided but we have dates
        if not rows_data and request_obj.from_date and request_obj.to_date:
            print("DEBUG: No rows provided, auto-generating days from date range")
            
            # Generate one row per day
            current_date = request_obj.from_date
            day_counter = 1
            
            while current_date <= request_obj.to_date:
                row_data = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'description': f'Day {day_counter} - {current_date.strftime("%A, %B %d")}',
                    'base_cost': 0.0,
                    'currency': request_obj.total_currency or 'USD',
                    'cost_unit': 'PER_PERSON',
                    'flag_hotel': False,
                    'flag_guide': False,
                    'flag_transport': False,
                    'flag_meal': False,
                    'flag_airport': False,
                    'hotel_single_rooms': 0,
                    'hotel_double_rooms': 0,
                    'hotel_triple_rooms': 0,
                    'hotel_other_rooms': 0
                }
                rows_data.append(row_data)
                
                current_date += timedelta(days=1)
                day_counter += 1
            
            print(f"DEBUG: Auto-generated {len(rows_data)} rows")
        
        # Clear existing itinerary rows
        deleted_count = ItineraryRow.query.filter_by(request_id=request_id).delete()
        print(f"DEBUG: Deleted {deleted_count} existing rows")
        
        # Add new rows
        for i, row_data in enumerate(rows_data):
            print(f"DEBUG: Processing row {i}: {row_data}")
            row = ItineraryRow(
                request_id=request_id,
                date=datetime.strptime(row_data['date'], '%Y-%m-%d').date(),
                description=row_data['description'],
                base_cost=float(row_data['base_cost']) if row_data['base_cost'] else 0.0,
                currency=row_data['currency'],
                cost_unit=row_data['cost_unit'],
                flag_hotel=row_data.get('flag_hotel', False),
                flag_guide=row_data.get('flag_guide', False),
                flag_transport=row_data.get('flag_transport', False),
                flag_meal=row_data.get('flag_meal', False),
                flag_airport=row_data.get('flag_airport', False),
                hotel_single_rooms=int(row_data.get('hotel_single_rooms', 0)),
                hotel_double_rooms=int(row_data.get('hotel_double_rooms', 0)),
                hotel_triple_rooms=int(row_data.get('hotel_triple_rooms', 0)),
                hotel_other_rooms=int(row_data.get('hotel_other_rooms', 0))
            )
            db.session.add(row)
            print(f"DEBUG: Added row {i} to session")
        
        # Recalculate totals
        request_obj.calculate_total()
        
        db.session.commit()
        print(f"DEBUG: Successfully saved itinerary")
        return jsonify({'success': True, 'message': 'Itinerary saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# API Routes for AJAX operations
@inbound_bp.route('/api/<int:request_id>/itinerary', methods=['GET'])
@login_required
def api_get_itinerary(request_id):
    """Get itinerary rows for a request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    rows = []
    for row in request_obj.itinerary_rows:
        rows.append({
            'id': row.id,
            'date': row.date.isoformat(),
            'description': row.description,
            'base_cost': row.base_cost,
            'cost_unit': row.cost_unit,
            'currency': row.currency,
            'flag_hotel': row.flag_hotel,
            'flag_guide': row.flag_guide,
            'flag_transport': row.flag_transport,
            'flag_meal': row.flag_meal,
            'flag_airport': row.flag_airport,
            'hotel_single_rooms': getattr(row, 'hotel_single_rooms', 0),
            'hotel_double_rooms': getattr(row, 'hotel_double_rooms', 0),
            'hotel_triple_rooms': getattr(row, 'hotel_triple_rooms', 0),
            'hotel_other_rooms': getattr(row, 'hotel_other_rooms', 0),
            'row_cost': row.calculate_row_cost(request_obj.pax)
        })
    
    return jsonify({'rows': rows, 'total': request_obj.calculate_total()})

@inbound_bp.route('/api/<int:request_id>/itinerary', methods=['POST'])
@login_required
def api_save_itinerary_original(request_id):
    """Save itinerary rows for a request (original version)"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    rows_data = data.get('rows', [])
    
    # Clear existing rows
    ItineraryRow.query.filter_by(request_id=request_id).delete()
    
    # Add new rows and auto-generate services
    for row_data in rows_data:
        row = ItineraryRow(
            request_id=request_id,
            date=datetime.strptime(row_data['date'], '%Y-%m-%d').date(),
            description=row_data['description'],
            base_cost=float(row_data.get('base_cost', 0)),
            cost_unit=row_data.get('cost_unit', COST_UNIT_PER_PERSON),
            currency=row_data.get('currency', 'USD'),
            flag_hotel=row_data.get('flag_hotel', False),
            flag_guide=row_data.get('flag_guide', False),
            flag_transport=row_data.get('flag_transport', False),
            flag_meal=row_data.get('flag_meal', False),
            flag_airport=row_data.get('flag_airport', False),
            hotel_single_rooms=int(row_data.get('hotel_single_rooms', 0)),
            hotel_double_rooms=int(row_data.get('hotel_double_rooms', 0)),
            hotel_triple_rooms=int(row_data.get('hotel_triple_rooms', 0)),
            hotel_other_rooms=int(row_data.get('hotel_other_rooms', 0))
        )
        db.session.add(row)
        db.session.flush()  # Get the ID
        
        # Auto-generate service records based on flags
        _auto_generate_services(request_obj, row)
    
    # Recalculate total
    request_obj.calculate_total()
    
    db.session.commit()
    
    return jsonify({'success': True, 'total': request_obj.total_amount})

@inbound_bp.route('/api/<int:request_id>/generate-days', methods=['POST'])
@login_required
def api_generate_by_days(request_id):
    """Generate itinerary rows by days"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Clear existing rows
    ItineraryRow.query.filter_by(request_id=request_id).delete()
    
    # Generate one row per day
    current_date = request_obj.from_date
    day_counter = 1
    
    while current_date <= request_obj.to_date:
        row = ItineraryRow(
            request_id=request_id,
            date=current_date,
            description=f'Day {day_counter} - {current_date.strftime("%A, %B %d")}',
            base_cost=0.0,
            cost_unit=COST_UNIT_PER_PERSON,
            currency=request_obj.total_currency
        )
        db.session.add(row)
        
        current_date += timedelta(days=1)
        day_counter += 1
    
    db.session.commit()
    
    return jsonify({'success': True})

@inbound_bp.route('/api/<int:request_id>/generate-sections', methods=['POST'])
@login_required
def api_generate_by_sections(request_id):
    """Generate itinerary rows by service sections"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Clear existing rows
    ItineraryRow.query.filter_by(request_id=request_id).delete()
    
    # Generate rows grouped by service type
    services = [
        ('Accommodation', True, False, False, False, False),  # Hotel flag
        ('Transportation', False, False, True, False, False),  # Transport flag
        ('Meals & Dining', False, False, False, True, False),  # Meal flag
        ('Guide Services', False, True, False, False, False),  # Guide flag
        ('Airport Services', False, False, False, False, True)  # Airport flag
    ]
    
    for service_name, hotel, guide, transport, meal, airport in services:
        row = ItineraryRow(
            request_id=request_id,
            date=request_obj.from_date,
            description=f'{service_name} - {request_obj.from_date.strftime("%B %d")} to {request_obj.to_date.strftime("%B %d")}',
            base_cost=0.0,
            cost_unit=COST_UNIT_PER_PERSON,
            currency=request_obj.total_currency,
            flag_hotel=hotel,
            flag_guide=guide,
            flag_transport=transport,
            flag_meal=meal,
            flag_airport=airport
        )
        db.session.add(row)
    
    db.session.commit()
    
    return jsonify({'success': True})

def _auto_generate_services(request_obj, itinerary_row):
    """Auto-generate service records based on itinerary row flags"""
    
    if itinerary_row.flag_hotel:
        # Generate hotel record
        hotel = InboundHotel(
            request_id=request_obj.id,
            source_itinerary_id=itinerary_row.id,
            check_in_date=itinerary_row.date,
            check_out_date=itinerary_row.date + timedelta(days=1),  # Default 1 night
            nights=1,
            meal_plan='BB',
            cost_per_night=itinerary_row.base_cost if itinerary_row.cost_unit == COST_UNIT_PER_PERSON else itinerary_row.base_cost / request_obj.pax,
            total_cost=itinerary_row.calculate_row_cost(request_obj.pax),
            currency=itinerary_row.currency
        )
        db.session.add(hotel)
    
    if itinerary_row.flag_transport:
        # Generate transport record
        # Default vehicle type based on pax size
        if request_obj.pax <= 4:
            vehicle_type = 'Sedan'
        elif request_obj.pax <= 8:
            vehicle_type = 'Van'
        else:
            vehicle_type = 'Bus'
        
        transport = InboundTransport(
            request_id=request_obj.id,
            source_itinerary_id=itinerary_row.id,
            date=itinerary_row.date,
            vehicle_type=vehicle_type,
            cost=itinerary_row.calculate_row_cost(request_obj.pax),
            currency=itinerary_row.currency
        )
        db.session.add(transport)
    
    if itinerary_row.flag_airport:
        # Generate airport transfer (special transport)
        transport = InboundTransport(
            request_id=request_obj.id,
            source_itinerary_id=itinerary_row.id,
            date=itinerary_row.date,
            vehicle_type='Airport Transfer',
            is_airport_transfer=True,
            cost=itinerary_row.calculate_row_cost(request_obj.pax),
            currency=itinerary_row.currency
        )
        db.session.add(transport)
    
    if itinerary_row.flag_meal:
        # Generate meal record
        meal = InboundMeal(
            request_id=request_obj.id,
            source_itinerary_id=itinerary_row.id,
            date=itinerary_row.date,
            meal_type='Lunch',  # Default
            cost_per_person=itinerary_row.base_cost if itinerary_row.cost_unit == COST_UNIT_PER_PERSON else itinerary_row.base_cost / request_obj.pax,
            total_cost=itinerary_row.calculate_row_cost(request_obj.pax),
            currency=itinerary_row.currency
        )
        db.session.add(meal)
    
    if itinerary_row.flag_guide:
        # Generate guide record
        # Default language from nationality mapping
        language_map = {
            'German': 'German',
            'French': 'French',
            'Spanish': 'Spanish',
            'Italian': 'Italian',
            'Russian': 'Russian',
            'Chinese': 'Mandarin',
            'Japanese': 'Japanese',
            'Korean': 'Korean',
            'Arabic': 'Arabic'
        }
        
        language = language_map.get(request_obj.nationality, 'English')
        
        guide = InboundGuide(
            request_id=request_obj.id,
            source_itinerary_id=itinerary_row.id,
            date=itinerary_row.date,
            language=language,
            service_type='Meet & Greet',
            duration_hours=4.0,  # Default 4 hours
            cost=itinerary_row.calculate_row_cost(request_obj.pax),
            currency=itinerary_row.currency
        )
        db.session.add(guide)

@inbound_bp.route('/api/<int:request_id>/update-master-details', methods=['POST'])
@login_required
def api_update_master_details(request_id):
    """Update master details"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Update master details
    request_obj.agent = data.get('agent', request_obj.agent)
    request_obj.contact_name = data.get('contact_name', request_obj.contact_name)
    request_obj.agent_ref = data.get('agent_ref', request_obj.agent_ref)
    request_obj.nationality = data.get('nationality', request_obj.nationality)
    request_obj.pax = data.get('pax', request_obj.pax)
    request_obj.special_note = data.get('special_note', request_obj.special_note)
    request_obj.customer_id = data.get('customer_id') if data.get('customer_id') else None
    
    # Handle date updates
    if data.get('from_date'):
        request_obj.from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').date()
    if data.get('to_date'):
        request_obj.to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').date()
    
    # Recalculate days
    request_obj.calculate_days()
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'no_of_days': request_obj.no_of_days,
        'message': 'Master details updated successfully'
    })

@inbound_bp.route('/api/<int:request_id>/update-status', methods=['POST'])
@login_required
def api_update_status(request_id):
    """Update request status"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in [STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED]:
        return jsonify({'error': 'Invalid status'}), 400
    
    request_obj.status = new_status
    db.session.commit()
    
    return jsonify({'success': True, 'status': new_status})

@inbound_bp.route('/api/<int:request_id>/generate-services', methods=['POST'])
@login_required
def api_generate_services(request_id):
    """Generate services and create normal booking"""
    try:
        request_obj = InboundRequest.query.get_or_404(request_id)
        
        if request_obj.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Import the necessary models
        from app.models import Booking, ServiceItem, Customer
        from app.models import SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_RESTAURANT, SERVICE_GUIDE
        
        # Create or get booking record
        if request_obj.booking_id:
            booking = Booking.query.get(request_obj.booking_id)
            if not booking:
                booking = None
        else:
            booking = None
            
        if not booking:
            # Use the customer from the inbound request if available
            # For existing requests without customer_id, try to find by contact name
            customer_id = getattr(request_obj, 'customer_id', None)
            if customer_id:
                customer = Customer.query.get(customer_id)
            else:
                # Fallback: find or create customer by contact name
                customer = Customer.query.filter_by(first_name=request_obj.contact_name).first()
                if not customer:
                    customer = Customer()
                    customer.first_name = request_obj.contact_name
                    customer.last_name = ""
                    customer.phone = "TBD"
                    customer.email = "tbd@example.com"
                    customer.nationality = request_obj.nationality
                    db.session.add(customer)
                    db.session.flush()
            
            # Create new booking
            booking = Booking()
            booking.reference_number = request_obj.request_number
            booking.user_id = request_obj.user_id
            booking.customer_id = customer.id
            booking.status = request_obj.status
            booking.total_amount = request_obj.total_amount
            db.session.add(booking)
            db.session.flush()
            
            # Link booking to inbound request and update status to BOOKED
            request_obj.booking_id = booking.id
            request_obj.status = 'BOOKED'
        
        # Clear existing service items
        ServiceItem.query.filter_by(booking_id=booking.id).delete()
        
        services_created = 0
        
        # Generate ServiceItem records based on itinerary flags
        for row in request_obj.itinerary_rows:
            row_cost = row.calculate_row_cost(request_obj.pax)
            
            # Hotel service - include room distribution data
            if row.flag_hotel:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_HOTEL
                service_item.start_date = row.date
                service_item.end_date = row.date + timedelta(days=1)
                service_item.description = f"Hotel accommodation - {row.description}"
                service_item.amount = row_cost
                service_item.status = STATUS_REQUEST
                # Store room distribution data in the description for now
                room_summary = f"S:{row.hotel_single_rooms or 0} D:{row.hotel_double_rooms or 0} T:{row.hotel_triple_rooms or 0} O:{row.hotel_other_rooms or 0}"
                service_item.description = f"Hotel accommodation - {row.description} | Rooms: {room_summary}"
                db.session.add(service_item)
                services_created += 1
            
            # Transport service
            if row.flag_transport:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_TRANSPORT
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Transport service - {row.description}"
                service_item.amount = row_cost
                service_item.status = STATUS_REQUEST
                db.session.add(service_item)
                services_created += 1
            
            # Restaurant/Meal service
            if row.flag_meal:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_RESTAURANT
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Restaurant meal - {row.description}"
                service_item.amount = row_cost
                service_item.status = STATUS_REQUEST
                db.session.add(service_item)
                services_created += 1
            
            # Guide service
            if row.flag_guide:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_GUIDE
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Tour guide service - {row.description}"
                service_item.amount = row_cost
                service_item.status = STATUS_REQUEST
                db.session.add(service_item)
                services_created += 1
        
        # Update booking total
        booking.calculate_total()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Generated {services_created} services",
            'booking_id': booking.id,
            'redirect_url': url_for('booking.details', booking_id=booking.id)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Removed view_services route - no longer needed since we redirect to normal booking page

@inbound_bp.route('/<int:request_id>/invoice')
@login_required
def generate_invoice(request_id):
    """Generate invoice for the request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    if request_obj.status == STATUS_REQUEST:
        abort(400, 'Cannot generate invoice for request status')
    
    return render_template('inbound/invoice.html', request=request_obj)

@inbound_bp.route('/<int:request_id>/voucher')
def generate_voucher(request_id):
    """Generate visual timeline voucher for the request"""
    from datetime import datetime
    from weasyprint import HTML
    from flask import make_response
    import io
    
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    # Temporarily disabled user validation for testing
    # if request_obj.user_id != current_user.id:
    #     abort(403)
    
    # Allow voucher generation for testing/preview
    # if request_obj.status in [STATUS_REQUEST, STATUS_BOOKED]:
    #     abort(400, 'Cannot generate voucher until confirmed')
    
    # Get layout preference from query parameter (default to vertical)
    layout = request.args.get('layout', 'vertical')
    
    # Choose template based on layout
    if layout == 'horizontal':
        template = 'inbound/voucher_timeline_horizontal.html'
    else:
        template = 'inbound/voucher_timeline.html'
    
    # Render the timeline template
    html = render_template(template, 
                          request=request_obj,
                          now=datetime.now())
    
    # Try to generate PDF using WeasyPrint
    try:
        # Create PDF from HTML
        pdf_buffer = io.BytesIO()
        HTML(string=html).write_pdf(pdf_buffer)
        pdf = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=tour_itinerary_{request_obj.request_number}.pdf'
        
        return response
    except Exception as e:
        # If PDF generation fails, return HTML version for debugging
        print(f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Return HTML with error info for debugging
        error_html = f"<h1>Voucher Generation Error</h1><p>Error: {str(e)}</p><hr>{html}"
        return error_html

@inbound_bp.route('/api/<int:request_id>/create-booking', methods=['POST'])
@login_required
def api_create_booking(request_id):
    """Create a booking from an inbound request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if booking already exists by looking for existing services
    if request_obj.booking_id:
        booking = Booking.query.get(request_obj.booking_id)
        if booking:
            return jsonify({
                'success': True,
                'message': 'Booking already exists',
                'booking_url': url_for('booking.details', booking_id=booking.id)
            })
    
    try:
        # Use the existing generate services function logic
        result = api_generate_services(request_id)
        result_data = result.get_json()
        
        if result_data.get('success'):
            return jsonify({
                'success': True,
                'message': 'Booking created successfully',
                'booking_url': result_data.get('redirect_url')
            })
        else:
            return jsonify({
                'success': False,
                'message': result_data.get('error', 'Failed to create booking')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating booking: {str(e)}'
        }), 500

@inbound_bp.route('/api/<int:request_id>/generate-quote', methods=['POST'])
@login_required
def api_generate_quote(request_id):
    """Generate a quote from an inbound request (creates booking with QUOTED status)"""
    # Import the necessary models
    from app.models import Booking, ServiceItem, Customer
    from app.models import SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_RESTAURANT, SERVICE_GUIDE
    
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if quote already exists
    if request_obj.booking_id:
        booking = Booking.query.get(request_obj.booking_id)
        if booking:
            return jsonify({
                'success': True,
                'message': 'Quote already exists',
                'booking_id': booking.id
            })
    
    try:
        
        # Create or get customer
        customer_id = getattr(request_obj, 'customer_id', None)
        if customer_id:
            customer = Customer.query.get(customer_id)
        else:
            # Fallback: find or create customer by contact name
            customer = Customer.query.filter_by(first_name=request_obj.contact_name).first()
            if not customer:
                customer = Customer()
                customer.first_name = request_obj.contact_name
                customer.last_name = ""
                customer.phone = "TBD"
                customer.email = "tbd@example.com"
                customer.nationality = request_obj.nationality
                db.session.add(customer)
                db.session.flush()
        
        # Create new booking with QUOTED status
        booking = Booking()
        booking.reference_number = request_obj.request_number
        booking.user_id = request_obj.user_id
        booking.customer_id = customer.id
        booking.status = 'QUOTED'  # Set as quoted instead of booked
        booking.total_amount = request_obj.total_amount
        db.session.add(booking)
        db.session.flush()
        
        # Link booking to inbound request and update status to QUOTED
        request_obj.booking_id = booking.id
        request_obj.status = 'QUOTED'
        
        # Clear existing service items and create new ones
        ServiceItem.query.filter_by(booking_id=booking.id).delete()
        
        services_created = 0
        
        # Create service items based on itinerary flags
        for row in request_obj.itinerary_rows:
            if row.flag_hotel:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_HOTEL
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Hotel service for {row.city}"
                service_item.amount = row.hotel_cost or 0
                service_item.status = 'QUOTED'
                db.session.add(service_item)
                services_created += 1
            
            if row.flag_transport:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_TRANSPORT
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Transport service for {row.city}"
                service_item.amount = row.transport_cost or 0
                service_item.status = 'QUOTED'
                db.session.add(service_item)
                services_created += 1
            
            if row.flag_meal:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_RESTAURANT
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Meal service for {row.city}"
                service_item.amount = row.meal_cost or 0
                service_item.status = 'QUOTED'
                db.session.add(service_item)
                services_created += 1
            
            if row.flag_guide:
                service_item = ServiceItem()
                service_item.booking_id = booking.id
                service_item.service_type = SERVICE_GUIDE
                service_item.start_date = row.date
                service_item.end_date = row.date
                service_item.description = f"Guide service for {row.city}"
                service_item.amount = row.guide_cost or 0
                service_item.status = 'QUOTED'
                db.session.add(service_item)
                services_created += 1
        
        # Recalculate booking total
        booking.calculate_total()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Quote generated successfully with {services_created} services',
            'booking_id': booking.id,
            'services_count': services_created
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error generating quote: {str(e)}'
        }), 500

@inbound_bp.route('/api/<int:request_id>/generate-proforma', methods=['POST'])
@login_required
def api_generate_proforma(request_id):
    """Generate a proforma invoice for a quoted booking"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if not request_obj.booking_id:
        return jsonify({
            'success': False,
            'message': 'No quote found. Please generate a quote first.'
        }), 400
    
    try:
        booking = Booking.query.get(request_obj.booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        if booking.status != 'QUOTED':
            return jsonify({
                'success': False,
                'message': 'Booking must be in QUOTED status to generate proforma invoice'
            }), 400
        
        # Generate proforma invoice number if not exists
        if not booking.invoice_number:
            booking.generate_invoice_number()
        
        # Update status to indicate proforma invoice generated
        booking.status = 'PROFORMA_GENERATED'
        request_obj.status = 'PROFORMA_GENERATED'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Proforma invoice generated successfully',
            'invoice_number': booking.invoice_number,
            'booking_id': booking.id,
            'redirect_url': f'/booking/{booking.id}/proforma-invoice'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error generating proforma invoice: {str(e)}'
        }), 500

@inbound_bp.route('/api/<int:request_id>/confirm-booking', methods=['POST'])
@login_required
def api_confirm_booking(request_id):
    """Confirm a booking after proforma invoice is generated"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if not request_obj.booking_id:
        return jsonify({
            'success': False,
            'message': 'No booking found. Please generate a quote first.'
        }), 400
    
    try:
        booking = Booking.query.get(request_obj.booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        if booking.status not in ['QUOTED', 'PROFORMA_GENERATED']:
            return jsonify({
                'success': False,
                'message': 'Booking must have proforma invoice before confirmation'
            }), 400
        
        # Confirm the booking
        booking.status = 'BOOKED'
        request_obj.status = 'BOOKED'
        
        # Update all service items to BOOKED status
        for service_item in booking.service_items:
            service_item.status = 'BOOKED'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Booking confirmed successfully',
            'booking_id': booking.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error confirming booking: {str(e)}'
        }), 500