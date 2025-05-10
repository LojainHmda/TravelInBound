from flask import render_template, request, redirect, url_for, flash, jsonify
import uuid
from datetime import datetime, timedelta

from app import app, db
from models import (
    User, Agent, Booking, ServiceItem, Document, Payment,
    STATUS_PLANNED, STATUS_PREPAID, STATUS_QUEUED, STATUS_PROCESSING, STATUS_CONFIRMED, STATUS_CLOSED,
    # Legacy status constants kept for backward compatibility
    STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_COMPLETED,
    SERVICE_FLIGHT, SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_VISA, SERVICE_INSURANCE
)
from forms import NewBookingForm, ServiceItemForm, UpdateServiceStatusForm, DocumentUploadForm

# Create a test user if none exists
# Create a function to initialize test data
def create_test_data():
    if not User.query.first():
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash="test_hash"  # In production, use proper password hashing
        )
        db.session.add(test_user)
        
        test_agent_flight = Agent(
            name="Jane Doe",
            email="jane@example.com",
            specialty="FLIGHT"
        )
        
        test_agent_hotel = Agent(
            name="John Smith",
            email="john@example.com",
            specialty="HOTEL"
        )
        
        db.session.add_all([test_agent_flight, test_agent_hotel])
        db.session.commit()

# Add with_appcontext to app startup
with app.app_context():
    create_test_data()

# Home page
@app.route('/')
def index():
    # Get latest bookings for demonstration
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('index.html', bookings=recent_bookings)

# Dashboard
@app.route('/dashboard')
def dashboard():
    # Get counts for each status using new status constants
    planned_count = Booking.query.filter_by(status=STATUS_PLANNED).count()
    prepaid_count = Booking.query.filter_by(status=STATUS_PREPAID).count()
    queued_count = Booking.query.filter_by(status=STATUS_QUEUED).count()
    processing_count = Booking.query.filter_by(status=STATUS_PROCESSING).count()
    confirmed_count = Booking.query.filter_by(status=STATUS_CONFIRMED).count()
    closed_count = Booking.query.filter_by(status=STATUS_CLOSED).count()
    
    # Also count legacy statuses for backward compatibility
    request_count = Booking.query.filter_by(status=STATUS_REQUEST).count()
    booked_count = Booking.query.filter_by(status=STATUS_BOOKED).count()
    in_progress_count = Booking.query.filter_by(status=STATUS_IN_PROGRESS).count()
    completed_count = Booking.query.filter_by(status=STATUS_COMPLETED).count()
    
    # Get service items for each service type
    flight_items = ServiceItem.query.filter_by(service_type=SERVICE_FLIGHT).all()
    hotel_items = ServiceItem.query.filter_by(service_type=SERVICE_HOTEL).all()
    transport_items = ServiceItem.query.filter_by(service_type=SERVICE_TRANSPORT).all()
    visa_items = ServiceItem.query.filter_by(service_type=SERVICE_VISA).all()
    insurance_items = ServiceItem.query.filter_by(service_type=SERVICE_INSURANCE).all()
    
    return render_template(
        'booking/dashboard.html',
        status_counts={
            # New status flow (uppercase keys to match template)
            'PLANNED': planned_count,
            'PREPAID': prepaid_count,
            'QUEUED': queued_count, 
            'PROCESSING': processing_count,
            'CONFIRMED': confirmed_count,
            'CLOSED': closed_count,
            # Legacy statuses for backward compatibility
            'REQUEST': request_count,
            'BOOKED': booked_count,
            'IN-PROGRESS': in_progress_count,
            'COMPLETED': completed_count
        },
        service_items={
            'flight': flight_items,
            'hotel': hotel_items,
            'transport': transport_items,
            'visa': visa_items,
            'insurance': insurance_items
        }
    )

# New booking request
@app.route('/requests', methods=['GET', 'POST'])
def new_booking():
    form = NewBookingForm()
    
    # Get all users for customer selection dropdown
    users = User.query.all()
    form.customer.choices = [(user.id, f"{user.username} ({user.email})") for user in users]
    
    # Generate request ID if not already set
    if not form.request_id.data:
        form.request_id.data = f"IR-{str(uuid.uuid4())[:5].upper()}"
    
    # Track items added to the booking
    service_items = []
    
    if request.method == 'POST':
        if form.add_item.data:
            # Add an item to the itinerary
            service_item = {
                'service_type': form.service_type.data,
                'from_date': form.from_date.data,
                'to_date': form.to_date.data,
                'description': form.description.data,
                'amount': form.amount.data,
                'currency': form.currency.data
            }
            
            # In a real application, store this in the session
            # For now, flash it to show functionality
            flash(f'Item added: {service_item["service_type"]} - {service_item["description"]}', 'success')
            
        elif form.submit.data and form.validate():
            # Create a unique reference number
            reference = form.request_id.data
            
            # Get the selected user
            user = User.query.get(form.customer.data)
            
            # Create the booking
            booking = Booking(
                reference_number=reference,
                user_id=user.id,
                status=STATUS_PLANNED
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
                    status=STATUS_PLANNED
                )
                
                db.session.add(service_item)
                db.session.commit()
            
            flash(f'Booking request {reference} created successfully', 'success')
            return redirect(url_for('booking_details', booking_id=booking.id))
    
    return render_template('booking/new_request.html', form=form)

# Booking details
@app.route('/booking/<int:booking_id>', methods=['GET'])
def booking_details(booking_id):
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

# Add service item to booking
@app.route('/booking/<int:booking_id>/add_service', methods=['POST'])
def add_service_item(booking_id):
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
            status=STATUS_PLANNED
        )
        
        # Assign to an agent with the matching specialty if available
        agent = Agent.query.filter_by(specialty=form.service_type.data).first()
        if agent:
            service_item.agent_id = agent.id
        
        db.session.add(service_item)
        
        # Update the booking's total amount
        booking.calculate_total()
        
        db.session.commit()
        
        flash(f'Service item added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
    
    # Get the referrer URL if available, otherwise default to booking details
    referrer = request.referrer
    if referrer and '/booking/' in referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('booking_details', booking_id=booking.id))

# Update booking status
@app.route('/booking/<int:booking_id>/update_status', methods=['POST'])
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    form = UpdateServiceStatusForm()
    
    if form.validate_on_submit():
        # Check if can move to CLOSED status
        if form.status.data == STATUS_CLOSED and not booking.can_complete():
            flash('Cannot mark as CLOSED until all service items are confirmed', 'danger')
        else:
            booking.status = form.status.data
            db.session.commit()
            flash(f'Booking status updated to {booking.status}', 'success')
    
    # Get the referrer URL if available, otherwise default to booking details
    referrer = request.referrer
    if referrer and '/booking/' in referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('booking_details', booking_id=booking.id))

# Update service item status
@app.route('/service_item/<int:item_id>/update_status', methods=['POST'])
def update_service_status(item_id):
    service_item = ServiceItem.query.get_or_404(item_id)
    form = UpdateServiceStatusForm()
    
    if form.validate_on_submit():
        service_item.status = form.status.data
        db.session.commit()
        flash(f'Service item status updated to {service_item.status}', 'success')
    
    # Get the referrer URL if available, otherwise default to booking details
    referrer = request.referrer
    if referrer and '/booking/' in referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('booking_details', booking_id=service_item.booking_id))

# Generate Prepayment
@app.route('/booking/<int:booking_id>/generate_invoice', methods=['GET', 'POST'])
def generate_invoice(booking_id):
    """Generate a prepayment for a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        total_amount = request.form.get('total_amount', type=float)
        notes = request.form.get('notes', '')
        
        if not total_amount:
            # If no total amount provided, calculate from service items
            total_amount = booking.calculate_total()
        
        # Generate a prepayment number
        invoice_number = booking.generate_invoice_number()
        
        # Update booking status to PREPAID
        booking.status = STATUS_PREPAID
        
        # Set prepayment information
        booking.invoice_date = datetime.utcnow()
        db.session.commit()
        
        flash(f'Prepayment #{invoice_number} generated successfully', 'success')
        
        # Get the referrer URL if available, otherwise default to booking details
        referrer = request.referrer
        if referrer and '/booking/' in referrer:
            return redirect(referrer)
        else:
            return redirect(url_for('booking_details', booking_id=booking.id))
    
    # Calculate total from service items
    total_amount = booking.calculate_total()
    
    return render_template(
        'booking/generate_invoice.html',
        booking=booking,
        total_amount=total_amount
    )

# Add Payment
@app.route('/booking/<int:booking_id>/add_payment', methods=['GET', 'POST'])
def add_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        payment_method = request.form.get('payment_method')
        transaction_id = request.form.get('transaction_id', '')
        payment_date_str = request.form.get('payment_date')
        notes = request.form.get('notes', '')
        
        if amount and payment_method:
            try:
                payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d')
            except:
                payment_date = datetime.utcnow()
                
            # Create new payment
            payment = Payment(
                booking_id=booking.id,
                amount=amount,
                payment_method=payment_method,
                transaction_id=transaction_id,
                payment_date=payment_date,
                notes=notes
            )
            
            db.session.add(payment)
            
            # Update booking payment status
            booking.payment_date = datetime.utcnow()
            booking.update_payment_status()
            
            db.session.commit()
            
            flash(f'Payment of ${amount} recorded successfully', 'success')
            
            # Get the referrer URL if available, otherwise default to booking details
            referrer = request.referrer
            if referrer and '/booking/' in referrer:
                return redirect(referrer)
            else:
                return redirect(url_for('booking_details', booking_id=booking.id))
    
    return render_template(
        'booking/add_payment.html',
        booking=booking,
        remaining_amount=(booking.total_amount - sum(payment.amount for payment in booking.payments))
    )

# API to get service items for a specific service type
@app.route('/api/service_items/<service_type>', methods=['GET'])
def get_service_items(service_type):
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
