import uuid
import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from app import db
from app.models.user import User
from app.models.booking import Booking, Payment
from app.models.service import ServiceItem, Document
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_COMPLETED

from app.forms.booking import BookingRequestForm, ServiceItemForm
from app.forms.status import UpdateServiceStatusForm
from app.forms.invoice import GenerateInvoiceForm, PaymentForm

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
        # Start a new session for this booking
        session['service_items'] = []
    
    # Initialize service items from session
    if 'service_items' not in session:
        session['service_items'] = []
    
    service_items = session['service_items']
    
    # Handle item removal if requested
    item_id_to_remove = request.args.get('remove_item')
    if item_id_to_remove:
        service_items = [item for item in service_items if item.get('item_id') != item_id_to_remove]
        session['service_items'] = service_items
        flash('Service item removed successfully', 'success')
        return redirect(url_for('booking.new_booking'))
    
    if request.method == 'POST':
        print("POST received. Form data:", request.form)
        print("Form is valid?", form.validate())
        if form.errors:
            print("Form errors:", form.errors)
            
        # Reload service items from session to ensure we don't lose anything
        service_items = session.get('service_items', [])

        # Check which button was clicked
        if 'add_item' in request.form or 'quick_add_service_type' in request.form:
            print("Add item button clicked")
            if form.validate():
                # Create a new service item to add to the itinerary
                service_item = {
                    'service_type': form.service_type.data,
                    'from_date': str(form.from_date.data) if form.from_date.data else '',
                    'to_date': str(form.to_date.data) if form.to_date.data else '',
                    'start_date': str(form.from_date.data) if form.from_date.data else '',  # For compatibility
                    'end_date': str(form.to_date.data) if form.to_date.data else '',        # For compatibility
                    'description': form.description.data,
                    'amount': float(form.amount.data) if form.amount.data else 0.0,
                    'currency': form.currency.data,
                    'item_id': str(uuid.uuid4())  # Add a unique ID for each item
                }
                
                # Debug output for the added item
                import sys
                print(f"Adding item to session: {service_item}", file=sys.stderr)
                
                # Add to list and update session
                service_items.append(service_item)
                session['service_items'] = service_items
                
                # Display a specialized message for quick-added items
                if 'quick_add_service_type' in request.form:
                    quick_service_type = request.form.get('quick_add_service_type')
                    service_name = dict(form.service_type.choices).get(quick_service_type, quick_service_type)
                    flash(f'Quick added {service_name} service', 'success')
                else:
                    # Regular add item message
                    flash(f'Item added: {service_item["service_type"]} - {service_item["description"]}', 'success')
                
                # Clear the form fields for next item
                form.description.data = ''
                form.amount.data = None
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'Error in {field}: {error}', 'danger')
            
        elif 'save_action' in request.form:
            print("Save button clicked")
            if form.validate():
                # Get the action type (save or generate_invoice)
                action = request.form.get('save_action', 'save')
                
                # Create a unique reference number
                reference = form.request_id.data
                
                # Check if a booking with this reference already exists
                booking = Booking.query.filter_by(reference_number=reference).first()
                
                # Only create a new booking if one doesn't already exist with this reference
                if not booking:
                    # Get the selected user
                    user = User.query.get(int(form.customer.data))
                    
                    # Create the booking without deposit amount
                    booking = Booking(
                        reference_number=reference,
                        user_id=user.id,
                        status=STATUS_REQUEST
                    )
                    
                    db.session.add(booking)
                    db.session.commit()
                else:
                    print(f"Found existing booking with reference {reference}, using it instead of creating a new one.")
                
                # Get service items from session
                session_items = session.get('service_items', [])
                
                # Debug information about session items
                import sys
                print(f"Session items: {session_items}", file=sys.stderr)
                
                # Only add service items if we just created a new booking
                # or if there are no existing service items for this booking
                if not booking.service_items or len(booking.service_items) == 0:
                    # Add all service items from the session
                    if session_items:
                        for item_data in session_items:
                            # Convert string dates back to Python date objects
                            from datetime import datetime
                            
                            # Debug output for the item data
                            print(f"Processing item: {item_data}", file=sys.stderr)
                            
                            # Parse the date strings with proper error handling
                            try:
                                # Check if we're using from_date/to_date or start_date/end_date
                                if 'from_date' in item_data and 'to_date' in item_data:
                                    if item_data['from_date'] and item_data['to_date']:
                                        start_date = datetime.strptime(item_data['from_date'], '%Y-%m-%d').date()
                                        end_date = datetime.strptime(item_data['to_date'], '%Y-%m-%d').date()
                                    else:
                                        # Use today's date and a week later as defaults
                                        start_date = datetime.now().date()
                                        end_date = datetime.now().date()
                                elif 'start_date' in item_data and 'end_date' in item_data:
                                    if item_data['start_date'] and item_data['end_date']:
                                        start_date = datetime.strptime(item_data['start_date'], '%Y-%m-%d').date()
                                        end_date = datetime.strptime(item_data['end_date'], '%Y-%m-%d').date()
                                    else:
                                        # Use today's date and a week later as defaults
                                        start_date = datetime.now().date()
                                        end_date = datetime.now().date()
                                else:
                                    # Use today's date and a week later as defaults
                                    start_date = datetime.now().date()
                                    end_date = datetime.now().date()
                                
                                print(f"Parsed dates: start_date={start_date}, end_date={end_date}", file=sys.stderr)
                            except (ValueError, TypeError) as e:
                                # Use today's date as a fallback if parsing fails
                                print(f"Error parsing dates: {e}", file=sys.stderr)
                                start_date = datetime.now().date()
                                end_date = datetime.now().date()
                            
                            service_item = ServiceItem(
                                booking_id=booking.id,
                                service_type=item_data['service_type'],
                                start_date=start_date,
                                end_date=end_date,
                                description=item_data['description'],
                                amount=float(item_data['amount']),
                                status=STATUS_REQUEST
                            )
                            
                            db.session.add(service_item)
                        
                        db.session.commit()
                        booking.calculate_total()
                        db.session.commit()
                
                # Also add the current item if it has data
                elif form.description.data and form.amount.data:
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
                    booking.calculate_total()
                    db.session.commit()
                
                # DON'T clear the session for save
                if action != 'save':
                    session.pop('service_items', None)
                
                # For save action, refresh service_items from the database so they don't disappear
                if action == 'save':
                    # Clear service_items and reload from DB
                    service_items = []
                    db_items = ServiceItem.query.filter_by(booking_id=booking.id).all()
                    for item in db_items:
                        service_items.append({
                            'id': item.id,
                            'service_type': item.service_type,
                            'start_date': item.start_date.strftime('%Y-%m-%d'),
                            'end_date': item.end_date.strftime('%Y-%m-%d'),
                            'description': item.description,
                            'amount': item.amount,
                            'status': item.status
                        })
                    session['service_items'] = service_items
                    # Update for our current scope
                    service_items = session.get('service_items', [])
                
                # Handle invoice generation if requested (but do not try to create a new booking)
                # Check for invoice generation request - prioritize this over checking invoice_notes
                if (action == 'generate_invoice' or action == 'invoice') and booking:
                    import sys
                    print(f"Generate invoice action detected, form data: {request.form}", file=sys.stderr)
                    
                    # Update the total amount if provided in the modal form
                    invoice_total = request.form.get('invoice_total')
                    if invoice_total:
                        try:
                            invoice_total = float(invoice_total)
                            if invoice_total > 0:
                                print(f"Setting booking total to {invoice_total}", file=sys.stderr)
                                booking.total_amount = invoice_total
                        except (ValueError, TypeError):
                            print(f"Invalid invoice_total: {invoice_total}", file=sys.stderr)
                    
                    # If no invoice_total was provided, calculate from service items
                    if not invoice_total and booking.service_items:
                        booking.calculate_total()
                        print(f"Calculated total from service items: {booking.total_amount}", file=sys.stderr)
                    
                    # Generate invoice number if one doesn't exist
                    if not booking.invoice_number:
                        booking.generate_invoice_number()
                        print(f"Generated invoice number: {booking.invoice_number}", file=sys.stderr)
                    
                    # Update the booking status to INVOICE
                    booking.status = STATUS_BOOKED
                    
                    # Save invoice notes
                    invoice_notes = request.form.get('invoice_notes', '')
                    print(f"Invoice notes: {invoice_notes}", file=sys.stderr)
                    # You could add the notes to the booking or create a separate model for invoice notes
                    
                    db.session.commit()
                    
                    flash(f'Invoice {booking.invoice_number} generated for booking {reference}', 'success')
                    
                    # Redirect to the invoice details page
                    return redirect(url_for('booking.invoice_details', booking_id=booking.id))
                
                # Check if payment information was provided - allow various action names
                payment_method = request.form.get('payment_method')
                payment_notes = request.form.get('payment_notes')
                if payment_method and booking and (action == 'process_payment' or action == 'payment'):
                    # Make sure we have a valid booking and the action is explicitly for payment
                    from datetime import datetime  # Import datetime here to fix the undefined issue
                    
                    # Create a payment record
                    payment = Payment(
                        booking_id=booking.id,
                        amount=booking.total_amount,  # Use the calculated total amount
                        payment_date=datetime.utcnow(),
                        payment_method=payment_method,
                        transaction_id='MANUAL-' + datetime.utcnow().strftime('%Y%m%d%H%M%S'),
                        notes=payment_notes or ''
                    )
                    
                    db.session.add(payment)
                    
                    # Update booking payment status
                    booking.update_payment_status()
                    
                    # Set payment date on booking if not already set
                    if not booking.payment_date:
                        booking.payment_date = datetime.utcnow()
                    
                    db.session.commit()
                    
                    flash(f'Payment of ${booking.total_amount:.2f} processed for booking {reference}', 'success')
                
                # Handle Start Operations action
                if action == 'start_operations' and booking:
                    # Update booking status to IN_PROGRESS
                    booking.status = STATUS_IN_PROGRESS
                    
                    # Update all service items to IN_PROGRESS too
                    for item in booking.service_items:
                        if item.status == STATUS_REQUEST:
                            item.status = STATUS_IN_PROGRESS
                    
                    db.session.commit()
                    flash(f'Operations started: Booking status updated to {booking.status}', 'success')
                    
                    # Get the first service item to confirm if any exists
                    if booking.service_items and len(booking.service_items) > 0:
                        first_item = booking.service_items[0]
                        return redirect(url_for('booking.confirm_service', item_id=first_item.id))
                
                # Only flash the success message if we're not redirecting elsewhere
                if action == 'save':
                    flash(f'Booking request {reference} created successfully with {len(session_items) or 0} service items', 'success')
                    # Instead of redirecting, we'll continue with the same request
                    # which will render the template with the current service items
                    # return redirect(url_for('booking.new_booking'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'Error in {field}: {error}', 'danger')
    
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
    
    # Check if this is a direct status transition to IN_PROGRESS (Start Operations)
    if 'new_status' in request.form and request.form['new_status'] == STATUS_IN_PROGRESS:
        old_status = booking.status
        new_status = STATUS_IN_PROGRESS
        
        # Check payment status when moving to IN_PROGRESS
        if booking.payment_status != 'FULL':
            flash('Warning: This booking has not been fully paid', 'warning')
        
        booking.status = new_status
        
        # Update all service items to IN_PROGRESS too
        for item in booking.service_items:
            if item.status == STATUS_REQUEST:
                item.status = STATUS_IN_PROGRESS
        
        db.session.commit()
        flash(f'Operations started: Booking status updated to {booking.status}', 'success')
        
        # Get the first service item to confirm
        if booking.service_items and len(booking.service_items) > 0:
            first_item = booking.service_items[0]
            return redirect(url_for('booking.confirm_service', item_id=first_item.id))
        else:
            return redirect(url_for('booking.details', booking_id=booking.id))
    
    # Regular form submission
    form = UpdateServiceStatusForm()
    if form.validate_on_submit():
        old_status = booking.status
        new_status = form.status.data
        
        # Handle special status transitions
        if new_status == STATUS_COMPLETED and not booking.can_complete():
            flash('Cannot mark as COMPLETED until all service items are fulfilled', 'danger')
            return redirect(url_for('booking.details', booking_id=booking.id))
        
        # If moving to BOOKED status, generate invoice number
        if new_status == STATUS_BOOKED and old_status != STATUS_BOOKED:
            booking.generate_invoice_number()
            flash(f'Invoice {booking.invoice_number} generated', 'success')
        
        # Check payment status when moving to IN_PROGRESS
        if new_status == STATUS_IN_PROGRESS and booking.payment_status != 'FULL':
            flash('Warning: This booking has not been fully paid', 'warning')
        
        booking.status = new_status
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

@booking_bp.route('/confirm_service/<int:item_id>', methods=['GET', 'POST'])
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
            
        elif service_item.service_type == 'TRANSPORT':
            transport_details = {
                'vehicle_type': request.form.get('vehicle_type', ''),
                'pickup_location': request.form.get('pickup_location', ''),
                'dropoff_location': request.form.get('dropoff_location', ''),
                'pickup_date': request.form.get('pickup_date', ''),
                'pickup_time': request.form.get('pickup_time', ''),
                'driver_name': request.form.get('driver_name', ''),
                'driver_contact': request.form.get('driver_contact', ''),
                'supplier': supplier,
                'special_requests': request.form.get('special_requests', '')
            }
            
            document.notes = json.dumps(transport_details)
            
        elif service_item.service_type == 'VISA':
            import sys
            print("Processing VISA confirmation form submission", file=sys.stderr)
            print(f"Supplier from form: '{supplier}'", file=sys.stderr)
            
            visa_details = {
                'applicant_name': request.form.get('applicant_name', ''),
                'passport_number': request.form.get('passport_number', ''),
                'nationality': request.form.get('nationality', ''),
                'date_of_birth': request.form.get('date_of_birth', ''),
                'gender': request.form.get('gender', ''),
                'destination_country': request.form.get('destination_country', ''),
                'visa_type': request.form.get('visa_type', ''),
                'application_date': request.form.get('application_date', ''),
                'application_status': request.form.get('application_status', ''),
                'valid_from': request.form.get('valid_from', ''),
                'valid_until': request.form.get('valid_until', ''),
                'number_of_entries': request.form.get('number_of_entries', ''),
                'processing_type': request.form.get('processing_type', ''),
                'expected_completion': request.form.get('expected_completion', ''),
                'special_notes': request.form.get('special_notes', ''),
                'supplier': supplier
            }
            
            print(f"VISA details to save: {visa_details}", file=sys.stderr)
            document.notes = json.dumps(visa_details)
            print(f"Document notes after setting: {document.notes[:100]}...", file=sys.stderr)
            
        elif service_item.service_type == 'INSURANCE':
            insurance_details = {
                'policy_number': request.form.get('policy_number', ''),
                'insurance_company': request.form.get('insurance_company', ''),
                'policy_type': request.form.get('policy_type', ''),
                'coverage_type': request.form.get('coverage_type', ''),
                'insured_name': request.form.get('insured_name', ''),
                'start_date': request.form.get('start_date', ''),
                'end_date': request.form.get('end_date', ''),
                'coverage_amount': request.form.get('coverage_amount', ''),
                'currency': request.form.get('currency', ''),
                'premium_amount': request.form.get('premium_amount', ''),
                'deductible': request.form.get('deductible', ''),
                'emergency_contact': request.form.get('emergency_contact', ''),
                'special_conditions': request.form.get('special_conditions', ''),
                'supplier': supplier
            }
            
            document.notes = json.dumps(insurance_details)
        
        # Save changes
        import sys
        print(f"About to save document with notes: {document.notes[:100]}...", file=sys.stderr)
        db.session.add(document)
        db.session.commit()
        
        # Verify the document was saved by retrieving it again
        saved_doc = Document.query.get(document.id)
        print(f"Document after commit - ID: {saved_doc.id}, Notes length: {len(saved_doc.notes) if saved_doc.notes else 0}", file=sys.stderr)
        
        # Mark this service item as COMPLETED
        service_item.status = STATUS_COMPLETED
        db.session.commit()
        
        flash(f'{service_item.service_type} confirmation details saved', 'success')
        
        # Get the booking ID for subsequent operations
        booking_id = service_item.booking_id
        
        # Handle the form action
        if action == 'next':
            # Find the next service item that needs confirmation
            next_item = ServiceItem.query.filter_by(
                booking_id=booking_id,
                status=STATUS_IN_PROGRESS
            ).filter(ServiceItem.id != service_item.id).first()
            
            if next_item:
                # Redirect to the next service item confirmation
                flash('Moving to next service item for confirmation', 'info')
                return redirect(url_for('booking.confirm_service', item_id=next_item.id))
        
        # Check if all items are now completed regardless of the action
        pending_items = ServiceItem.query.filter(
            ServiceItem.booking_id == booking_id,
            ServiceItem.status != STATUS_COMPLETED
        ).count()
        
        if pending_items == 0:
            # All service items are completed, update booking status
            booking = Booking.query.get(booking_id)
            booking.status = STATUS_COMPLETED
            db.session.commit()
            flash('All services confirmed! Booking is now complete.', 'success')
        
        # Default behavior: redirect to the booking details page
        return redirect(url_for('booking.details', booking_id=booking_id))
    
    # Get existing confirmation document if available
    import sys
    print(f"GET request for item_id: {item_id} - Loading confirmation data", file=sys.stderr)
    
    confirmation_doc = Document.query.filter_by(
        service_item_id=service_item.id, 
        document_type='CONFIRMATION'
    ).first()
    
    if confirmation_doc:
        print(f"Found confirmation document ID: {confirmation_doc.id}", file=sys.stderr)
        print(f"Document number: {confirmation_doc.document_number}", file=sys.stderr)
        print(f"Notes length: {len(confirmation_doc.notes) if confirmation_doc.notes else 0}", file=sys.stderr)
    else:
        print("No confirmation document found", file=sys.stderr)
    
    # Prepare data for template with default values
    import json
    
    # Set up base confirmation data
    confirmation_data = {
        'confirmation_reference': '',
        'supplier': 'Direct'
    }
    
    # Add service-specific default fields
    if service_item.service_type == 'FLIGHT':
        confirmation_data.update({
            'passenger_count': {
                'adults': 1,
                'children': 0,
                'infants': 0
            },
            'passenger_names': [],
            'airline': '',
            'flight_number': '',
            'departure_airport': '',
            'arrival_airport': '',
            'flight_date': service_item.start_date.strftime('%Y-%m-%d'),
            'flight_time': '',
            'travel_class': 'Economy',
            'terminal': '',
            'ticket_number': '',
            'pnr': ''
        })
    elif service_item.service_type == 'HOTEL':
        confirmation_data.update({
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
        })
    elif service_item.service_type == 'VISA':
        confirmation_data.update({
            'applicant_name': '',
            'passport_number': '',
            'nationality': '',
            'date_of_birth': '',
            'gender': '',
            'destination_country': '',
            'visa_type': 'Tourist',
            'application_date': service_item.start_date.strftime('%Y-%m-%d'),
            'application_status': 'Applied',
            'valid_from': '',
            'valid_until': service_item.end_date.strftime('%Y-%m-%d'),
            'number_of_entries': 'Single',
            'processing_type': 'Standard',
            'expected_completion': '',
            'special_notes': ''
        })
    elif service_item.service_type == 'INSURANCE':
        confirmation_data.update({
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
        })
    
    import sys
    print(f"Default confirmation_data for {service_item.service_type}: {confirmation_data}", file=sys.stderr)
    
    if confirmation_doc:
        # If there's existing confirmation data, parse it
        try:
            if confirmation_doc.notes:
                parsed_data = json.loads(confirmation_doc.notes)
                # Debug output to see what's in the parsed data
                print(f"PARSED DATA CONTENTS: {parsed_data}", file=sys.stderr)
                # Update our defaults with the parsed data
                confirmation_data.update(parsed_data)
                # Add confirmation reference number
                confirmation_data['confirmation_reference'] = confirmation_doc.document_number
                print(f"Parsed confirmation data: {list(confirmation_data.keys())}", file=sys.stderr)
                print(f"FINAL DATA: {confirmation_data}", file=sys.stderr)
            else:
                print("Document notes field is empty", file=sys.stderr)
        except (json.JSONDecodeError, TypeError) as e:
            # If parsing fails, we keep our defaults
            print(f"Error parsing JSON: {str(e)}", file=sys.stderr)
    
    # Show the appropriate confirmation form based on service type
    if service_item.service_type == 'FLIGHT':
        template = 'booking/confirm_flight.html'
    elif service_item.service_type == 'HOTEL':
        template = 'booking/confirm_hotel.html'
    elif service_item.service_type == 'TRANSPORT':
        template = 'booking/confirm_transport.html'
    elif service_item.service_type == 'VISA':
        template = 'booking/confirm_visa.html'
    elif service_item.service_type == 'INSURANCE':
        template = 'booking/confirm_insurance.html'
    else:
        # Generic confirmation form
        template = 'booking/confirm_generic.html'
    
    return render_template(template, 
                          service_item=service_item, 
                          confirmation_data=confirmation_data, 
                          confirmation_doc=confirmation_doc)

@booking_bp.route('/<int:booking_id>/generate_invoice', methods=['GET', 'POST'])
def generate_invoice(booking_id):
    """Generate an invoice for a booking"""
    booking = Booking.query.get_or_404(booking_id)
    form = GenerateInvoiceForm()
    
    # Pre-fill the form with the current total
    if request.method == 'GET':
        form.total_amount.data = booking.total_amount
    
    if request.method == 'POST':
        import sys
        print(f"POST data received in generate_invoice: {request.form}", file=sys.stderr)
        
        # Handle both direct form submission and AJAX/form submissions with different parameters
        new_total = None
        
        # Check for invoice_total in form data first (this comes from the modal in new_request.html)
        invoice_total = request.form.get('invoice_total')
        if invoice_total:
            try:
                new_total = float(invoice_total)
                print(f"Using invoice_total from form: {new_total}", file=sys.stderr)
            except (ValueError, TypeError):
                print(f"Invalid invoice_total: {invoice_total}", file=sys.stderr)
        
        # Then check for regular form validation
        if new_total is None and form.validate_on_submit():
            new_total = form.total_amount.data
            print(f"Using total_amount from validated form: {new_total}", file=sys.stderr)
        
        # Finally, look for other form fields
        if new_total is None:
            total_amount = request.form.get('total_amount')
            if total_amount:
                try:
                    new_total = float(total_amount)
                    print(f"Using total_amount from form: {new_total}", file=sys.stderr)
                except (ValueError, TypeError):
                    print(f"Invalid total_amount: {total_amount}", file=sys.stderr)
        
        # If still no valid total, use the current booking total
        if new_total is None:
            new_total = booking.total_amount
            print(f"Using existing booking total: {new_total}", file=sys.stderr)
        
        # If we have a valid total, update and generate invoice
        if new_total is not None:
            # Update the booking total
            booking.total_amount = new_total
            
            # Generate invoice number if not already set
            if not booking.invoice_number:
                booking.generate_invoice_number()
            
            # Update status to INVOICE
            booking.status = STATUS_BOOKED
            
            # Add invoice notes if provided
            notes = form.notes.data or request.form.get('invoice_notes', '')
            # You could save notes to the booking or create a separate model for invoice notes
            
            db.session.commit()
            flash(f'Invoice {booking.invoice_number} generated successfully', 'success')
            
            # Check if this is from the new booking form by looking at the referrer or a flag
            if 'save_action' in request.form:
                # Return to the new booking form (or stay on current page)
                return redirect(url_for('booking.new_booking'))
            else:
                # Otherwise go to invoice details page
                return redirect(url_for('booking.invoice_details', booking_id=booking.id))
    
    return render_template('booking/generate_invoice.html', form=form, booking=booking)

@booking_bp.route('/<int:booking_id>/invoice', methods=['GET'])
def invoice_details(booking_id):
    """View invoice details"""
    import sys
    print(f"Invoice details route called for booking_id: {booking_id}", file=sys.stderr)
    
    booking = Booking.query.get_or_404(booking_id)
    
    # If no invoice yet, redirect to generate page
    if not booking.invoice_number:
        flash('No invoice generated yet. Please generate an invoice first.', 'warning')
        return redirect(url_for('booking.generate_invoice', booking_id=booking.id))
    
    # Ensure we have an invoice date
    if not booking.invoice_date:
        from datetime import datetime
        booking.invoice_date = datetime.utcnow()
        db.session.commit()
        print(f"Added missing invoice date for booking {booking.id}", file=sys.stderr)
    
    print(f"Rendering invoice template with invoice #{booking.invoice_number}", file=sys.stderr)
    return render_template('booking/invoice_details.html', booking=booking)

@booking_bp.route('/<int:booking_id>/add_payment', methods=['GET', 'POST'])
def add_payment(booking_id):
    """Process a payment for a booking"""
    booking = Booking.query.get_or_404(booking_id)
    form = PaymentForm()
    
    # Set defaults on GET request
    if request.method == 'GET':
        # Default payment date to today
        form.payment_date.data = datetime.utcnow().date()
        
        # Default amount to remaining balance
        total_paid = sum(payment.amount for payment in booking.payments)
        remaining = booking.total_amount - total_paid
        form.amount.data = remaining if remaining > 0 else booking.total_amount
    
    if form.validate_on_submit():
        payment = Payment(
            booking_id=booking.id,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            payment_method=form.payment_method.data,
            transaction_id=form.transaction_id.data,
            notes=form.notes.data
        )
        
        db.session.add(payment)
        
        # Update booking payment status
        booking.update_payment_status()
        
        # Set payment date on booking if not already set
        if not booking.payment_date:
            booking.payment_date = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Payment of ${form.amount.data:.2f} processed successfully', 'success')
        return redirect(url_for('booking.details', booking_id=booking.id))
    
    return render_template('booking/add_payment.html', form=form, booking=booking)

@booking_bp.route('/<int:booking_id>/edit_total', methods=['POST'])
def edit_total(booking_id):
    """Edit the total amount of a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Get the new total from the form submission
    new_total = request.form.get('total_amount', type=float)
    
    if new_total is not None:
        booking.total_amount = new_total
        db.session.commit()
        flash(f'Total amount updated to ${new_total:.2f}', 'success')
    else:
        flash('Invalid amount provided', 'danger')
    
    return redirect(url_for('booking.details', booking_id=booking.id))

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

@booking_bp.route('/api/<int:booking_id>/details', methods=['GET'])
def booking_details_api(booking_id):
    """API endpoint to get booking details for AJAX loading"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Format service items
    service_items = []
    for item in booking.service_items:
        # Check if this item has confirmation details
        confirmation_doc = Document.query.filter_by(
            service_item_id=item.id, 
            document_type='CONFIRMATION'
        ).first()
        
        confirmation_data = None
        if confirmation_doc:
            confirmation_data = {
                'reference': confirmation_doc.document_number
            }
            
            # Add supplier info if available
            try:
                if confirmation_doc.notes:
                    doc_data = json.loads(confirmation_doc.notes)
                    if 'supplier' in doc_data:
                        confirmation_data['supplier'] = doc_data['supplier']
            except (json.JSONDecodeError, ValueError):
                pass
                
        service_items.append({
            'id': item.id,
            'service_type': item.service_type,
            'start_date': item.start_date.strftime('%d %b'),
            'end_date': item.end_date.strftime('%d %b %Y'),
            'description': item.description,
            'amount': item.amount,
            'status': item.status,
            'confirmation': confirmation_data
        })
    
    # Return JSON response with booking details
    return jsonify({
        'id': booking.id,
        'reference_number': booking.reference_number,
        'status': booking.status,
        'created_at': booking.created_at.strftime('%d %b %Y'),
        'total_amount': booking.total_amount,
        'customer_name': booking.requester.username,
        'customer_email': booking.requester.email,
        'service_items': service_items
    })

@booking_bp.route('/api/service/<int:item_id>/details', methods=['GET'])
def service_item_details_api(item_id):
    """API endpoint to get service item details including confirmation form HTML"""
    import sys
    import json
    
    service_item = ServiceItem.query.get_or_404(item_id)
    
    # Get confirmation document if available
    confirmation_doc = Document.query.filter_by(
        service_item_id=service_item.id, 
        document_type='CONFIRMATION'
    ).first()
    
    # Prepare confirmation data with defaults
    confirmation_data = {
        'confirmation_reference': '',
        'supplier': 'Direct'
    }
    
    # Add service-specific default fields
    if service_item.service_type == 'FLIGHT':
        confirmation_data.update({
            'passenger_count': {
                'adults': 1,
                'children': 0,
                'infants': 0
            },
            'passenger_names': [],
            'airline': '',
            'flight_number': '',
            'departure_airport': '',
            'arrival_airport': '',
            'flight_date': service_item.start_date.strftime('%Y-%m-%d'),
            'flight_time': '',
            'travel_class': 'Economy',
            'terminal': '',
            'ticket_number': '',
            'pnr': ''
        })
    elif service_item.service_type == 'HOTEL':
        confirmation_data.update({
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
        })
    elif service_item.service_type == 'VISA':
        confirmation_data.update({
            'applicant_name': '',
            'passport_number': '',
            'nationality': '',
            'date_of_birth': '',
            'gender': '',
            'destination_country': '',
            'visa_type': 'Tourist',
            'application_date': service_item.start_date.strftime('%Y-%m-%d'),
            'application_status': 'Applied',
            'valid_from': '',
            'valid_until': service_item.end_date.strftime('%Y-%m-%d'),
            'number_of_entries': 'Single',
            'processing_type': 'Standard',
            'expected_completion': '',
            'special_notes': ''
        })
    elif service_item.service_type == 'INSURANCE':
        confirmation_data.update({
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
        })
    
    if confirmation_doc:
        try:
            if confirmation_doc.notes:
                parsed_data = json.loads(confirmation_doc.notes)
                # Update defaults with parsed data
                confirmation_data.update(parsed_data)
                # Add confirmation reference number
                confirmation_data['confirmation_reference'] = confirmation_doc.document_number
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing JSON in API: {str(e)}", file=sys.stderr)
    
    # Determine which form template to use
    if service_item.service_type == 'FLIGHT':
        form_template = 'booking/forms/confirm_flight_form.html'
    elif service_item.service_type == 'HOTEL':
        form_template = 'booking/forms/confirm_hotel_form.html'
    elif service_item.service_type == 'TRANSPORT':
        form_template = 'booking/forms/confirm_transport_form.html'
    elif service_item.service_type == 'VISA':
        form_template = 'booking/forms/confirm_visa_form.html'
    elif service_item.service_type == 'INSURANCE':
        form_template = 'booking/forms/confirm_insurance_form.html'
    else:
        form_template = 'booking/forms/confirm_generic_form.html'
    
    # Render the form template to HTML
    form_html = render_template(
        form_template,
        service_item=service_item,
        confirmation_data=confirmation_data,
        confirmation_doc=confirmation_doc,
        inline_form=True  # Flag to indicate this is for inline display
    )
    
    # Return both the data and the rendered form HTML
    return jsonify({
        'id': service_item.id,
        'booking_id': service_item.booking_id,
        'service_type': service_item.service_type,
        'description': service_item.description,
        'start_date': service_item.start_date.strftime('%Y-%m-%d'),
        'end_date': service_item.end_date.strftime('%Y-%m-%d'),
        'amount': service_item.amount,
        'status': service_item.status,
        'has_confirmation': confirmation_doc is not None,
        'confirmation_reference': confirmation_doc.document_number if confirmation_doc else None,
        'form_html': form_html
    })