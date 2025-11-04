from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import json
import os

from app import db
from app.models.inbound import (
    InboundRequest, ItineraryRow, InboundHotel, InboundTransport, 
    InboundMeal, InboundGuide, InboundCashExpense, COST_UNIT_PER_PERSON, COST_UNIT_PER_GROUP
)
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from app.models.service import SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_RESTAURANT, SERVICE_GUIDE, ServiceItem
from app.models.booking import Booking
from app.models.customer import Customer
from app.forms.inbound import (
    InboundRequestForm, ItineraryRowForm, InboundHotelForm, 
    InboundTransportForm, InboundMealForm, InboundGuideForm
)
from app.services.proforma_doc_generator import ProformaDocGenerator
from app.services.voucher_trip_plan_generator import VoucherTripPlanGenerator

# Create blueprint for inbound tour operator routes
inbound_bp = Blueprint('inbound', __name__, url_prefix='/inbound')

@inbound_bp.route('/')
@login_required
def index():
    """List all inbound requests with filtering and run-down plan"""
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
    
    # Get run-down plan data for confirmed itineraries
    run_down_data = get_run_down_data_by_date()
    
    return render_template('inbound/index.html', 
                         requests=requests,
                         run_down_data=run_down_data)

def get_run_down_data_by_date():
    """Get confirmed itineraries grouped by date with activities"""
    from app.models.customer import Customer
    from sqlalchemy import and_
    
    # Get date range (next 30 days)
    today = datetime.now().date()
    date_to = today + timedelta(days=30)
    
    # Get all confirmed requests with their itinerary rows
    confirmed_requests = InboundRequest.query.filter(
        InboundRequest.user_id == current_user.id,
        InboundRequest.status.in_(['CONFIRMED', 'BOOKED'])
    ).all()
    
    # Group activities by date
    activities_by_date = {}
    
    for req in confirmed_requests:
        # Get customer info
        customer_name = "TBA"
        if req.customer_id:
            from app.models.customer import Customer
            customer = Customer.query.get(req.customer_id)
            if customer:
                customer_name = customer.name
        elif req.contact_name:
            customer_name = req.contact_name
        
        # Process itinerary rows
        for row in req.itinerary_rows:
            if row.date < today or row.date > date_to:
                continue
                
            date_key = row.date.strftime('%Y-%m-%d')
            
            if date_key not in activities_by_date:
                activities_by_date[date_key] = {
                    'date': row.date,
                    'date_formatted': row.date.strftime('%A, %B %d, %Y'),
                    'activities': []
                }
            
            # Build activity info with detailed service data
            services = []
            base_cost = row.base_cost or 0
            
            if row.flag_hotel:
                # Build room breakdown
                room_details = []
                if row.hotel_single_rooms > 0:
                    room_details.append(f"{row.hotel_single_rooms} Single")
                if row.hotel_double_rooms > 0:
                    room_details.append(f"{row.hotel_double_rooms} Double")
                if row.hotel_triple_rooms > 0:
                    room_details.append(f"{row.hotel_triple_rooms} Triple")
                if row.hotel_other_rooms > 0:
                    room_details.append(f"{row.hotel_other_rooms} Other")
                
                services.append({
                    'type': 'HOTEL',
                    'icon': 'fa-hotel',
                    'description': row.description or 'Hotel Service',
                    'cost': base_cost,
                    'rooms': ', '.join(room_details) if room_details else 'Rooms TBA',
                    'cost_unit': row.cost_unit
                })
            if row.flag_transport:
                services.append({
                    'type': 'TRANSPORT',
                    'icon': 'fa-bus',
                    'description': row.description or 'Transport Service',
                    'cost': base_cost,
                    'cost_unit': row.cost_unit,
                    'pax': req.pax
                })
            if row.flag_meal:
                services.append({
                    'type': 'MEAL',
                    'icon': 'fa-utensils',
                    'description': row.description or 'Meal Service',
                    'cost': base_cost,
                    'cost_unit': row.cost_unit,
                    'pax': req.pax
                })
            if row.flag_guide:
                services.append({
                    'type': 'GUIDE',
                    'icon': 'fa-user-tie',
                    'description': row.description or 'Guide Service',
                    'cost': base_cost,
                    'cost_unit': row.cost_unit,
                    'pax': req.pax
                })
            if row.flag_airport:
                services.append({
                    'type': 'AIRPORT',
                    'icon': 'fa-plane',
                    'description': row.description or 'Airport Service',
                    'cost': 0,
                    'pax': req.pax
                })
            
            if services:  # Only add if there are services
                activities_by_date[date_key]['activities'].append({
                    'request_number': req.request_number,
                    'request_id': req.id,
                    'customer_name': customer_name,
                    'pax': req.pax,
                    'services': services,
                    'status': req.status,
                    'status_color': get_status_color(req.status)
                })
    
    # Sort by date
    sorted_data = sorted(activities_by_date.values(), key=lambda x: x['date'])
    return sorted_data

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
    print(f"[DEBUG] api_save_itinerary_original called for request_id: {request_id}")
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        print(f"[DEBUG] Access denied: user {current_user.id} != owner {request_obj.user_id}")
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    print(f"[DEBUG] Received data: {data}")
    rows_data = data.get('rows', [])
    print(f"[DEBUG] Number of rows to save: {len(rows_data)}")
    
    # Update arrival/departure details if provided
    if 'arrival_point' in data:
        request_obj.arrival_point = data.get('arrival_point') or None
    if 'departure_point' in data:
        request_obj.departure_point = data.get('departure_point') or None
    if 'arrival_time' in data and data.get('arrival_time'):
        try:
            request_obj.arrival_time = datetime.strptime(data.get('arrival_time'), '%H:%M').time()
        except:
            request_obj.arrival_time = None
    elif 'arrival_time' in data and not data.get('arrival_time'):
        request_obj.arrival_time = None
    if 'departure_time' in data and data.get('departure_time'):
        try:
            request_obj.departure_time = datetime.strptime(data.get('departure_time'), '%H:%M').time()
        except:
            request_obj.departure_time = None
    elif 'departure_time' in data and not data.get('departure_time'):
        request_obj.departure_time = None
    
    # Update new arrival/departure fields
    if 'visa_type' in data:
        request_obj.visa_type = data.get('visa_type') or 'NOT_INCLUDED'
    if 'arrival_driver_name' in data:
        request_obj.arrival_driver_name = data.get('arrival_driver_name') or None
    if 'meeting_assistance' in data:
        # Properly parse boolean from various input types
        ma_value = data.get('meeting_assistance')
        if isinstance(ma_value, bool):
            request_obj.meeting_assistance = ma_value
        elif isinstance(ma_value, str):
            request_obj.meeting_assistance = ma_value.lower() in ('true', '1', 'yes')
        elif isinstance(ma_value, (int, float)):
            request_obj.meeting_assistance = bool(ma_value)
        else:
            request_obj.meeting_assistance = False
    if 'departure_tax' in data:
        request_obj.departure_tax = data.get('departure_tax') or 'NOT_INCLUDED'
    
    # Update or create rows using row IDs for matching (handles multiple rows per date)
    # Get existing rows indexed by ID
    existing_rows_dict = {row.id: row for row in ItineraryRow.query.filter_by(request_id=request_id).all()}
    submitted_ids = set()
    
    # Import models needed for service deletion
    from app.models.inbound import InboundHotel, InboundTransport, InboundMeal, InboundGuide
    
    # Process each row from the submitted data
    for row_data in rows_data:
        row_date = datetime.strptime(row_data['date'], '%Y-%m-%d').date()
        row_id = row_data.get('id')  # May be None for new rows
        
        # Update existing row or create new one
        if row_id and row_id in existing_rows_dict:
            # Update existing row by ID
            submitted_ids.add(row_id)
            row = existing_rows_dict[row_id]
            # Update all fields
            row.date = row_date
            row.description = row_data['description']
            row.restaurant = row_data.get('restaurant', '')
            row.cash_expense = float(row_data.get('cash_expense', 0))
            row.comment = row_data.get('comment', '')
            row.base_cost = float(row_data.get('base_cost', 0))
            row.cost_unit = row_data.get('cost_unit', COST_UNIT_PER_PERSON)
            row.currency = row_data.get('currency', 'USD')
            row.flag_hotel = row_data.get('flag_hotel', False)
            row.flag_guide = row_data.get('flag_guide', False)
            row.flag_transport = row_data.get('flag_transport', False)
            row.flag_meal = row_data.get('flag_meal', False)
            row.flag_airport = row_data.get('flag_airport', False)
            row.hotel_single_rooms = int(row_data.get('hotel_single_rooms', 0))
            row.hotel_double_rooms = int(row_data.get('hotel_double_rooms', 0))
            row.hotel_triple_rooms = int(row_data.get('hotel_triple_rooms', 0))
            row.hotel_other_rooms = int(row_data.get('hotel_other_rooms', 0))
        else:
            # Create new row (no ID or ID not found)
            row = ItineraryRow(
                request_id=request_id,
                date=row_date,
                description=row_data['description'],
                restaurant=row_data.get('restaurant', ''),
                cash_expense=float(row_data.get('cash_expense', 0)),
                comment=row_data.get('comment', ''),
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
        
        db.session.flush()  # Get the ID for new rows
        
        # Delete existing auto-generated services for this row to avoid duplicates
        InboundHotel.query.filter_by(source_itinerary_id=row.id).delete()
        InboundTransport.query.filter_by(source_itinerary_id=row.id).delete()
        InboundMeal.query.filter_by(source_itinerary_id=row.id).delete()
        InboundGuide.query.filter_by(source_itinerary_id=row.id).delete()
        
        # Regenerate service records based on current flags
        _auto_generate_services(request_obj, row)
    
    # Delete orphaned rows (rows whose IDs are no longer in the submitted data)
    orphaned_rows = [row for row in existing_rows_dict.values() if row.id not in submitted_ids]
    for orphaned_row in orphaned_rows:
        # Delete services first to avoid foreign key violations
        InboundHotel.query.filter_by(source_itinerary_id=orphaned_row.id).delete()
        InboundTransport.query.filter_by(source_itinerary_id=orphaned_row.id).delete()
        InboundMeal.query.filter_by(source_itinerary_id=orphaned_row.id).delete()
        InboundGuide.query.filter_by(source_itinerary_id=orphaned_row.id).delete()
        # Now delete the row itself
        db.session.delete(orphaned_row)
    
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
    
    # Update arrival/departure details
    request_obj.arrival_point = data.get('arrival_point', request_obj.arrival_point)
    request_obj.departure_point = data.get('departure_point', request_obj.departure_point)
    
    # Handle date updates
    if data.get('from_date'):
        request_obj.from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').date()
    if data.get('to_date'):
        request_obj.to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').date()
    
    # Handle time updates
    if data.get('arrival_time'):
        try:
            request_obj.arrival_time = datetime.strptime(data.get('arrival_time'), '%H:%M').time()
        except:
            pass  # Invalid time format, skip
    elif data.get('arrival_time') == '':
        request_obj.arrival_time = None
        
    if data.get('departure_time'):
        try:
            request_obj.departure_time = datetime.strptime(data.get('departure_time'), '%H:%M').time()
        except:
            pass  # Invalid time format, skip
    elif data.get('departure_time') == '':
        request_obj.departure_time = None
    
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

@inbound_bp.route('/api/<int:request_id>/arrival-departure-batches', methods=['GET'])
@login_required
def api_get_arrival_departure_batches(request_id):
    """Get all arrival/departure batches for a request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Import the ArrivalDeparture model
    from app.models.inbound import ArrivalDeparture
    
    batches = ArrivalDeparture.query.filter_by(request_id=request_id).all()
    
    batches_data = []
    for batch in batches:
        # Fallback to legacy fields if new batch fields are empty (for backwards compatibility)
        arrival_point = batch.arrival_point or (batch.point if batch.type == 'ARRIVAL' else '')
        arrival_time = batch.arrival_time or (batch.time if batch.type == 'ARRIVAL' else None)
        departure_point = batch.departure_point or (batch.point if batch.type == 'DEPARTURE' else '')
        departure_time = batch.departure_time or (batch.time if batch.type == 'DEPARTURE' else None)
        driver_name = batch.arrival_driver_name or batch.driver_name or ''
        
        batch_dict = {
            'id': batch.id,
            'arrival_date': batch.arrival_date.strftime('%Y-%m-%d') if batch.arrival_date else '',
            'arrival_point': arrival_point or '',
            'arrival_time': arrival_time.strftime('%H:%M') if arrival_time else '',
            'departure_date': batch.departure_date.strftime('%Y-%m-%d') if batch.departure_date else '',
            'departure_point': departure_point or '',
            'departure_time': departure_time.strftime('%H:%M') if departure_time else '',
            'visa_type': batch.visa_type or 'NOT_INCLUDED',
            'arrival_driver_name': driver_name,
            'meeting_assistance': batch.meeting_assistance,
            'departure_tax': batch.departure_tax or 'NOT_INCLUDED',
            'pax_count': batch.pax_count or 0,
            'batch_name': batch.batch_name or ''
        }
        batches_data.append(batch_dict)
    
    return jsonify({'batches': batches_data})

@inbound_bp.route('/api/<int:request_id>/arrival-departure-batches', methods=['POST'])
@login_required
def api_save_arrival_departure_batches(request_id):
    """Save arrival/departure batches for a request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    batches_data = data.get('batches', [])
    
    # Import the ArrivalDeparture model
    from app.models.inbound import ArrivalDeparture
    
    try:
        # Delete existing batches
        ArrivalDeparture.query.filter_by(request_id=request_id).delete()
        
        # Create new batches
        for batch_data in batches_data:
            # Parse date values
            arrival_date = None
            if batch_data.get('arrival_date'):
                try:
                    arrival_date = datetime.strptime(batch_data['arrival_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            departure_date = None
            if batch_data.get('departure_date'):
                try:
                    departure_date = datetime.strptime(batch_data['departure_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Parse time values
            arrival_time = None
            if batch_data.get('arrival_time'):
                try:
                    arrival_time = datetime.strptime(batch_data['arrival_time'], '%H:%M').time()
                except:
                    pass
            
            departure_time = None
            if batch_data.get('departure_time'):
                try:
                    departure_time = datetime.strptime(batch_data['departure_time'], '%H:%M').time()
                except:
                    pass
            
            # Parse meeting_assistance as boolean
            meeting_assistance = False
            ma_value = batch_data.get('meeting_assistance')
            if isinstance(ma_value, bool):
                meeting_assistance = ma_value
            elif isinstance(ma_value, str):
                meeting_assistance = ma_value in ('1', 'true', 'True', 'yes', 'Yes')
            elif isinstance(ma_value, (int, float)):
                meeting_assistance = bool(ma_value)
            
            # Parse pax_count
            pax_count = 0
            if batch_data.get('pax_count'):
                try:
                    pax_count = int(batch_data['pax_count'])
                except:
                    pax_count = 0
            
            batch = ArrivalDeparture(
                request_id=request_id,
                arrival_date=arrival_date,
                arrival_point=batch_data.get('arrival_point') or None,
                arrival_time=arrival_time,
                departure_date=departure_date,
                departure_point=batch_data.get('departure_point') or None,
                departure_time=departure_time,
                visa_type=batch_data.get('visa_type') or 'NOT_INCLUDED',
                arrival_driver_name=batch_data.get('arrival_driver_name') or None,
                meeting_assistance=meeting_assistance,
                departure_tax=batch_data.get('departure_tax') or 'NOT_INCLUDED',
                pax_count=pax_count,
                batch_name=batch_data.get('batch_name') or None
            )
            db.session.add(batch)
        
        db.session.commit()
        
        # Auto-flag itinerary rows with flag_airport based on arrival/departure dates
        from app.models.inbound import ItineraryRow
        
        # Step 1: Clear ALL flag_airport values for this request (to remove stale flags)
        ItineraryRow.query.filter_by(request_id=request_id).update({'flag_airport': False})
        
        # Step 2: Set flag_airport for all rows matching arrival/departure dates
        for batch_data in batches_data:
            # Parse dates again for auto-flagging
            arrival_date = None
            if batch_data.get('arrival_date'):
                try:
                    arrival_date = datetime.strptime(batch_data['arrival_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            departure_date = None
            if batch_data.get('departure_date'):
                try:
                    departure_date = datetime.strptime(batch_data['departure_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Set flag_airport for ALL rows on arrival date
            if arrival_date:
                arrival_rows = ItineraryRow.query.filter_by(
                    request_id=request_id,
                    date=arrival_date
                ).all()
                for row in arrival_rows:
                    row.flag_airport = True
            
            # Set flag_airport for ALL rows on departure date
            if departure_date:
                departure_rows = ItineraryRow.query.filter_by(
                    request_id=request_id,
                    date=departure_date
                ).all()
                for row in departure_rows:
                    row.flag_airport = True
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Batches saved and itinerary auto-flagged successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving batches: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

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
        
        # Update status to QUOTED when proforma invoice generated
        booking.status = 'QUOTED'
        request_obj.status = 'QUOTED'
        
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

@inbound_bp.route('/<int:request_id>/preview-proforma', methods=['GET'])
@login_required
def preview_proforma(request_id):
    """Preview proforma invoice on a web page before exporting to Word"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    # CREATE BOOKING IF IT DOESN'T EXIST
    if not request_obj.booking_id:
        # Get or create customer
        if request_obj.customer_id:
            customer = Customer.query.get(request_obj.customer_id)
        else:
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
        
        # Create booking with QUOTED status
        booking = Booking()
        booking.reference_number = request_obj.request_number
        booking.user_id = request_obj.user_id
        booking.customer_id = customer.id
        booking.status = 'QUOTED'
        booking.total_amount = request_obj.total_amount or 0
        db.session.add(booking)
        db.session.flush()
        
        # Generate invoice number AFTER flush (so booking.id exists)
        booking.generate_invoice_number()
        
        # Link booking to request
        request_obj.booking_id = booking.id
        request_obj.status = 'QUOTED'
        db.session.commit()
    
    # Collect customer information
    customer_data = {}
    if request_obj.customer_id:
        customer = Customer.query.get(request_obj.customer_id)
        if customer:
            customer_data = {
                'name': customer.name,
                'company_name': customer.company_name,
                'email': customer.email,
                'phone': customer.phone,
                'nationality': customer.nationality
            }
    else:
        # Use contact name from request if no customer linked
        customer_data = {
            'name': request_obj.contact_name,
            'nationality': request_obj.nationality
        }
    
    # Collect tour information
    tour_data = {
        'from_date': request_obj.from_date.strftime('%d %b %Y') if request_obj.from_date else '',
        'to_date': request_obj.to_date.strftime('%d %b %Y') if request_obj.to_date else '',
        'pax': request_obj.pax,
        'nationality': request_obj.nationality
    }
    
    # Collect all service items with date ranges
    service_items = []
    
    # Add hotels
    for hotel in request_obj.inbound_hotels:
        service_items.append({
            'type': 'Hotel',
            'description': f"Hotel: {hotel.hotel_name or 'TBD'} - {hotel.location or ''} ({hotel.room_type or 'Standard'}, {hotel.meal_plan or 'BB'})",
            'date_from': hotel.check_in_date,
            'date_to': hotel.check_out_date,
            'pax': request_obj.pax,
            'unit_price': hotel.cost_per_night or 0,
            'total': hotel.total_cost or 0
        })
    
    # Add transport
    for transport in request_obj.inbound_transports:
        service_items.append({
            'type': 'Transport',
            'description': f"Transport: {transport.vehicle_type or 'Vehicle'} - {transport.pickup_location or ''} to {transport.dropoff_location or ''}",
            'date_from': transport.date,
            'date_to': transport.end_date if transport.end_date else transport.date,
            'pax': request_obj.pax,
            'unit_price': transport.cost or 0,
            'total': transport.cost or 0
        })
    
    # Add meals
    for meal in request_obj.inbound_meals:
        service_items.append({
            'type': 'Meal',
            'description': f"Meal: {meal.meal_type or 'Meal'} at {meal.restaurant or 'Restaurant'} - {meal.location or ''}",
            'date_from': meal.date,
            'date_to': meal.end_date if meal.end_date else meal.date,
            'pax': request_obj.pax,
            'unit_price': meal.cost_per_person or 0,
            'total': meal.total_cost or 0
        })
    
    # Add guides
    for guide in request_obj.inbound_guides:
        service_items.append({
            'type': 'Guide',
            'description': f"Guide: {guide.service_type or 'Guide Service'} - {guide.guide_name or 'TBD'} ({guide.language or 'English'})",
            'date_from': guide.date,
            'date_to': guide.end_date if guide.end_date else guide.date,
            'pax': request_obj.pax,
            'unit_price': guide.cost or 0,
            'total': guide.cost or 0
        })
    
    # Sort service items by date
    service_items.sort(key=lambda x: x['date_from'] if x['date_from'] else datetime.max.date())
    
    # Calculate total
    grand_total = sum(item['total'] for item in service_items)
    
    # Update status to QUOTED when generating proforma invoice preview
    if request_obj.status not in ['QUOTED', 'CONFIRMED']:
        request_obj.status = 'QUOTED'
        
        # Also update booking status if it exists
        if request_obj.booking_id:
            booking = Booking.query.get(request_obj.booking_id)
            if booking:
                booking.status = 'QUOTED'
        
        db.session.commit()
    
    # Prepare invoice data for template
    invoice_data = {
        'invoice_number': request_obj.request_number,
        'invoice_date': datetime.now().strftime('%d %b %Y'),
        'company_name': 'Windows of Jordan',
        'company_address': 'Amman, Jordan',
        'customer': customer_data,
        'tour': tour_data,
        'service_items': service_items,
        'grand_total': grand_total
    }
    
    return render_template('inbound/preview_proforma.html', 
                         request=request_obj,
                         invoice=invoice_data)

@inbound_bp.route('/api/<int:request_id>/update-proforma-prices', methods=['POST'])
@login_required
def update_proforma_prices(request_id):
    """Update pricing for proforma invoice service items"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        # Collect all service models in order
        all_services = []
        for hotel in request_obj.inbound_hotels:
            all_services.append(('hotel', hotel))
        for transport in request_obj.inbound_transports:
            all_services.append(('transport', transport))
        for meal in request_obj.inbound_meals:
            all_services.append(('meal', meal))
        for guide in request_obj.inbound_guides:
            all_services.append(('guide', guide))
        
        # Update each service based on index
        for item in items:
            index = item['index']
            if index < len(all_services):
                service_type, service = all_services[index]
                
                if service_type == 'hotel':
                    service.cost_per_night = item['unit_price']
                    service.total_cost = item['total']
                elif service_type == 'transport':
                    service.cost = item['unit_price']
                elif service_type == 'meal':
                    service.cost_per_person = item['unit_price']
                    service.total_cost = item['total']
                elif service_type == 'guide':
                    service.cost_per_day = item['unit_price']
                    service.total_cost = item['total']
        
        # Recalculate total
        total = sum(item['total'] for item in items)
        request_obj.total_amount = total
        
        # Update booking total if exists
        if request_obj.booking_id:
            booking = Booking.query.get(request_obj.booking_id)
            if booking:
                booking.total_amount = total
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Prices updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@inbound_bp.route('/api/<int:request_id>/update-pricing-mode', methods=['POST'])
@login_required
def update_pricing_mode(request_id):
    """Update pricing mode for proforma invoice (ITEMIZED or LUMPSUM)"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        pricing_mode = data.get('pricing_mode', 'ITEMIZED')
        
        if pricing_mode not in ['ITEMIZED', 'LUMPSUM']:
            return jsonify({'success': False, 'message': 'Invalid pricing mode'}), 400
        
        request_obj.pricing_mode = pricing_mode
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Pricing mode updated to {pricing_mode}'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@inbound_bp.route('/api/<int:request_id>/export-proforma-doc', methods=['GET'])
@login_required
def api_export_proforma_doc(request_id):
    """Export proforma invoice as Word document with service line items"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    try:
        # Collect customer information
        customer_data = {}
        if request_obj.customer_id:
            customer = Customer.query.get(request_obj.customer_id)
            if customer:
                customer_data = {
                    'name': customer.name,
                    'company_name': customer.company_name,
                    'email': customer.email,
                    'phone': customer.phone,
                    'nationality': customer.nationality
                }
        else:
            # Use contact name from request if no customer linked
            customer_data = {
                'name': request_obj.contact_name,
                'nationality': request_obj.nationality
            }
        
        # Collect tour information
        tour_data = {
            'from_date': request_obj.from_date.strftime('%d %b %Y') if request_obj.from_date else '',
            'to_date': request_obj.to_date.strftime('%d %b %Y') if request_obj.to_date else '',
            'pax': request_obj.pax,
            'nationality': request_obj.nationality
        }
        
        # Collect all service items with date ranges
        service_items = []
        
        # Add hotels
        for hotel in request_obj.inbound_hotels:
            service_items.append({
                'description': f"Hotel: {hotel.hotel_name or 'TBD'} - {hotel.location or ''} ({hotel.room_type or 'Standard'}, {hotel.meal_plan or 'BB'})",
                'date_from': hotel.check_in_date,
                'date_to': hotel.check_out_date,
                'pax': request_obj.pax,
                'unit_price': hotel.cost_per_night,
                'total': hotel.total_cost
            })
        
        # Add transport
        for transport in request_obj.inbound_transports:
            service_items.append({
                'description': f"Transport: {transport.vehicle_type or 'Vehicle'} - {transport.pickup_location or ''} to {transport.dropoff_location or ''}",
                'date_from': transport.date,
                'date_to': transport.end_date if transport.end_date else transport.date,
                'pax': request_obj.pax,
                'unit_price': transport.cost,
                'total': transport.cost
            })
        
        # Add meals
        for meal in request_obj.inbound_meals:
            service_items.append({
                'description': f"Meal: {meal.meal_type or 'Meal'} at {meal.restaurant or 'Restaurant'} - {meal.location or ''}",
                'date_from': meal.date,
                'date_to': meal.end_date if meal.end_date else meal.date,
                'pax': request_obj.pax,
                'unit_price': meal.cost_per_person,
                'total': meal.total_cost
            })
        
        # Add guides
        for guide in request_obj.inbound_guides:
            service_items.append({
                'description': f"Guide: {guide.service_type or 'Guide Service'} - {guide.guide_name or 'TBD'} ({guide.language or 'English'})",
                'date_from': guide.date,
                'date_to': guide.end_date if guide.end_date else guide.date,
                'pax': request_obj.pax,
                'unit_price': guide.cost,
                'total': guide.cost
            })
        
        # Sort service items by date
        service_items.sort(key=lambda x: x['date_from'] if x['date_from'] else datetime.max.date())
        
        # Update booking status to QUOTED when exporting proforma
        if request_obj.booking_id:
            booking = Booking.query.get(request_obj.booking_id)
            if booking and booking.status != 'QUOTED':
                booking.status = 'QUOTED'
                request_obj.status = 'QUOTED'
                db.session.commit()
        
        # Prepare invoice data
        invoice_data = {
            'invoice_number': request_obj.request_number,
            'invoice_date': datetime.now().strftime('%d %b %Y'),
            'company_name': 'Windows of Jordan',
            'company_address': 'Amman, Jordan',
            'customer': customer_data,
            'tour': tour_data,
            'service_items': service_items
        }
        
        # Generate Word document
        generator = ProformaDocGenerator()
        output_path = generator.generate_proforma(invoice_data)
        
        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'Proforma_{request_obj.request_number}.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        flash(f'Error generating proforma document: {str(e)}', 'error')
        return redirect(url_for('inbound.view_request', request_id=request_id))

@inbound_bp.route('/api/<int:request_id>/export-voucher-doc', methods=['GET'])
@login_required
def api_export_voucher_doc(request_id):
    """Export trip voucher as Word document with full itinerary"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    try:
        # Collect tour information
        customer_name = request_obj.contact_name
        if request_obj.customer_id:
            customer = Customer.query.get(request_obj.customer_id)
            if customer:
                customer_name = customer.name
        
        tour_data = {
            'guest_name': customer_name,
            'nationality': request_obj.nationality,
            'pax': request_obj.pax,
            'agent_ref': request_obj.agent_ref or '',
            'notes': request_obj.special_note or '',
            'tour_file': request_obj.request_number,
            'from_date': request_obj.from_date.strftime('%d-%b-%y') if request_obj.from_date else '',
            'to_date': request_obj.to_date.strftime('%d-%b-%y') if request_obj.to_date else ''
        }
        
        # Collect arrivals/departures data from flagged transport services
        arrivals_data = []
        arrival_departure_transports = [
            t for t in request_obj.inbound_transports 
            if t.is_arrival or t.is_departure
        ]
        
        if arrival_departure_transports:
            for transport in sorted(arrival_departure_transports, key=lambda x: x.date):
                border = 'Airport'
                if transport.pickup_location and 'border' in transport.pickup_location.lower():
                    border = 'Border'
                
                drop_point = transport.dropoff_location or 'TBA'
                if transport.is_departure:
                    drop_point = transport.pickup_location or 'TBA'
                
                time_str = transport.pickup_time.strftime('%H:%M') if transport.pickup_time else ''
                
                arrivals_data.append({
                    'date': transport.date.strftime('%d-%b-%y'),
                    'border': border,
                    'drop_point': drop_point,
                    'pax': request_obj.pax,
                    'carrier': '',
                    'flight': '',
                    'time': time_str,
                    'note': f"{transport.vehicle_type}" if transport.vehicle_type else ''
                })
        else:
            # Add default arrival/departure if no flagged transfers
            arrivals_data.append({
                'date': request_obj.from_date.strftime('%d-%b-%y') if request_obj.from_date else '',
                'border': 'Airport',
                'drop_point': 'TBA',
                'pax': request_obj.pax,
                'carrier': '',
                'flight': '',
                'time': '',
                'note': ''
            })
            arrivals_data.append({
                'date': request_obj.to_date.strftime('%d-%b-%y') if request_obj.to_date else '',
                'border': 'Airport',
                'drop_point': 'TBA',
                'pax': request_obj.pax,
                'carrier': '',
                'flight': '',
                'time': '',
                'note': ''
            })
        
        # Collect hotel details
        hotels_data = []
        for hotel in request_obj.inbound_hotels:
            # Get room data from itinerary rows for this hotel's date range
            single_rooms = 0
            double_rooms = 0
            twin_rooms = 0
            triple_rooms = 0
            other_rooms = 0
            
            # Find itinerary row with hotel flag for this hotel's check-in date
            for row in request_obj.itinerary_rows:
                if row.flag_hotel and row.date == hotel.check_in_date:
                    single_rooms = row.hotel_single_rooms or 0
                    double_rooms = row.hotel_double_rooms or 0
                    twin_rooms = 0  # We use double for DBL
                    triple_rooms = row.hotel_triple_rooms or 0
                    other_rooms = row.hotel_other_rooms or 0
                    break
            
            hotels_data.append({
                'check_in': hotel.check_in_date.strftime('%d-%b-%y') if hotel.check_in_date else 'TBA',
                'check_out': hotel.check_out_date.strftime('%d-%b-%y') if hotel.check_out_date else 'TBA',
                'name': hotel.hotel_name or 'Hotel TBA',
                'board_basis': hotel.meal_plan or 'BB',
                'note': '',
                'single_rooms': single_rooms,
                'double_rooms': double_rooms,
                'twin_rooms': twin_rooms,
                'triple_rooms': triple_rooms,
                'other_rooms': other_rooms
            })
        
        # Build itinerary organized by service type
        itinerary_days = []
        
        # Group all services by date
        services_by_date = {}
        
        # Add hotels
        for hotel in request_obj.inbound_hotels:
            current_date = hotel.check_in_date
            while current_date < hotel.check_out_date:
                date_key = current_date.strftime('%d-%b-%y')
                if date_key not in services_by_date:
                    services_by_date[date_key] = []
                
                services_by_date[date_key].append(f"Hotel: {hotel.hotel_name or 'TBA'}")
                current_date += timedelta(days=1)
        
        # Add transport
        for transport in request_obj.inbound_transports:
            date_key = transport.date.strftime('%d-%b-%y')
            if date_key not in services_by_date:
                services_by_date[date_key] = []
            
            services_by_date[date_key].append(
                f"Transport: {transport.pickup_location or 'TBA'} → {transport.dropoff_location or 'TBA'}"
            )
        
        # Add meals
        for meal in request_obj.inbound_meals:
            current_date = meal.date
            end_date = meal.end_date if meal.end_date else meal.date
            while current_date <= end_date:
                date_key = current_date.strftime('%d-%b-%y')
                if date_key not in services_by_date:
                    services_by_date[date_key] = []
                
                services_by_date[date_key].append(
                    f"{meal.meal_type or 'Meal'}: {meal.restaurant or 'TBA'}"
                )
                current_date += timedelta(days=1)
        
        # Add guides
        for guide in request_obj.inbound_guides:
            current_date = guide.date
            end_date = guide.end_date if guide.end_date else guide.date
            while current_date <= end_date:
                date_key = current_date.strftime('%d-%b-%y')
                if date_key not in services_by_date:
                    services_by_date[date_key] = []
                
                services_by_date[date_key].append(
                    f"Guide: {guide.service_type or 'Guide Service'} ({guide.language or 'English'})"
                )
                current_date += timedelta(days=1)
        
        # Convert to list format
        for date_key in sorted(services_by_date.keys(), key=lambda x: datetime.strptime(x, '%d-%b-%y')):
            description = '\n'.join(services_by_date[date_key])
            itinerary_days.append({
                'date': date_key,
                'description': description
            })
        
        # Collect meals data
        meals_data = []
        for meal in request_obj.inbound_meals:
            start_date = meal.date
            end_date = meal.end_date if meal.end_date else meal.date
            
            # Generate entry for each day in range
            current_date = start_date
            while current_date <= end_date:
                meals_data.append({
                    'date': current_date.strftime('%d-%b-%y'),
                    'restaurant': meal.restaurant or 'Restaurant',
                    'meal_type': meal.meal_type or 'Lunch',
                    'pax': request_obj.pax,
                    'note': ''
                })
                current_date += timedelta(days=1)
        
        # Collect transport data
        transport_data = []
        for transport in request_obj.inbound_transports:
            start_date = transport.date
            end_date = transport.end_date if transport.end_date else transport.date
            
            # Generate entry for date range
            current_date = start_date
            while current_date <= end_date:
                transport_data.append({
                    'time': f"{current_date.strftime('%d-%b-%y')} - {end_date.strftime('%d-%b-%y')}",
                    'name': transport.vehicle_type or 'Vehicle',
                    'note': f"{transport.pickup_location or ''} to {transport.dropoff_location or ''}",
                    'driver': ''
                })
                break  # Only add once for range
        
        # Collect guides data
        guides_data = []
        for guide in request_obj.inbound_guides:
            guides_data.append({
                'from_date': guide.date.strftime('%d-%b-%y') if guide.date else '',
                'to_date': guide.end_date.strftime('%d-%b-%y') if guide.end_date else guide.date.strftime('%d-%b-%y'),
                'name': guide.guide_name or 'TBA',
                'language': guide.language or 'English',
                'note': guide.service_type or ''
            })
        
        # Collect cash expenses data
        cash_expenses_data = []
        for expense in request_obj.inbound_cash_expenses:
            start_date = expense.date
            end_date = expense.end_date if expense.end_date else expense.date
            
            # Generate entry for each day in range
            current_date = start_date
            while current_date <= end_date:
                amount_display = f"{expense.currency} {expense.amount:.2f}"
                if expense.is_per_person:
                    amount_display += " pp"
                
                cash_expenses_data.append({
                    'date': current_date.strftime('%d-%b-%y'),
                    'category': expense.category or 'Expense',
                    'description': expense.description,
                    'amount': amount_display,
                    'driver_name': expense.driver_name or '',
                    'note': expense.location or ''
                })
                current_date += timedelta(days=1)
        
        # Prepare voucher data
        voucher_data = {
            'tour_file': request_obj.request_number,
            'company_name': 'Windows of Jordan',
            'tour': tour_data,
            'arrivals': arrivals_data,
            'hotels': hotels_data,
            'itinerary_days': itinerary_days,
            'meals': meals_data,
            'transport': transport_data,
            'guides': guides_data,
            'cash_expenses': cash_expenses_data
        }
        
        # Generate Word document
        generator = VoucherTripPlanGenerator()
        output_path = generator.generate_voucher(voucher_data)
        
        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'Voucher_{request_obj.request_number}.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        flash(f'Error generating voucher document: {str(e)}', 'error')
        return redirect(url_for('inbound.view_request', id=request_id))

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
        
        # Confirm the booking and move to CONFIRMED status
        booking.status = 'CONFIRMED'
        request_obj.status = 'CONFIRMED'
        
        # Update all service items to CONFIRMED status
        for service_item in booking.service_items:
            service_item.status = 'CONFIRMED'
        
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

@inbound_bp.route('/api/<int:request_id>/start-processing', methods=['POST'])
@login_required
def api_start_processing(request_id):
    """Start processing an itinerary - change status from CONFIRMED to PROCESSING"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if request_obj.status != 'CONFIRMED':
        return jsonify({
            'success': False,
            'message': 'Itinerary must be CONFIRMED before processing can start'
        }), 400
    
    try:
        # Change status to PROCESSING (operations active)
        request_obj.status = 'PROCESSING'
        
        if request_obj.booking_id:
            booking = Booking.query.get(request_obj.booking_id)
            if booking:
                booking.status = 'PROCESSING'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Processing started successfully. Operations are now active.',
            'new_status': 'PROCESSING'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error starting processing: {str(e)}'
        }), 500

# ============================================================
# RUN-DOWN PLAN DASHBOARD
# ============================================================

def get_status_color(status):
    """Map booking status to color for visual coding"""
    status_colors = {
        'QUOTED': '#3b82f6',  # Blue
        'PROFORMA_GENERATED': '#8b5cf6',  # Purple
        'BOOKED': '#eab308',  # Yellow/Pending
        'CONFIRMED': '#22c55e',  # Green
        'COMPLETED': '#10b981',  # Green
        'CANCELLED': '#ef4444',  # Red
        'REQUEST': '#64748b',  # Gray
    }
    return status_colors.get(status, '#94a3b8')

@inbound_bp.route('/run-down')
@login_required
def run_down_plan():
    """Run-down plan dashboard showing all PROCESSING itineraries"""
    # Get all PROCESSING itineraries for current user
    processing_requests = InboundRequest.query.filter_by(
        user_id=current_user.id,
        status='PROCESSING'
    ).order_by(InboundRequest.from_date).all()
    
    # Get counts by status for stats bar
    status_counts = {
        'REQUEST': InboundRequest.query.filter_by(user_id=current_user.id, status='REQUEST').count(),
        'QUOTED': InboundRequest.query.filter_by(user_id=current_user.id, status='QUOTED').count(),
        'CONFIRMED': InboundRequest.query.filter_by(user_id=current_user.id, status='CONFIRMED').count(),
        'PROCESSING': InboundRequest.query.filter_by(user_id=current_user.id, status='PROCESSING').count(),
        'COMPLETED': InboundRequest.query.filter_by(user_id=current_user.id, status='COMPLETED').count()
    }
    
    return render_template('inbound/run_down.html',
                         processing_requests=processing_requests,
                         status_counts=status_counts)

@inbound_bp.route('/api/run-down-data')
@login_required
def api_run_down_data():
    """API endpoint for run-down plan data"""
    from app.models.customer import Customer
    from app.models.service import ServiceConfirmation
    from app.models.supplier import Supplier
    from sqlalchemy import and_, or_
    
    # Get filter parameters
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    status_filter = request.args.get('status', '')
    booking_filter = request.args.get('booking', '')
    
    # Parse dates
    try:
        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        else:
            date_from = datetime.now().date() - timedelta(days=7)
        
        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        else:
            date_to = datetime.now().date() + timedelta(days=30)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Build query - join ServiceItem with Booking and Customer
    query = db.session.query(
        ServiceItem.start_date.label('service_date'),
        ServiceItem.service_type,
        ServiceItem.description,
        ServiceItem.status.label('service_status'),
        ServiceItem.amount,
        Booking.reference_number.label('booking_number'),
        Booking.status.label('booking_status'),
        Booking.id.label('booking_id'),
        Customer.first_name,
        Customer.last_name,
        Customer.company_name,
        InboundRequest.pax,
        InboundRequest.contact_name,
        InboundRequest.id.label('request_id')
    ).join(
        Booking, ServiceItem.booking_id == Booking.id
    ).outerjoin(
        Customer, Booking.customer_id == Customer.id
    ).outerjoin(
        InboundRequest, Booking.id == InboundRequest.booking_id
    ).filter(
        Booking.user_id == current_user.id
    ).filter(
        and_(
            ServiceItem.start_date >= date_from,
            ServiceItem.start_date <= date_to
        )
    )
    
    # Apply status filter
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    
    # Apply booking number filter
    if booking_filter:
        query = query.filter(Booking.reference_number.contains(booking_filter))
    
    # Order by date
    query = query.order_by(ServiceItem.start_date, Booking.reference_number)
    
    # Execute query
    results = query.all()
    
    # Format results by date
    run_down_data = {}
    for row in results:
        service_date = row.service_date.strftime('%Y-%m-%d')
        
        # Initialize date bucket if not exists
        if service_date not in run_down_data:
            run_down_data[service_date] = {
                'date': service_date,
                'date_formatted': row.service_date.strftime('%A, %B %d, %Y'),
                'services': []
            }
        
        # Build guest name
        if row.first_name and row.last_name:
            guest_name = f"{row.first_name} {row.last_name}"
        elif row.company_name:
            guest_name = row.company_name
        elif row.contact_name:
            guest_name = row.contact_name
        else:
            guest_name = "TBA"
        
        # Add service to date bucket
        service_data = {
            'booking_number': row.booking_number,
            'booking_id': row.booking_id,
            'request_id': row.request_id,
            'guest_name': guest_name,
            'pax': row.pax or 1,
            'service_type': row.service_type,
            'description': row.description or f"{row.service_type} Service",
            'amount': row.amount or 0,
            'status': row.booking_status,
            'status_color': get_status_color(row.booking_status),
            'service_status': row.service_status
        }
        
        run_down_data[service_date]['services'].append(service_data)
    
    # Convert to sorted list
    sorted_data = sorted(run_down_data.values(), key=lambda x: x['date'])
    
    return jsonify({
        'success': True,
        'data': sorted_data,
        'total_days': len(sorted_data),
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d')
    })

@inbound_bp.route('/run-down-export-excel')
@login_required
def run_down_export_excel():
    """Export run-down plan to Excel"""
    from app.models.customer import Customer
    from sqlalchemy import and_
    import io
    from flask import send_file
    
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        flash('Excel export requires openpyxl package', 'error')
        return redirect(url_for('inbound.run_down_plan'))
    
    # Get filter parameters
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    status_filter = request.args.get('status', '')
    booking_filter = request.args.get('booking', '')
    
    # Parse dates
    try:
        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        else:
            date_from = datetime.now().date() - timedelta(days=7)
        
        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        else:
            date_to = datetime.now().date() + timedelta(days=30)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('inbound.run_down_plan'))
    
    # Build query
    query = db.session.query(
        ServiceItem.start_date.label('service_date'),
        ServiceItem.service_type,
        ServiceItem.description,
        ServiceItem.status.label('service_status'),
        ServiceItem.amount,
        Booking.reference_number.label('booking_number'),
        Booking.status.label('booking_status'),
        Customer.first_name,
        Customer.last_name,
        Customer.company_name,
        InboundRequest.pax,
        InboundRequest.contact_name
    ).join(
        Booking, ServiceItem.booking_id == Booking.id
    ).outerjoin(
        Customer, Booking.customer_id == Customer.id
    ).outerjoin(
        InboundRequest, Booking.id == InboundRequest.booking_id
    ).filter(
        Booking.user_id == current_user.id
    ).filter(
        and_(
            ServiceItem.start_date >= date_from,
            ServiceItem.start_date <= date_to
        )
    )
    
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    if booking_filter:
        query = query.filter(Booking.reference_number.contains(booking_filter))
    
    query = query.order_by(ServiceItem.start_date, Booking.reference_number)
    results = query.all()
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Run-Down Plan"
    
    # Header styling
    header_fill = PatternFill(start_color="FFBF00", end_color="FFBF00", fill_type="solid")
    header_font = Font(bold=True, color="000000", size=12)
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Title
    ws.merge_cells('A1:H1')
    ws['A1'] = f"Run-Down Plan: {date_from.strftime('%B %d, %Y')} - {date_to.strftime('%B %d, %Y')}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal="center")
    
    # Headers
    headers = ['Date', 'Booking #', 'Guest / Group', 'Pax', 'Service Type', 'Description', 'Amount', 'Status']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Data rows
    row = 4
    for result in results:
        # Guest name
        if result.first_name and result.last_name:
            guest_name = f"{result.first_name} {result.last_name}"
        elif result.company_name:
            guest_name = result.company_name
        elif result.contact_name:
            guest_name = result.contact_name
        else:
            guest_name = "TBA"
        
        ws.cell(row=row, column=1, value=result.service_date.strftime('%Y-%m-%d')).border = thin_border
        ws.cell(row=row, column=2, value=result.booking_number).border = thin_border
        ws.cell(row=row, column=3, value=guest_name).border = thin_border
        ws.cell(row=row, column=4, value=result.pax or 1).border = thin_border
        ws.cell(row=row, column=5, value=result.service_type).border = thin_border
        ws.cell(row=row, column=6, value=result.description or f"{result.service_type} Service").border = thin_border
        ws.cell(row=row, column=7, value=result.amount or 0).border = thin_border
        ws.cell(row=row, column=7, value=f"${result.amount or 0:.2f}").border = thin_border
        ws.cell(row=row, column=8, value=result.booking_status).border = thin_border
        
        row += 1
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 35
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 18
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"RunDown_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@inbound_bp.route('/run-down-export-pdf')
@login_required
def run_down_export_pdf():
    """Export run-down plan to PDF"""
    from app.models.customer import Customer
    from sqlalchemy import and_
    
    # Get filter parameters
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    status_filter = request.args.get('status', '')
    booking_filter = request.args.get('booking', '')
    
    # Parse dates
    try:
        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        else:
            date_from = datetime.now().date() - timedelta(days=7)
        
        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        else:
            date_to = datetime.now().date() + timedelta(days=30)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('inbound.run_down_plan'))
    
    # Build query
    query = db.session.query(
        ServiceItem.start_date.label('service_date'),
        ServiceItem.service_type,
        ServiceItem.description,
        ServiceItem.amount,
        Booking.reference_number.label('booking_number'),
        Booking.status.label('booking_status'),
        Customer.first_name,
        Customer.last_name,
        Customer.company_name,
        InboundRequest.pax,
        InboundRequest.contact_name
    ).join(
        Booking, ServiceItem.booking_id == Booking.id
    ).outerjoin(
        Customer, Booking.customer_id == Customer.id
    ).outerjoin(
        InboundRequest, Booking.id == InboundRequest.booking_id
    ).filter(
        Booking.user_id == current_user.id
    ).filter(
        and_(
            ServiceItem.start_date >= date_from,
            ServiceItem.start_date <= date_to
        )
    )
    
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    if booking_filter:
        query = query.filter(Booking.reference_number.contains(booking_filter))
    
    query = query.order_by(ServiceItem.start_date, Booking.reference_number)
    results = query.all()
    
    # Group by date
    run_down_data = {}
    for row in results:
        service_date = row.service_date.strftime('%Y-%m-%d')
        if service_date not in run_down_data:
            run_down_data[service_date] = {
                'date': service_date,
                'date_formatted': row.service_date.strftime('%A, %B %d, %Y'),
                'services': []
            }
        
        if row.first_name and row.last_name:
            guest_name = f"{row.first_name} {row.last_name}"
        elif row.company_name:
            guest_name = row.company_name
        elif row.contact_name:
            guest_name = row.contact_name
        else:
            guest_name = "TBA"
        
        run_down_data[service_date]['services'].append({
            'booking_number': row.booking_number,
            'guest_name': guest_name,
            'pax': row.pax or 1,
            'service_type': row.service_type,
            'description': row.description or f"{row.service_type} Service",
            'amount': row.amount or 0,
            'status': row.booking_status,
            'status_color': get_status_color(row.booking_status)
        })
    
    sorted_data = sorted(run_down_data.values(), key=lambda x: x['date'])
    
    # Calculate total services
    total_services = sum(len(day['services']) for day in sorted_data)
    
    # Render PDF template
    return render_template('inbound/run_down_pdf.html',
                         data=sorted_data,
                         date_from=date_from,
                         date_to=date_to,
                         total_days=len(sorted_data),
                         total_services=total_services,
                         current_time=datetime.now())


# WIZARD DISABLED - User requested NO wizard workflow
# @inbound_bp.route('/wizard/step1', methods=['GET', 'POST'])
# @login_required
def wizard_step1_DISABLED():
    """Wizard Step 1: Arrival & Departure Details"""
    from flask import session
    
    if request.method == 'POST':
        # Get arrival and departure dates
        arrival_date = request.form.get('arrival_date')
        departure_date = request.form.get('departure_date')
        
        # Calculate number of days
        from_dt = datetime.strptime(arrival_date, '%Y-%m-%d').date()
        to_dt = datetime.strptime(departure_date, '%Y-%m-%d').date()
        no_of_days = (to_dt - from_dt).days + 1
        
        # Get customer_id if selected, otherwise use contact_name
        customer_id = request.form.get('customer_id', '')
        
        # Store wizard data in session
        session['wizard_data'] = {
            # Arrival/Departure info
            'arrival_point': request.form.get('arrival_point'),
            'arrival_date': arrival_date,
            'arrival_time': request.form.get('arrival_time', ''),
            'arrival_reference': request.form.get('arrival_reference', ''),
            'departure_point': request.form.get('departure_point'),
            'departure_date': departure_date,
            'departure_time': request.form.get('departure_time', ''),
            'departure_reference': request.form.get('departure_reference', ''),
            
            # Contact & Group info
            'customer_id': customer_id if customer_id else None,
            'contact_name': request.form.get('contact_name'),
            'agent_ref': request.form.get('agent_ref', ''),
            'customer_type': request.form.get('customer_type', 'AGENCY'),
            'nationality': request.form.get('nationality'),
            'pax': int(request.form.get('pax', 1)),
            'special_note': request.form.get('special_note', ''),
            
            # Calculated fields
            'from_date': arrival_date,  # Use arrival as start
            'to_date': departure_date,   # Use departure as end
            'no_of_days': no_of_days,
            
            # Initialize service collections
            'hotels': [],
            'transports': [],
            'meals': [],
            'guides': []
        }
        session.modified = True
        return redirect(url_for('inbound.wizard_step2'))
    
    # GET request - pass any existing wizard data to template
    wizard_data = session.get('wizard_data', {})
    return render_template('inbound/wizard_step1.html', wizard_data=wizard_data)


# @inbound_bp.route('/wizard/step2', methods=['GET', 'POST'])
# @login_required
def wizard_step2_DISABLED():
    """Wizard Step 2: Add All Services"""
    from flask import session
    
    if 'wizard_data' not in session:
        flash('Please start from step 1', 'warning')
        return redirect(url_for('inbound.wizard_step1'))
    
    if request.method == 'POST':
        # Parse services from form (handles both 2-level and 3-level nested structures)
        services_data = {}
        for key, value in request.form.items():
            if key.startswith('services['):
                parts = key.split('[')
                index = parts[1].split(']')[0]
                
                if index not in services_data:
                    services_data[index] = {}
                
                # Check if this is a nested structure like services[0][rooms][0][field]
                if len(parts) > 3 and 'rooms' in key:
                    # This is a hotel room field: services[INDEX][rooms][ROOM_INDEX][FIELD]
                    room_index = parts[3].split(']')[0]
                    field_name = parts[4].split(']')[0]
                    
                    if 'rooms' not in services_data[index]:
                        services_data[index]['rooms'] = {}
                    if room_index not in services_data[index]['rooms']:
                        services_data[index]['rooms'][room_index] = {}
                    
                    services_data[index]['rooms'][room_index][field_name] = value
                else:
                    # Simple field: services[INDEX][FIELD]
                    field = parts[2].split(']')[0]
                    services_data[index][field] = value
        
        # Validate at least one service
        if not services_data:
            flash('Please add at least one service before continuing to review', 'warning')
            wizard_data = session.get('wizard_data', {})
            return render_template('inbound/wizard_step2.html', wizard_data=wizard_data)
        
        # Store services in session
        session['wizard_data']['services'] = services_data
        session.modified = True
        
        # Redirect to step 3 (Review)
        return redirect(url_for('inbound.wizard_step3'))
    
    # GET request - pass wizard data to template
    wizard_data = session.get('wizard_data', {})
    return render_template('inbound/wizard_step2.html', wizard_data=wizard_data)


# @inbound_bp.route('/wizard/step3', methods=['GET', 'POST'])
# @login_required
def wizard_step3_DISABLED():
    """Wizard Step 3: Review & Create"""
    from flask import session
    
    if 'wizard_data' not in session:
        flash('Please start from step 1', 'warning')
        return redirect(url_for('inbound.wizard_step1'))
    
    if request.method == 'POST':
        wizard_data = session['wizard_data']
        
        # Helper functions
        def safe_int(value, default=0):
            """Safely convert to int, handling empty strings"""
            if not value or value == '':
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        def safe_float(value, default=0.0):
            """Safely convert to float, handling empty strings"""
            if not value or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def date_range(start_date, end_date):
            """Generate list of dates between start and end (inclusive for start, exclusive for end for hotel nights)"""
            from datetime import timedelta
            dates = []
            current = start_date
            while current < end_date:
                dates.append(current)
                current += timedelta(days=1)
            return dates
        
        # Get services from session
        services_data = wizard_data.get('services', {})
        
        # Validate that we have at least one service
        if not services_data:
            flash('Please add at least one service before creating the tour', 'error')
            return redirect(url_for('inbound.wizard_step2'))
        
        # Start transaction
        try:
            from datetime import timedelta
            from_date = datetime.strptime(wizard_data['from_date'], '%Y-%m-%d').date()
            to_date = datetime.strptime(wizard_data['to_date'], '%Y-%m-%d').date()
            
            # Create InboundRequest
            request_obj = InboundRequest(
                request_number=InboundRequest.generate_request_number(),
                from_date=from_date,
                to_date=to_date,
                no_of_days=wizard_data['no_of_days'],
                customer_type=wizard_data['customer_type'],
                contact_name=wizard_data['contact_name'],
                customer_id=wizard_data.get('customer_id'),
                agent_ref=wizard_data.get('agent_ref', ''),
                nationality=wizard_data['nationality'],
                pax=wizard_data['pax'],
                special_note=wizard_data.get('special_note', ''),
                user_id=current_user.id,
                status=STATUS_REQUEST
            )
            
            db.session.add(request_obj)
            db.session.flush()  # Get the ID
            
            # Create arrival transport if driver/vehicle specified
            if wizard_data.get('arrival_driver') or wizard_data.get('arrival_vehicle'):
                arrival_time_str = wizard_data.get('arrival_time')
                arrival_time = None
                if arrival_time_str:
                    try:
                        arrival_time = datetime.strptime(arrival_time_str, '%H:%M').time()
                    except:
                        pass
                
                arrival_transport = InboundTransport(
                    request_id=request_obj.id,
                    date=from_date,
                    vehicle_type=wizard_data.get('arrival_vehicle'),
                    driver_name=wizard_data.get('arrival_driver'),
                    pickup_location=wizard_data.get('arrival_point', ''),
                    dropoff_location='Hotel',  # Default dropoff
                    pickup_time=arrival_time,
                    is_airport_transfer=True,
                    is_arrival=True,
                    cost=0.0,
                    currency='USD'
                )
                db.session.add(arrival_transport)
            
            # Create departure transport if driver/vehicle specified
            if wizard_data.get('departure_driver') or wizard_data.get('departure_vehicle'):
                departure_time_str = wizard_data.get('departure_time')
                departure_time = None
                if departure_time_str:
                    try:
                        departure_time = datetime.strptime(departure_time_str, '%H:%M').time()
                    except:
                        pass
                
                departure_transport = InboundTransport(
                    request_id=request_obj.id,
                    date=to_date,
                    vehicle_type=wizard_data.get('departure_vehicle'),
                    driver_name=wizard_data.get('departure_driver'),
                    pickup_location='Hotel',  # Default pickup
                    dropoff_location=wizard_data.get('departure_point', ''),
                    pickup_time=departure_time,
                    is_airport_transfer=True,
                    is_departure=True,
                    cost=0.0,
                    currency='USD'
                )
                db.session.add(departure_transport)
            
            # Track itinerary rows by date to merge services on same dates
            itinerary_by_date = {}
            
            # Process each service and generate itinerary rows
            for index in sorted(services_data.keys(), key=int):
                service = services_data[index]
                service_type = service.get('type')
                
                if service_type == 'hotel':
                    # Hotel: create rows for each night with inherited rooming
                    check_in = datetime.strptime(service['check_in_date'], '%Y-%m-%d').date()
                    check_out = datetime.strptime(service['check_out_date'], '%Y-%m-%d').date()
                    
                    # Validate hotel dates
                    if check_out <= check_in:
                        raise ValueError(f"Hotel check-out date must be after check-in date")
                    
                    hotel_name = service.get('hotel_name', '')
                    location = service.get('location', '')
                    
                    # Room distribution (inherited across all nights)
                    single = safe_int(service.get('single_rooms'))
                    double = safe_int(service.get('double_rooms'))
                    triple = safe_int(service.get('triple_rooms'))
                    other = safe_int(service.get('other_rooms'))
                    
                    cost = safe_float(service.get('cost'))
                    cost_unit = service.get('cost_unit', COST_UNIT_PER_PERSON)
                    
                    # Generate description
                    desc = f"Hotel: {hotel_name or 'TBD'}"
                    if location:
                        desc += f" ({location})"
                    
                    # Create itinerary row for each night
                    for night_date in date_range(check_in, check_out):
                        if night_date not in itinerary_by_date:
                            itinerary_by_date[night_date] = {
                                'date': night_date,
                                'description': desc,
                                'base_cost': cost,
                                'cost_unit': cost_unit,
                                'flag_hotel': True,
                                'hotel_single_rooms': single,
                                'hotel_double_rooms': double,
                                'hotel_triple_rooms': triple,
                                'hotel_other_rooms': other,
                                'flag_transport': False,
                                'flag_meal': False,
                                'flag_guide': False
                            }
                        else:
                            # Merge with existing
                            itinerary_by_date[night_date]['description'] += f" | {desc}"
                            itinerary_by_date[night_date]['base_cost'] += cost
                            itinerary_by_date[night_date]['flag_hotel'] = True
                            itinerary_by_date[night_date]['hotel_single_rooms'] = single
                            itinerary_by_date[night_date]['hotel_double_rooms'] = double
                            itinerary_by_date[night_date]['hotel_triple_rooms'] = triple
                            itinerary_by_date[night_date]['hotel_other_rooms'] = other
                
                elif service_type == 'transport':
                    # Transport: single date
                    transport_date = datetime.strptime(service['date'], '%Y-%m-%d').date()
                    pickup = service.get('pickup_location', 'TBD')
                    dropoff = service.get('dropoff_location', 'TBD')
                    vehicle = service.get('vehicle_type', '')
                    cost = safe_float(service.get('cost'))
                    cost_unit = service.get('cost_unit', COST_UNIT_PER_GROUP)
                    
                    desc = f"Transport: {pickup} → {dropoff}"
                    if vehicle:
                        desc += f" ({vehicle})"
                    
                    if transport_date not in itinerary_by_date:
                        itinerary_by_date[transport_date] = {
                            'date': transport_date,
                            'description': desc,
                            'base_cost': cost,
                            'cost_unit': cost_unit,
                            'flag_hotel': False,
                            'hotel_single_rooms': 0,
                            'hotel_double_rooms': 0,
                            'hotel_triple_rooms': 0,
                            'hotel_other_rooms': 0,
                            'flag_transport': True,
                            'flag_meal': False,
                            'flag_guide': False
                        }
                    else:
                        # Merge with existing
                        itinerary_by_date[transport_date]['description'] += f" | {desc}"
                        itinerary_by_date[transport_date]['base_cost'] += cost
                        itinerary_by_date[transport_date]['flag_transport'] = True
                
                elif service_type == 'meal':
                    # Meal: single date or date range (FROM/TO dates)
                    meal_from = datetime.strptime(service['from_date'], '%Y-%m-%d').date()
                    meal_to_str = service.get('to_date', '')
                    meal_to = datetime.strptime(meal_to_str, '%Y-%m-%d').date() if meal_to_str else meal_from
                    meal_type = service.get('meal_type', 'Meal')
                    restaurant = service.get('restaurant', 'TBD')
                    cost = safe_float(service.get('cost'))
                    cost_unit = service.get('cost_unit', COST_UNIT_PER_PERSON)
                    
                    desc = f"{meal_type} at {restaurant}"
                    
                    # Create row for each day in range (inclusive)
                    meal_to_inclusive = meal_to + timedelta(days=1)
                    for meal_date in date_range(meal_from, meal_to_inclusive):
                        if meal_date not in itinerary_by_date:
                            itinerary_by_date[meal_date] = {
                                'date': meal_date,
                                'description': desc,
                                'base_cost': cost,
                                'cost_unit': cost_unit,
                                'flag_hotel': False,
                                'hotel_single_rooms': 0,
                                'hotel_double_rooms': 0,
                                'hotel_triple_rooms': 0,
                                'hotel_other_rooms': 0,
                                'flag_transport': False,
                                'flag_meal': True,
                                'flag_guide': False
                            }
                        else:
                            # Merge with existing
                            itinerary_by_date[meal_date]['description'] += f" | {desc}"
                            itinerary_by_date[meal_date]['base_cost'] += cost
                            itinerary_by_date[meal_date]['flag_meal'] = True
                
                elif service_type == 'guide':
                    # Guide: single date or date range (optional TO date)
                    guide_from = datetime.strptime(service['from_date'], '%Y-%m-%d').date()
                    guide_to_str = service.get('to_date', '')
                    guide_to = datetime.strptime(guide_to_str, '%Y-%m-%d').date() if guide_to_str else guide_from
                    guide_type = service.get('guide_type', 'Guide Service')
                    language = service.get('language', '')
                    cost = safe_float(service.get('cost'))
                    cost_unit = service.get('cost_unit', COST_UNIT_PER_GROUP)
                    
                    desc = f"{guide_type}"
                    if language:
                        desc += f" ({language})"
                    
                    # Create row for each day in range (inclusive)
                    guide_to_inclusive = guide_to + timedelta(days=1)
                    for guide_date in date_range(guide_from, guide_to_inclusive):
                        if guide_date not in itinerary_by_date:
                            itinerary_by_date[guide_date] = {
                                'date': guide_date,
                                'description': desc,
                                'base_cost': cost,
                                'cost_unit': cost_unit,
                                'flag_hotel': False,
                                'hotel_single_rooms': 0,
                                'hotel_double_rooms': 0,
                                'hotel_triple_rooms': 0,
                                'hotel_other_rooms': 0,
                                'flag_transport': False,
                                'flag_meal': False,
                                'flag_guide': True
                            }
                        else:
                            # Merge with existing
                            itinerary_by_date[guide_date]['description'] += f" | {desc}"
                            itinerary_by_date[guide_date]['base_cost'] += cost
                            itinerary_by_date[guide_date]['flag_guide'] = True
            
            # Create ItineraryRow objects from merged data
            for row_date in sorted(itinerary_by_date.keys()):
                row_data = itinerary_by_date[row_date]
                
                row = ItineraryRow(
                    request_id=request_obj.id,
                    date=row_data['date'],
                    description=row_data['description'],
                    base_cost=row_data['base_cost'],
                    cost_unit=row_data['cost_unit'],
                    currency='USD',
                    flag_hotel=row_data['flag_hotel'],
                    flag_transport=row_data['flag_transport'],
                    flag_meal=row_data['flag_meal'],
                    flag_guide=row_data['flag_guide'],
                    hotel_single_rooms=row_data['hotel_single_rooms'],
                    hotel_double_rooms=row_data['hotel_double_rooms'],
                    hotel_triple_rooms=row_data['hotel_triple_rooms'],
                    hotel_other_rooms=row_data['hotel_other_rooms']
                )
                
                db.session.add(row)
            
            # Create service records directly from service data
            for service_idx, service in services_data.items():
                service_type = service.get('type')
                
                if service_type == 'transport':
                    # Create InboundTransport record with arrival/departure flags
                    transport_date = datetime.strptime(service['date'], '%Y-%m-%d').date()
                    from_date_str = service.get('from_date')
                    to_date_str = service.get('to_date')
                    
                    from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date() if from_date_str else transport_date
                    to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date() if to_date_str else transport_date
                    
                    pickup_time_str = service.get('time')
                    pickup_time = None
                    if pickup_time_str:
                        try:
                            pickup_time = datetime.strptime(pickup_time_str, '%H:%M').time()
                        except:
                            pass
                    
                    transport = InboundTransport(
                        request_id=request_obj.id,
                        date=from_date,
                        end_date=to_date if to_date != from_date else None,
                        vehicle_type=service.get('vehicle_type'),
                        driver_name=service.get('driver_name'),
                        pickup_location=service.get('pickup_location'),
                        dropoff_location=service.get('dropoff_location'),
                        pickup_time=pickup_time,
                        is_arrival=service.get('is_arrival') == '1',
                        is_departure=service.get('is_departure') == '1',
                        cost=safe_float(service.get('cost', 0)),
                        currency='USD'
                    )
                    db.session.add(transport)
                
                elif service_type == 'meal':
                    # Create InboundMeal records
                    meal_from = datetime.strptime(service['from_date'], '%Y-%m-%d').date()
                    meal_to_str = service.get('to_date', '')
                    meal_to = datetime.strptime(meal_to_str, '%Y-%m-%d').date() if meal_to_str else meal_from
                    
                    meal = InboundMeal(
                        request_id=request_obj.id,
                        date=meal_from,
                        end_date=meal_to if meal_to != meal_from else None,
                        meal_type=service.get('meal_type'),
                        restaurant=service.get('restaurant'),
                        cost_per_person=safe_float(service.get('cost', 0)),
                        currency='USD'
                    )
                    db.session.add(meal)
                
                elif service_type == 'guide':
                    # Create InboundGuide records (single date or date range)
                    guide_from = datetime.strptime(service['from_date'], '%Y-%m-%d').date()
                    guide_to_str = service.get('to_date', '')
                    guide_to = datetime.strptime(guide_to_str, '%Y-%m-%d').date() if guide_to_str else guide_from
                    
                    guide = InboundGuide(
                        request_id=request_obj.id,
                        date=guide_from,
                        end_date=guide_to if guide_to != guide_from else None,
                        service_type=service.get('guide_type'),
                        language=service.get('language', 'English'),
                        cost=safe_float(service.get('cost', 0)),
                        currency='USD'
                    )
                    db.session.add(guide)
                
                elif service_type == 'hotel':
                    # Create InboundHotel record
                    check_in = datetime.strptime(service['check_in_date'], '%Y-%m-%d').date()
                    check_out = datetime.strptime(service['check_out_date'], '%Y-%m-%d').date()
                    nights = (check_out - check_in).days
                    
                    hotel = InboundHotel(
                        request_id=request_obj.id,
                        hotel_name=service.get('hotel_name'),
                        location=service.get('location'),
                        check_in_date=check_in,
                        check_out_date=check_out,
                        nights=nights,
                        total_cost=safe_float(service.get('cost', 0)),
                        currency='USD'
                    )
                    db.session.add(hotel)
            
            # Calculate total
            db.session.flush()
            request_obj.calculate_total()
            
            # Commit transaction
            db.session.commit()
            
            # Clear wizard data from session
            session.pop('wizard_data', None)
            
            flash(f'Tour itinerary {request_obj.request_number} created successfully!', 'success')
            return redirect(url_for('inbound.view_request', id=request_obj.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating itinerary: {str(e)}', 'error')
            return redirect(url_for('inbound.wizard_step2'))
    
    # GET request - show review page
    wizard_data = session.get('wizard_data', {})
    return render_template('inbound/wizard_step3.html', wizard_data=wizard_data)
@inbound_bp.route('/api/<int:request_id>/export-expense-report')
@login_required
def api_export_expense_report(request_id):
    """Export cash expense report in Windows of Jordan Excel format"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    import os
    import tempfile
    
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        
        # Header
        ws['B2'] = 'Windows of Jordan'
        ws['B2'].font = Font(size=16, bold=True)
        ws['B3'] = ' Actual Expense Sheet'
        ws['B3'].font = Font(size=22)
        
        # File info
        ws['B5'] = request_obj.request_number
        ws['E5'] = 'Date'
        ws['F5'] = request_obj.from_date if request_obj.from_date else datetime.now()
        ws['F5'].number_format = 'DD-MMM-YY'
        
        ws['B8'] = f'File Expense {request_obj.agent or "N/A"}'
        ws['E8'] = 'Ref:'
        ws['F8'] = request_obj.contact_name or 'N/A'
        ws['E9'] = 'Pax:'
        ws['F9'] = str(request_obj.pax)
        
        # Table header
        header_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
        ws['B11'] = 'Item'
        ws['C11'] = 'Driver'
        ws['D11'] = 'Cost PP'
        ws['E11'] = 'Pax'
        ws['F11'] = 'Total'
        
        for cell in ['B11', 'C11', 'D11', 'E11', 'F11']:
            ws[cell].font = Font(bold=True)
            ws[cell].fill = header_fill
            ws[cell].alignment = Alignment(horizontal='center')
        
        # Add expense items
        row = 12
        for expense in sorted(request_obj.inbound_cash_expenses, key=lambda x: x.date):
            ws[f'B{row}'] = expense.description
            ws[f'C{row}'] = expense.driver_name or '-'
            ws[f'D{row}'] = expense.amount
            ws[f'E{row}'] = request_obj.pax if expense.is_per_person else 1
            ws[f'F{row}'] = f'=SUM(D{row}*E{row})'
            row += 1
        
        # Totals
        if row > 12:
            ws[f'F{row+1}'] = f'=SUM(F12:F{row-1})'
            ws[f'F{row+1}'].font = Font(bold=True)
            
            ws[f'D{row+2}'] = 'Advance Payment'
            ws[f'D{row+2}'].font = Font(bold=True)
            ws[f'F{row+2}'] = 0
            
            ws[f'D{row+3}'] = 'Total'
            ws[f'D{row+3}'].font = Font(bold=True, size=12)
            ws[f'F{row+3}'] = f'=F{row+1}-F{row+2}'
            ws[f'F{row+3}'].font = Font(bold=True, size=12)
            
            # Signature lines
            ws[f'B{row+7}'] = 'Authorization:…................................................'
            ws[f'D{row+7}'] = 'Guide\\Driver:…............................'
        
        # Save to temp file
        output_dir = tempfile.gettempdir()
        output_path = os.path.join(output_dir, f'Expense_Report_{request_obj.request_number}.xlsx')
        wb.save(output_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'Expense_Report_{request_obj.request_number}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error generating expense report: {str(e)}', 'error')
        return redirect(url_for('inbound.view_request', id=request_id))

@inbound_bp.route('/<int:request_id>/add-cash-expense', methods=['POST'])
@login_required
def add_cash_expense(request_id):
    """Add a cash expense item and create itinerary row"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    try:
        from app.models.inbound import ItineraryRow
        
        expense_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        description = request.form['description']
        driver_name = request.form.get('driver_name', '')
        amount = float(request.form['amount'])
        
        # Create the cash expense record
        expense = InboundCashExpense(
            request_id=request_obj.id,
            date=expense_date,
            description=description,
            driver_name=driver_name,
            amount=amount,
            currency='USD',
            is_per_person=False
        )
        db.session.add(expense)
        db.session.flush()
        
        # Create or update itinerary row for this date
        existing_row = ItineraryRow.query.filter_by(
            request_id=request_obj.id,
            date=expense_date
        ).first()
        
        if existing_row:
            # Add expense to existing row description
            expense_text = f"Cash: {description} (${amount:.2f})"
            if existing_row.description:
                existing_row.description += f" | {expense_text}"
            else:
                existing_row.description = expense_text
            # Add to base cost
            existing_row.base_cost += amount
        else:
            # Create new itinerary row
            expense_text = f"Cash: {description} (${amount:.2f})"
            
            itinerary_row = ItineraryRow(
                request_id=request_obj.id,
                date=expense_date,
                description=expense_text,
                base_cost=amount,
                currency='USD'
            )
            db.session.add(itinerary_row)
        
        db.session.commit()
        flash('Cash expense added to itinerary successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding cash expense: {str(e)}', 'error')
    
    return redirect(url_for('inbound.view_request', id=request_id))

@inbound_bp.route('/<int:request_id>/update-cash-expense/<int:expense_id>', methods=['POST'])
@login_required
def update_cash_expense(request_id, expense_id):
    """Update a cash expense item"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    expense = InboundCashExpense.query.get_or_404(expense_id)
    
    if expense.request_id != request_id:
        abort(403)
    
    try:
        if 'date' in request.form:
            expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        if 'description' in request.form:
            expense.description = request.form['description']
        if 'driver_name' in request.form:
            expense.driver_name = request.form['driver_name']
        if 'amount' in request.form:
            expense.amount = float(request.form['amount'])
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating cash expense: {str(e)}', 'error')
    
    return redirect(url_for('inbound.view_request', id=request_id))

@inbound_bp.route('/<int:request_id>/delete-cash-expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_cash_expense(request_id, expense_id):
    """Delete a cash expense item"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    expense = InboundCashExpense.query.get_or_404(expense_id)
    
    if expense.request_id != request_id:
        abort(403)
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Cash expense deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting cash expense: {str(e)}', 'error')
    
    return redirect(url_for('inbound.view_request', id=request_id))

@inbound_bp.route('/<int:request_id>/add-meal', methods=['POST'])
@login_required
def add_meal(request_id):
    """Add a meal item and create itinerary row"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    try:
        from app.models.inbound import ItineraryRow, SERVICE_FLAG_MEAL
        
        meal_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        meal_type = request.form['meal_type']
        restaurant = request.form.get('restaurant', '')
        location = request.form.get('location', '')
        
        # Create the meal record
        meal = InboundMeal(
            request_id=request_obj.id,
            date=meal_date,
            meal_type=meal_type,
            restaurant=restaurant,
            location=location,
            cost_per_person=0.0,
            currency='USD',
            status='CONFIRMED'
        )
        db.session.add(meal)
        db.session.flush()
        
        # Create or update itinerary row for this date
        existing_row = ItineraryRow.query.filter_by(
            request_id=request_obj.id,
            date=meal_date
        ).first()
        
        if existing_row:
            # Add meal flag to existing row
            existing_row.has_meal = True
            if existing_row.description:
                existing_row.description += f" | {meal_type}"
            else:
                existing_row.description = meal_type
        else:
            # Create new itinerary row
            description = f"{meal_type}"
            if restaurant:
                description += f" at {restaurant}"
            if location:
                description += f" ({location})"
            
            itinerary_row = ItineraryRow(
                request_id=request_obj.id,
                date=meal_date,
                description=description,
                has_meal=True,
                base_cost=0.0,
                currency='USD'
            )
            db.session.add(itinerary_row)
            db.session.flush()
            
            # Link meal to itinerary row
            meal.source_itinerary_id = itinerary_row.id
        
        db.session.commit()
        flash('Meal added to itinerary successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding meal: {str(e)}', 'error')
    
    return redirect(url_for('inbound.view_request', id=request_id))

@inbound_bp.route('/<int:request_id>/delete-meal/<int:meal_id>', methods=['POST'])
@login_required
def delete_meal(request_id, meal_id):
    """Delete a meal item"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    meal = InboundMeal.query.get_or_404(meal_id)
    
    if meal.request_id != request_id:
        abort(403)
    
    try:
        db.session.delete(meal)
        db.session.commit()
        flash('Meal deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting meal: {str(e)}', 'error')
    
    return redirect(url_for('inbound.view_request', id=request_id))

@inbound_bp.route('/api/hotels/search')
@login_required
def api_search_hotels():
    """API endpoint to search hotels for autocomplete"""
    query = request.args.get('query', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    # Query distinct hotel names from InboundHotel table
    hotels_query = db.session.query(InboundHotel.hotel_name, InboundHotel.location).filter(
        InboundHotel.hotel_name.isnot(None),
        InboundHotel.hotel_name != ''
    )
    
    # Apply search filter if query provided
    if query:
        hotels_query = hotels_query.filter(
            db.or_(
                InboundHotel.hotel_name.ilike(f'%{query}%'),
                InboundHotel.location.ilike(f'%{query}%')
            )
        )
    
    # Get distinct hotel names with their most recent location
    hotels_query = hotels_query.distinct(InboundHotel.hotel_name).order_by(
        InboundHotel.hotel_name
    ).limit(limit)
    
    hotels = hotels_query.all()
    
    # Format for Select2
    results = []
    for hotel_name, location in hotels:
        results.append({
            'id': hotel_name,
            'text': f"{hotel_name}" + (f" ({location})" if location else ""),
            'name': hotel_name,
            'location': location or ''
        })
    
    return jsonify({'results': results})
