from flask import render_template, request, redirect, url_for, flash, jsonify, session
import uuid
from datetime import datetime, timedelta

from app import app, db
from models import (
    User, Agent, Booking, ServiceItem, Document, Payment,
    STATUS_REQUEST, STATUS_INVOICE, STATUS_IN_PROGRESS, STATUS_COMPLETED,
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
    # Get counts for each status
    request_count = Booking.query.filter_by(status=STATUS_REQUEST).count()
    invoice_count = Booking.query.filter_by(status=STATUS_INVOICE).count()
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
            'request': request_count,
            'invoice': invoice_count,
            'in_progress': in_progress_count,
            'completed': completed_count
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
@app.route('/booking/new', methods=['GET', 'POST'])
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
            
        elif form.save_action.data and form.validate():
            # Create a unique reference number
            reference = form.request_id.data
            
            # Get the selected user
            user = User.query.get(form.customer.data)
            
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
            
            # Run invoice and payment actions if provided
            if form.invoice_notes.data:
                # Set invoice date
                booking.invoice_number = f"INV-{reference[3:]}"
                booking.invoice_date = datetime.now()
                booking.status = STATUS_INVOICE
                flash(f'Invoice {booking.invoice_number} generated for booking {reference}', 'success')
            
            if form.payment_method.data:
                # Process payment (simplified)
                amount = booking.total_amount or 0
                payment = Payment(
                    booking_id=booking.id,
                    amount=amount,
                    payment_date=datetime.now(),
                    payment_method=form.payment_method.data,
                    notes=form.payment_notes.data
                )
                booking.payment_status = 'FULL' if amount > 0 else 'NONE'
                db.session.add(payment)
                db.session.commit()
                
                flash(f'Payment of ${amount:.2f} processed for booking {reference}', 'success')
            
            flash(f'Booking request {reference} created successfully', 'success')
            # Set the booking ID in the session for later use
            session['current_booking_id'] = booking.id
            # Return to the same page instead of redirecting
            return render_template('booking/new_request.html', form=form, booking=booking)
    
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
            status=STATUS_REQUEST
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
    
    return redirect(url_for('booking_details', booking_id=booking.id))

# Update booking status
@app.route('/booking/<int:booking_id>/update_status', methods=['POST'])
def update_booking_status(booking_id):
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
    
    return redirect(url_for('booking_details', booking_id=booking.id))

# Start operations for a booking
@app.route('/booking/<int:booking_id>/start_operations', methods=['GET'])
def start_operations(booking_id):
    """Start operations for a booking after payment (partial or full)"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure booking has an invoice and at least partial payment
    if not booking.invoice_number:
        flash('Cannot start operations until an invoice is generated', 'danger')
        return redirect(url_for('booking_details', booking_id=booking.id))
    
    if booking.payment_status not in ['PARTIAL', 'FULL']:
        flash('Cannot start operations until at least a partial payment is recorded', 'danger')
        return redirect(url_for('booking_details', booking_id=booking.id))
    
    # Update booking and all service items to IN_PROGRESS status
    booking.status = STATUS_IN_PROGRESS
    for item in booking.service_items:
        item.status = STATUS_IN_PROGRESS
    
    db.session.commit()
    flash('Operations started! You can now confirm each service item.', 'success')
    
    # Get the first service item to confirm
    first_item = ServiceItem.query.filter_by(booking_id=booking.id).first()
    if first_item:
        return redirect(url_for('confirm_service', item_id=first_item.id))
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
    
    return redirect(url_for('booking_details', booking_id=service_item.booking_id))

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

# Confirm service item details
@app.route('/confirm_service/<int:item_id>', methods=['GET', 'POST'])
def confirm_service(item_id):
    """Confirm details for a specific service item with a dedicated form"""
    import sys
    print(f"Confirm service route called for item_id: {item_id}", file=sys.stderr)
    service_item = ServiceItem.query.get_or_404(item_id)
    
    # Handle form submission
    if request.method == 'POST':
        import sys
        print(f"POST request received for confirm_service. Form data:", file=sys.stderr)
        for key, value in request.form.items():
            print(f"  {key}: {value}", file=sys.stderr)

        # Get confirmation reference and supplier
        confirmation_reference = request.form.get('confirmation_reference', '')
        supplier = request.form.get('supplier', '')
        form_notes = request.form.get('notes', '')
        service_type = request.form.get('service_type', '')
        
        # Get the action type (save, next, complete)
        action = request.form.get('action', 'save')
        
        print(f"confirmation_reference: {confirmation_reference}", file=sys.stderr)
        print(f"supplier: {supplier}", file=sys.stderr)
        print(f"form_notes: {form_notes}", file=sys.stderr)
        print(f"service_type: {service_type}, actual service type: {service_item.service_type}", file=sys.stderr)
        
        # Set item status to IN_PROGRESS
        service_item.status = STATUS_IN_PROGRESS
        
        # Check if a confirmation document already exists
        document = Document.query.filter_by(
            service_item_id=service_item.id,
            document_type='CONFIRMATION'
        ).first()
        
        if document:
            # Update existing document - don't overwrite notes yet, just update the doc number
            document.document_number = confirmation_reference
            print(f"Updating existing confirmation document: {document.id}")
        else:
            # Create new document - notes will be set later with the JSON data
            document = Document(
                service_item_id=service_item.id,
                document_type='CONFIRMATION',
                document_number=confirmation_reference,
                notes=""  # Will be set below with service-specific data
            )
            print(f"Creating new confirmation document for service item: {service_item.id}")
        
        # Store the service-specific details as JSON in the notes field
        import json
        
        if service_item.service_type == 'FLIGHT':
            flight_details = {
                'airline': request.form.get('airline', ''),
                'flight_number': request.form.get('flight_number', ''),
                'departure_airport': request.form.get('departure_airport', ''),
                'arrival_airport': request.form.get('arrival_airport', ''),
                'flight_date': request.form.get('flight_date', ''),
                'flight_time': request.form.get('flight_time', ''),
                'travel_class': request.form.get('travel_class', ''),
                'terminal': request.form.get('terminal', ''),
                'ticket_number': request.form.get('ticket_number', ''),
                'supplier': supplier,
                'pnr': request.form.get('pnr', ''),
                'passenger_count': {
                    'adults': request.form.get('adults', 1),
                    'children': request.form.get('children', 0),
                    'infants': request.form.get('infants', 0)
                }
            }
            
            # Get passenger names
            passenger_names = request.form.getlist('passenger_names[]')
            if passenger_names:
                flight_details['passenger_names'] = passenger_names
            
            document.notes = json.dumps(flight_details)
        
        elif service_item.service_type == 'HOTEL':
            import sys
            print("Processing HOTEL confirmation form submission", file=sys.stderr)
            
            # Log form values for debugging
            single_rooms = request.form.get('single_rooms', '0')
            double_rooms = request.form.get('double_rooms', '0')
            twin_rooms = request.form.get('twin_rooms', '0')
            triple_rooms = request.form.get('triple_rooms', '0')
            
            print(f"Room counts from form - single: {single_rooms}, double: {double_rooms}, twin: {twin_rooms}, triple: {triple_rooms}", file=sys.stderr)
            
            hotel_details = {
                'hotel_name': request.form.get('hotel_name', ''),
                'from_date': request.form.get('from_date', ''),
                'to_date': request.form.get('to_date', ''),
                'meal_plan': request.form.get('meal_plan', ''),
                'status': request.form.get('status', ''),
                'cost': request.form.get('cost', ''),
                'currency': request.form.get('currency', 'USD'),
                'supplier': supplier,
                'special_notes': request.form.get('special_notes', ''),
                'rooms': {
                    'single': int(single_rooms) if single_rooms.isdigit() else 0,
                    'double': int(double_rooms) if double_rooms.isdigit() else 0,
                    'twin': int(twin_rooms) if twin_rooms.isdigit() else 0,
                    'triple': int(triple_rooms) if triple_rooms.isdigit() else 0,
                    'other': request.form.get('other_rooms', '')
                }
            }
            
            print(f"Hotel details to save: {hotel_details}", file=sys.stderr)
            document.notes = json.dumps(hotel_details)
            print(f"About to save document with notes: {document.notes[:100]}...", file=sys.stderr)
        
        # Add more service types as needed
        elif service_item.service_type == 'TRANSPORT':
            transport_details = {
                'confirmation_reference': confirmation_reference,
                'supplier': supplier,
                'transport_type': request.form.get('transport_type', 'Airport Transfer'),
                'pick_up': request.form.get('pick_up', ''),
                'drop_off': request.form.get('drop_off', ''),
                'date': request.form.get('date', ''),
                'time': request.form.get('time', ''),
                'vehicle_type': request.form.get('vehicle_type', ''),
                'passengers': request.form.get('passengers', '1'),
                'driver_contact': request.form.get('driver_contact', ''),
                'special_instructions': request.form.get('special_instructions', ''),
            }
            document.notes = json.dumps(transport_details)
        
        elif service_item.service_type == 'VISA':
            visa_details = {
                'confirmation_reference': confirmation_reference,
                'supplier': supplier,
                'country': request.form.get('country', ''),
                'visa_type': request.form.get('visa_type', ''),
                'application_date': request.form.get('application_date', ''),
                'processing_time': request.form.get('processing_time', ''),
                'visa_validity': request.form.get('visa_validity', ''),
                'visa_number': request.form.get('visa_number', ''),
                'applicant_name': request.form.get('applicant_name', ''),
                'passport_number': request.form.get('passport_number', ''),
                'status': request.form.get('status', ''),
                'notes': request.form.get('application_notes', ''),
            }
            document.notes = json.dumps(visa_details)
        
        elif service_item.service_type == 'INSURANCE':
            insurance_details = {
                'confirmation_reference': confirmation_reference,
                'supplier': supplier,
                'policy_number': request.form.get('policy_number', ''),
                'insurance_company': request.form.get('insurance_company', ''),
                'policy_type': request.form.get('policy_type', 'Travel'),
                'coverage_type': request.form.get('coverage_type', 'Comprehensive'),
                'insured_name': request.form.get('insured_name', ''),
                'start_date': request.form.get('start_date', ''),
                'end_date': request.form.get('end_date', ''),
                'coverage_amount': request.form.get('coverage_amount', ''),
                'currency': request.form.get('currency', 'USD'),
                'premium_amount': request.form.get('premium_amount', ''),
                'deductible': request.form.get('deductible', ''),
                'emergency_contact': request.form.get('emergency_contact', ''),
                'special_conditions': request.form.get('special_conditions', ''),
            }
            document.notes = json.dumps(insurance_details)
        
        db.session.add(document)
        db.session.commit()
        
        print(f"Document after commit - ID: {document.id}, Notes length: {len(document.notes)}", file=sys.stderr)
        
        flash(f'{service_item.service_type} service confirmed with reference: {confirmation_reference}', 'success')
        
        # Determine next action based on the form button clicked
        if action == 'next':
            # Find the next service item to confirm
            next_item = ServiceItem.query.filter(
                ServiceItem.booking_id == service_item.booking_id,
                ServiceItem.id > service_item.id
            ).order_by(ServiceItem.id).first()
            
            if next_item:
                return redirect(url_for('confirm_service', item_id=next_item.id))
        
        # Default: return to booking details
        return redirect(url_for('booking_details', booking_id=service_item.booking_id))
    
    # GET request - show the confirmation form
    import sys
    print(f"GET request for item_id: {item_id} - Loading confirmation data", file=sys.stderr)
    
    # Check if a confirmation document exists
    document = Document.query.filter_by(
        service_item_id=service_item.id,
        document_type='CONFIRMATION'
    ).first()
    
    # Initialize confirmation data with defaults
    confirmation_data = {}
    
    if document:
        import json
        print(f"Found confirmation document ID: {document.id}", file=sys.stderr)
        print(f"Document number: {document.document_number}", file=sys.stderr)
        print(f"Notes length: {len(document.notes)}", file=sys.stderr)
        
        # Set basic fields from document
        confirmation_data['confirmation_reference'] = document.document_number
        
        # Parse the JSON data from notes
        try:
            parsed_data = json.loads(document.notes)
            print(f"PARSED DATA CONTENTS: {parsed_data}", file=sys.stderr)
            print(f"Parsed confirmation data: {list(parsed_data.keys())}", file=sys.stderr)
            
            # Update confirmation data with parsed values
            confirmation_data.update(parsed_data)
            
            print(f"FINAL DATA: {confirmation_data}", file=sys.stderr)
        except json.JSONDecodeError:
            flash('Error parsing confirmation data', 'danger')
    else:
        print("No confirmation document found", file=sys.stderr)
        # Set default values based on service type
        if service_item.service_type == 'FLIGHT':
            confirmation_data = {
                'confirmation_reference': '',
                'supplier': 'Direct',
                'airline': '',
                'flight_number': '',
                'departure_airport': '',
                'arrival_airport': '',
                'flight_date': service_item.start_date.strftime('%Y-%m-%d'),
                'flight_time': '',
                'passenger_count': {
                    'adults': 1,
                    'children': 0,
                    'infants': 0
                },
                'passenger_names': ['']
            }
        elif service_item.service_type == 'HOTEL':
            confirmation_data = {
                'confirmation_reference': '',
                'supplier': 'Direct',
                'hotel_name': '',
                'from_date': service_item.start_date.strftime('%Y-%m-%d'),
                'to_date': service_item.end_date.strftime('%Y-%m-%d'),
                'meal_plan': 'Room Only',
                'status': 'confirmed',
                'cost': service_item.amount,
                'currency': 'USD',
                'special_notes': '',
                'rooms': {
                    'single': 1,
                    'double': 0,
                    'twin': 0,
                    'triple': 0,
                    'other': ''
                }
            }
        elif service_item.service_type == 'TRANSPORT':
            confirmation_data = {
                'confirmation_reference': '',
                'supplier': 'Direct',
                'transport_type': 'Airport Transfer',
                'pick_up': '',
                'drop_off': '',
                'date': service_item.start_date.strftime('%Y-%m-%d'),
                'time': '',
                'vehicle_type': 'Standard Car',
                'passengers': 1,
                'driver_contact': '',
                'special_instructions': ''
            }
        elif service_item.service_type == 'VISA':
            confirmation_data = {
                'confirmation_reference': '',
                'supplier': 'Direct',
                'country': '',
                'visa_type': 'Tourist',
                'application_date': service_item.start_date.strftime('%Y-%m-%d'),
                'processing_time': '5-7 Business Days',
                'visa_validity': '3 Months',
                'visa_number': '',
                'applicant_name': '',
                'passport_number': '',
                'status': 'Processing',
                'notes': ''
            }
        elif service_item.service_type == 'INSURANCE':
            confirmation_data = {
                'confirmation_reference': '',
                'supplier': 'Direct',
                'policy_number': '',
                'insurance_company': '',
                'policy_type': 'Travel',
                'coverage_type': 'Comprehensive',
                'insured_name': '',
                'start_date': service_item.start_date.strftime('%Y-%m-%d'),
                'end_date': service_item.end_date.strftime('%Y-%m-%d'),
                'coverage_amount': service_item.amount,
                'currency': 'USD',
                'premium_amount': '',
                'deductible': '',
                'emergency_contact': '',
                'special_conditions': ''
            }
        print(f"Default confirmation_data for {service_item.service_type}: {confirmation_data}", file=sys.stderr)
    
    # Render confirmation template based on service type
    template_name = f'booking/confirm_{service_item.service_type.lower()}.html'
    
    return render_template(
        template_name,
        service_item=service_item,
        booking=service_item.booking,
        confirmation_data=confirmation_data
    )
