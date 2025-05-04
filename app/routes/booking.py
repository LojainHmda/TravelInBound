import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models.user import User
from app.models.booking import Booking
from app.models.service import ServiceItem
from app.models import STATUS_REQUEST

from app.forms.booking import BookingRequestForm, ServiceItemForm
from app.forms.status import UpdateServiceStatusForm

# Create a blueprint for booking-related routes
booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/new', methods=['GET', 'POST'])
def new_booking():
    """Create a new booking request with itinerary items"""
    form = BookingRequestForm()
    
    # Get all users for customer selection dropdown
    users = User.query.all()
    form.customer.choices = [(str(user.id), f"{user.username} ({user.email})") for user in users]
    
    # Generate request ID if not already set
    if not form.request_id.data:
        form.request_id.data = f"IR-{str(uuid.uuid4())[:5].upper()}"
    
    # Track items added to the booking
    service_items = []
    
    if request.method == 'POST':
        if form.add_item.data and form.validate():
            # Add an item to the itinerary
            service_item = {
                'service_type': form.service_type.data,
                'from_date': form.from_date.data,
                'to_date': form.to_date.data,
                'description': form.description.data,
                'amount': form.amount.data,
                'currency': form.currency.data
            }
            service_items.append(service_item)
            
            # In a real application, store this in the session
            # For now, flash it to show functionality
            flash(f'Item added: {service_item["service_type"]} - {service_item["description"]}', 'success')
            
        elif form.submit.data and form.validate():
            # Create a unique reference number
            reference = form.request_id.data
            
            # Get the selected user
            user = User.query.get(int(form.customer.data))
            
            # Create the booking
            booking = Booking(
                reference_number=reference,
                user_id=user.id,
                status=STATUS_REQUEST
            )
            
            db.session.add(booking)
            db.session.commit()
            
            # Add service item if provided
            if form.description.data and form.amount.data:
                service_item = ServiceItem(
                    booking_id=booking.id,
                    service_type=form.service_type.data,
                    start_date=form.from_date.data,
                    end_date=form.to_date.data,
                    description=form.description.data,
                    amount=form.amount.data,
                    status=STATUS_REQUEST
                )
                
                db.session.add(service_item)
                db.session.commit()
            
            flash(f'Booking request {reference} created successfully', 'success')
            return redirect(url_for('booking.details', booking_id=booking.id))
    
    return render_template('booking/new_request.html', form=form, items=service_items)

@booking_bp.route('/<int:booking_id>', methods=['GET'])
def details(booking_id):
    """View details of a specific booking"""
    booking = Booking.query.get_or_404(booking_id)
    service_form = ServiceItemForm()
    status_form = UpdateServiceStatusForm()
    status_form.status.data = booking.status
    
    return render_template(
        'booking/booking_details.html',
        booking=booking,
        service_form=service_form,
        status_form=status_form
    )

@booking_bp.route('/<int:booking_id>/add_service', methods=['POST'])
def add_service_item(booking_id):
    """Add a service item to an existing booking"""
    booking = Booking.query.get_or_404(booking_id)
    form = ServiceItemForm()
    
    if form.validate_on_submit():
        service_item = ServiceItem(
            booking_id=booking.id,
            service_type=form.service_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            description=form.description.data,
            amount=form.amount.data,
            status=STATUS_REQUEST
        )
        
        from app.models.user import Agent
        # Assign to an agent with the matching specialty if available
        agent = Agent.query.filter_by(specialty=form.service_type.data).first()
        if agent:
            service_item.agent_id = agent.id
        
        db.session.add(service_item)
        
        # Update the booking's total amount
        booking.calculate_total()
        
        db.session.commit()
        
        flash('Service item added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
    
    return redirect(url_for('booking.details', booking_id=booking.id))

@booking_bp.route('/<int:booking_id>/update_status', methods=['POST'])
def update_booking_status(booking_id):
    """Update the status of an entire booking"""
    booking = Booking.query.get_or_404(booking_id)
    form = UpdateServiceStatusForm()
    
    if form.validate_on_submit():
        # Check if can move to COMPLETED status
        if form.status.data == STATUS_COMPLETED and not booking.can_complete():
            flash('Cannot mark as COMPLETED until all service items are fulfilled', 'danger')
        else:
            booking.status = form.status.data
            db.session.commit()
            flash(f'Booking status updated to {booking.status}', 'success')
    
    return redirect(url_for('booking.details', booking_id=booking.id))

@booking_bp.route('/service_item/<int:item_id>/update_status', methods=['POST'])
def update_service_status(item_id):
    """Update the status of a specific service item"""
    service_item = ServiceItem.query.get_or_404(item_id)
    form = UpdateServiceStatusForm()
    
    if form.validate_on_submit():
        service_item.status = form.status.data
        db.session.commit()
        flash(f'Service item status updated to {service_item.status}', 'success')
    
    return redirect(url_for('booking.details', booking_id=service_item.booking_id))

@booking_bp.route('/api/service_items/<service_type>', methods=['GET'])
def get_service_items(service_type):
    """API endpoint to get service items by type"""
    items = ServiceItem.query.filter_by(service_type=service_type).all()
    
    result = []
    for item in items:
        result.append({
            'id': item.id,
            'booking_reference': item.booking.reference_number,
            'description': item.description,
            'start_date': item.start_date.strftime('%Y-%m-%d'),
            'end_date': item.end_date.strftime('%Y-%m-%d'),
            'amount': item.amount,
            'status': item.status
        })
    
    return jsonify(result)