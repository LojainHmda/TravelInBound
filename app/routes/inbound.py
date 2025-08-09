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
from app.forms.inbound import (
    InboundRequestForm, ItineraryRowForm, InboundHotelForm, 
    InboundTransportForm, InboundMealForm, InboundGuideForm
)

# Create blueprint for inbound tour operator routes
inbound_bp = Blueprint('inbound', __name__, url_prefix='/inbound')

@inbound_bp.route('/')
@login_required
def index():
    """List all inbound requests"""
    requests = InboundRequest.query.filter_by(user_id=current_user.id).order_by(InboundRequest.created_at.desc()).all()
    return render_template('inbound/index.html', requests=requests)

@inbound_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_request():
    """Create new inbound request with itinerary"""
    form = InboundRequestForm()
    
    if form.validate_on_submit():
        # Create new request
        request_obj = InboundRequest(
            request_number=InboundRequest.generate_request_number(),
            from_date=form.from_date.data,
            to_date=form.to_date.data,
            agent=form.agent.data,
            contact_name=form.contact_name.data,
            agent_ref=form.agent_ref.data,
            nationality=form.nationality.data,
            pax=form.pax.data,
            special_note=form.special_note.data,
            user_id=current_user.id
        )
        
        # Calculate days
        request_obj.calculate_days()
        
        db.session.add(request_obj)
        db.session.commit()
        
        flash(f'Inbound request {request_obj.request_number} created successfully!', 'success')
        return redirect(url_for('inbound.edit_request', id=request_obj.id))
    
    return render_template('inbound/new_request.html', form=form)

@inbound_bp.route('/<int:id>/edit')
@login_required
def edit_request(id):
    """Edit inbound request with full itinerary interface"""
    request_obj = InboundRequest.query.get_or_404(id)
    
    # Check ownership
    if request_obj.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('inbound.index'))
    
    return render_template('inbound/edit_request.html', request=request_obj)

@inbound_bp.route('/<int:id>/view')
@login_required
def view_request(id):
    """View inbound request details"""
    request_obj = InboundRequest.query.get_or_404(id)
    
    # Check ownership
    if request_obj.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('inbound.index'))
    
    return render_template('inbound/view_request.html', request=request_obj)

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
            'row_cost': row.calculate_row_cost(request_obj.pax)
        })
    
    return jsonify({'rows': rows, 'total': request_obj.calculate_total()})

@inbound_bp.route('/api/<int:request_id>/itinerary', methods=['POST'])
@login_required
def api_save_itinerary(request_id):
    """Save itinerary rows for a request"""
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
            flag_airport=row_data.get('flag_airport', False)
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
    """Generate all service records based on itinerary flags"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Clear existing auto-generated services
    InboundHotel.query.filter_by(request_id=request_id).delete()
    InboundTransport.query.filter_by(request_id=request_id).delete()
    InboundMeal.query.filter_by(request_id=request_id).delete()
    InboundGuide.query.filter_by(request_id=request_id).delete()
    
    # Generate services for each itinerary row
    for row in request_obj.itinerary_rows:
        _auto_generate_services(request_obj, row)
    
    db.session.commit()
    
    return jsonify({'success': True})

@inbound_bp.route('/<int:request_id>/services')
@login_required
def view_services(request_id):
    """View all services for a request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    return render_template('inbound/view_services.html', request=request_obj)

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
@login_required
def generate_voucher(request_id):
    """Generate voucher for the request"""
    request_obj = InboundRequest.query.get_or_404(request_id)
    
    if request_obj.user_id != current_user.id:
        abort(403)
    
    if request_obj.status in [STATUS_REQUEST, STATUS_BOOKED]:
        abort(400, 'Cannot generate voucher until confirmed')
    
    return render_template('inbound/voucher.html', request=request_obj)