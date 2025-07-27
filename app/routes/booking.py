import uuid
import json
import sys
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
import os
import base64
from werkzeug.utils import secure_filename

from app import db
from app.models.user import User
from app.models.booking import Booking, Payment
from app.models.customer import Customer
from app.models.service import ServiceItem, Document
from app.models import STATUS_REQUEST, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from flask_login import current_user, login_required
from app.utils.openai_helper import analyze_flight_ticket

from app.forms.booking import BookingRequestForm, ServiceItemForm
from app.forms.status import UpdateServiceStatusForm
from app.forms.invoice import GenerateInvoiceForm, PaymentForm

# Create a blueprint for booking-related routes
booking_bp = Blueprint('booking', __name__)

def cascade_booking_status_to_service_items(booking, new_status):
    """Helper function to ensure service items follow booking status changes"""
    if new_status == STATUS_IN_PROGRESS:
        # Update ALL service items to IN_PROGRESS status when booking moves to IN_PROGRESS
        for item in booking.service_items:
            if item.status != STATUS_CONFIRMED:  # Don't change already confirmed items
                old_item_status = item.status
                item.status = STATUS_IN_PROGRESS
                
                # DON'T automatically mark as invoiced - invoicing only happens when explicitly generating an invoice
                # Invoice fields should only be set when actually generating invoice, not when starting operations
                
                print(f"CASCADED: Service item {item.id} from {old_item_status} to IN_PROGRESS", file=sys.stderr)
        
        print(f"CASCADE COMPLETE: All eligible service items updated to IN_PROGRESS for booking {booking.id}", file=sys.stderr)



@booking_bp.route('/api/<int:booking_id>/details', methods=['GET'])
def booking_api_details(booking_id):
    """API endpoint to get booking details for the dashboard"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Prepare service items data
    service_items = []
    for item in booking.service_items:
        # Find confirmation document if it exists
        confirmation_doc = next((doc for doc in item.documents if doc.document_type == 'CONFIRMATION'), None)
        confirmation_data = None
        
        if confirmation_doc:
            try:
                # Parse JSON notes if available
                confirmation_data = {
                    'reference': confirmation_doc.document_number,
                    'supplier': ''
                }
                
                if confirmation_doc.notes:
                    notes_data = json.loads(confirmation_doc.notes)
                    if 'supplier' in notes_data:
                        confirmation_data['supplier'] = notes_data['supplier']
            except:
                # If JSON parsing fails, just use document number
                pass
        
        # Format dates for display
        start_date = item.start_date.strftime('%d %b %Y')
        end_date = item.end_date.strftime('%d %b %Y')
        
        service_items.append({
            'id': item.id,
            'service_type': item.service_type,
            'start_date': start_date,
            'end_date': end_date,
            'description': item.description,
            'amount': item.amount,
            'status': item.status,
            'confirmation': confirmation_data
        })
    
    # Format data for response
    booking_data = {
        'id': booking.id,
        'reference_number': booking.reference_number,
        'user_id': booking.user_id,
        'user_name': booking.requester.username,
        'status': booking.status,
        'created_at': booking.created_at.strftime('%d %b %Y'),
        'total_amount': booking.total_amount,
        'service_items': service_items
    }
    
    return jsonify(booking_data)

@booking_bp.route('/create-from-detail', methods=['POST'])
def create_booking_from_detail():
    """Create a new booking from the booking details page"""
    from app.models.customer import Customer
    
    if request.method == 'POST':
        # Get the customer ID from the form
        customer_id = request.form.get('customer')
        request_id = request.form.get('request_id')
        
        if customer_id:
            customer = Customer.query.get(int(customer_id))
            if customer:
                # Generate reference number (same format as request_id if provided)
                reference = request_id or f"REQ-{str(uuid.uuid4())[:8].upper()}"
                
                # Create the booking
                booking = Booking(
                    reference_number=reference,
                    user_id=1,  # Use a default user_id (first admin user)
                    customer_id=customer.id,
                    status=STATUS_REQUEST
                )
                
                db.session.add(booking)
                db.session.commit()
                
                flash(f'Booking {reference} created successfully!', 'success')
                return redirect(url_for('booking.details', booking_id=booking.id))
            else:
                flash('Customer not found!', 'danger')
        else:
            flash('Please select a customer!', 'danger')
    
    # If something went wrong, redirect back to the dashboard
    return redirect(url_for('main.dashboard'))

@booking_bp.route('/new/detail', methods=['GET'])
def new_booking_detail():
    """Create a new booking using the booking details page"""
    # Create an empty booking form
    service_form = ServiceItemForm()
    status_form = UpdateServiceStatusForm()
    
    # Get all customers for the customer selection modal
    from app.models.customer import Customer
    customers = Customer.query.all()
    
    # Generate a new request ID
    request_id = f"IR-{str(uuid.uuid4())[:5].upper()}"
    
    return render_template(
        'booking/booking_details_new.html',
        booking=None,
        service_form=service_form,
        status_form=status_form,
        customers=customers,
        is_new_booking=True,
        request_id=request_id
    )

@booking_bp.route('/new', methods=['GET', 'POST'])
def new_booking():
    """Create a new booking request with itinerary items"""
    form = BookingRequestForm()
    
    # Get all customers for customer selection dropdown
    from app.models.customer import Customer
    customers = Customer.query.all()
    form.customer.choices = [(str(customer.id), f"{customer.name} ({customer.email})") for customer in customers]
    
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
                    'amount': float(form.amount.data) if form.amount.data else None,
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
            
            # Check if we already have a booking reference in the request - if so, this is likely an update
            reference = form.request_id.data
            existing_booking = Booking.query.filter_by(reference_number=reference).first()
            
            # When updating an existing booking with invoice amount, we'll bypass strict validation
            # This allows updating just the total_amount without requiring customer selection again
            if existing_booking and request.form.get('save_action') == 'generate_invoice' and (request.form.get('total_amount') or request.form.get('invoice_total')):
                # We have an existing booking, we're generating invoice, and we have a total amount
                print(f"Updating existing booking {reference} with new invoice amount")
                action = 'generate_invoice'
                booking = existing_booking
                
                # Jump directly to the invoice generation code
                import sys
                print(f"Generate invoice action detected, form data: {request.form}", file=sys.stderr)
                
                # Update the total amount if provided
                invoice_total = request.form.get('invoice_total') or request.form.get('total_amount')
                try:
                    invoice_total = float(invoice_total) if invoice_total else None
                    if invoice_total and invoice_total > 0:
                        print(f"Setting booking total to {invoice_total}", file=sys.stderr)
                        booking.total_amount = invoice_total
                except (ValueError, TypeError):
                    print(f"Invalid invoice_total: {invoice_total}", file=sys.stderr)
                
                # Generate invoice number if one doesn't exist
                if not booking.invoice_number:
                    booking.generate_invoice_number()
                    print(f"Generated invoice number: {booking.invoice_number}", file=sys.stderr)
                
                # Update the booking status to IN_PROGRESS
                booking.status = STATUS_IN_PROGRESS
                
                # Invoice data is stored in the booking table as the primary source
                print(f"Invoice data stored in booking table: {booking.invoice_number}", file=sys.stderr)
                
                # Save changes
                db.session.commit()
                flash(f'Invoice {booking.invoice_number} updated successfully with new amount: {booking.total_amount}', 'success')
                
                # Redirect to the booking details page
                return redirect(url_for('booking.details', booking_id=booking.id))
                
            elif form.validate():
                # Regular validation for new bookings
                # Get the action type (save or generate_invoice)
                action = request.form.get('save_action', 'save')
                
                # Create a unique reference number
                reference = form.request_id.data
                
                # Check if a booking with this reference already exists
                booking = Booking.query.filter_by(reference_number=reference).first()
                
                # Only create a new booking if one doesn't already exist with this reference
                if not booking:
                    # Get the selected customer
                    from app.models.customer import Customer
                    customer = Customer.query.get(int(form.customer.data))
                    
                    # Create the booking with customer ID
                    booking = Booking(
                        reference_number=reference,
                        user_id=1,  # Use a default user_id (first admin user)
                        customer_id=customer.id,  # Store customer ID
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
                                amount=float(item_data['amount']) if item_data['amount'] else 0.0,
                                status=STATUS_REQUEST
                            )
                            
                            db.session.add(service_item)
                        
                        db.session.commit()
                        booking.calculate_total()
                        db.session.commit()
                
                # Also add the current item if it has data
                elif form.description.data:  # Remove amount requirement for package pricing
                    service_item = ServiceItem(
                        booking_id=booking.id,
                        service_type=form.service_type.data,
                        start_date=form.from_date.data,
                        end_date=form.to_date.data,
                        description=form.description.data,
                        amount=form.amount.data if form.amount.data else 0.0,
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
                    
                    # Update the total amount if provided either in the modal form or direct form
                    # First check for invoice_total (from modal)
                    invoice_total = request.form.get('invoice_total')
                    
                    # If not found, try total_amount (from direct form field)
                    if not invoice_total:
                        invoice_total = request.form.get('total_amount')
                        
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
                    
                    # Update the booking status to IN_PROGRESS
                    booking.status = STATUS_IN_PROGRESS
                    
                    # Use helper function to cascade status to all service items
                    cascade_booking_status_to_service_items(booking, STATUS_IN_PROGRESS)
                    
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
    
    # Get all customers for the customer selection modal
    from app.models.customer import Customer
    customers = Customer.query.all()
    
    # Optionally add a booking form for new bookings
    booking_form = BookingRequestForm()
    
    # Get credit memos for this booking
    from app.models.invoice import Invoice
    credit_memos = Invoice.query.filter_by(booking_id=booking.id, is_credit_memo=True).all()
    credit_memo_amount = sum(abs(memo.total_amount) for memo in credit_memos)
    
    print(f"DEBUG: Found {len(credit_memos)} credit memos for booking {booking.id}")
    for memo in credit_memos:
        print(f"DEBUG: Credit memo {memo.invoice_number}: ${memo.total_amount}")
    
    return render_template(
        'booking/booking_details_new.html',
        booking=booking,
        service_form=service_form,
        status_form=status_form,
        customers=customers,
        booking_form=booking_form,
        credit_memos=credit_memos,
        credit_memo_amount=credit_memo_amount
    )

@booking_bp.route('/<int:booking_id>/add_service', methods=['POST'])
def add_service_item(booking_id):
    """Add a service item to an existing booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if booking is already invoiced - prevent adding new services
    if booking.invoice_number:
        flash('Cannot add new services to an invoiced booking. Please create a new booking or issue a credit memo for changes.', 'error')
        return redirect(url_for('booking.details', booking_id=booking.id))
    
    form = ServiceItemForm()
    
    if form.validate_on_submit():
        service_item = ServiceItem(
            booking_id=booking.id,
            service_type=form.service_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            description=form.description.data,
            amount=form.amount.data if form.amount.data else 0.0,  # Default to 0.0 for database compatibility
            status=STATUS_REQUEST
        )
        
        from app.models.user import Agent
        # Assign to an agent with the matching specialty if available
        agent = Agent.query.filter_by(specialty=form.service_type.data).first()
        if agent:
            service_item.agent_id = agent.id
        
        import sys
        db.session.add(service_item)
        
        # Update the booking's total amount (for display purposes only)
        booking.calculate_total()
        
        # Check if booking already has an invoice
        has_invoice = booking.invoice_number is not None
        print(f"Booking has invoice: {has_invoice} - Invoice #: {booking.invoice_number}", file=sys.stderr)
        
        # Set service status based on booking status, but DO NOT auto-invoice
        if booking.status == STATUS_IN_PROGRESS:
            # Set the new service item to IN_PROGRESS as well
            service_item.status = STATUS_IN_PROGRESS
            print(f"Set new service item to IN_PROGRESS status", file=sys.stderr)
        
        # NEVER automatically mark as invoiced - only when user explicitly generates invoice
        service_item.is_invoiced = False
        print(f"Service item added without auto-invoicing", file=sys.stderr)
        
        # Recalculate booking total
        booking.calculate_total()
        
        db.session.commit()
        
        # Check if user wants to add additional details
        add_confirmation = request.form.get('add_confirmation')
        if add_confirmation:
            flash('Service item added successfully. Please fill in additional details.', 'success')
            return redirect(url_for('booking.confirm_service', item_id=service_item.id))
        else:
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
        if booking.payment_status not in ['FULL', 'PARTIAL']:
            flash('Error: Payment is required before starting operations', 'danger')
            return redirect(url_for('booking.details', booking_id=booking.id))
        
        # If it's only partially paid, show a warning
        if booking.payment_status == 'PARTIAL':
            flash('Warning: This booking has only been partially paid', 'warning')
            
        booking.status = new_status
        
        # Use helper function to cascade status to all service items
        cascade_booking_status_to_service_items(booking, new_status)
        
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
        if new_status == STATUS_CONFIRMED and not booking.can_complete():
            flash('Cannot mark as CONFIRMED until all service items are confirmed', 'danger')
            return redirect(url_for('booking.details', booking_id=booking.id))
        
        # REMOVED AUTOMATIC INVOICE GENERATION - Invoice generation should be independent from status changes
        # Users should manually generate invoices through the "Generate Invoice" button
        # This ensures complete separation between booking status changes and invoicing
        
        # ALWAYS cascade status to service items when moving to IN_PROGRESS
        if new_status == STATUS_IN_PROGRESS:
            cascade_booking_status_to_service_items(booking, new_status)
            print(f"CASCADING STATUS: Updated all service items to IN_PROGRESS for booking {booking.id}", file=sys.stderr)
        
        # Check payment status when moving to IN_PROGRESS
        if new_status == STATUS_IN_PROGRESS and booking.payment_status != 'FULL':
            flash('Warning: This booking has not been fully paid', 'warning')
        
        booking.status = new_status
        db.session.commit()
        flash(f'Booking status updated to {booking.status}', 'success')
    
    return redirect(url_for('booking.details', booking_id=booking.id))

@booking_bp.route('/search', methods=['GET'])
def search():
    """Redirect to the new find bookings page"""
    return redirect(url_for('main.find_bookings'))

def export_bookings_csv(bookings):
    """Export search results to CSV"""
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Reference Number', 'Customer', 'Created Date', 'Status', 
        'Total Amount', 'Payment Status', 'Invoice Number', 
        'Service Types', 'Service Count'
    ])
    
    # Write data
    for booking in bookings:
        customer_name = booking.customer.name if hasattr(booking, 'customer') and booking.customer else 'No Customer'
        service_types = ', '.join(set(item.service_type for item in booking.service_items))
        service_count = len(booking.service_items)
        
        writer.writerow([
            booking.reference_number,
            customer_name,
            booking.created_at.strftime('%Y-%m-%d'),
            booking.status,
            f"{booking.total_amount:.2f}",
            booking.payment_status,
            booking.invoice_number or 'No Invoice',
            service_types,
            service_count
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=booking_search_results.csv'
    
    return response

@booking_bp.route('/service_item/<int:item_id>/update_status', methods=['POST'])
def update_service_status(item_id):
    """Update the status of a specific service item"""
    service_item = ServiceItem.query.get_or_404(item_id)
    booking = service_item.booking
    form = UpdateServiceStatusForm()
    
    if form.validate_on_submit():
        # Check if the booking is in the correct status for service confirmation
        if form.status.data == STATUS_CONFIRMED and booking.status != STATUS_IN_PROGRESS:
            flash('Error: Booking must be IN_PROGRESS before services can be confirmed', 'danger')
        else:
            # Update the service item status
            service_item.status = form.status.data
            db.session.commit()
            
            # If the status is changed to CONFIRMED, check if all items are now confirmed
            if service_item.status == STATUS_CONFIRMED:
                if booking.can_complete():
                    booking.status = STATUS_CONFIRMED
                    db.session.commit()
                    flash('All services are confirmed. Booking marked as confirmed!', 'success')
                
            flash(f'Service item status updated to {service_item.status}', 'success')
    
    # Check for referrer to return to the correct page
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    
    return redirect(url_for('booking.details', booking_id=service_item.booking_id))

@booking_bp.route('/service_item/<int:item_id>/delete', methods=['POST'])
def delete_service_item(item_id):
    """Permanently delete a service item that is not confirmed"""
    service_item = ServiceItem.query.get_or_404(item_id)
    booking = service_item.booking
    booking_id = booking.id
    
    # Only allow deletion if the service is not confirmed
    if service_item.status == STATUS_CONFIRMED:
        flash('Cannot delete a confirmed service item. Please cancel it instead.', 'danger')
        return redirect(url_for('booking.details', booking_id=booking_id))
    
    # First delete any documents related to this service item
    Document.query.filter_by(service_item_id=service_item.id).delete()
    
    # Delete the service item
    db.session.delete(service_item)
    db.session.commit()
    
    # Recalculate booking total
    booking.calculate_total()
    db.session.commit()
    
    flash('Service item successfully deleted', 'success')
    return redirect(url_for('booking.details', booking_id=booking_id))

@booking_bp.route('/service_item/<int:item_id>/cancel', methods=['POST'])
def cancel_service_item(item_id):
    """Cancel a service item and generate a credit memo if it was already invoiced"""
    import sys
    print(f"CANCEL SERVICE: Starting cancellation for item_id={item_id}", file=sys.stderr)
    
    try:
        service_item = ServiceItem.query.get_or_404(item_id)
        booking = service_item.booking
        print(f"CANCEL SERVICE: Found service item {item_id} for booking {booking.id}", file=sys.stderr)
    except Exception as e:
        print(f"CANCEL SERVICE ERROR: Failed to get service item {item_id}: {e}", file=sys.stderr)
        flash('Service item not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if this item can be cancelled
    if service_item.is_cancelled:
        flash('This service item has already been cancelled', 'warning')
        return redirect(url_for('booking.details', booking_id=booking.id))
    
    # Allow cancellation of all items, including confirmed ones
    # We removed the restriction here to enable cancellation of confirmed services
    
    # Process cancellation
    reason = request.form.get('cancel_reason', '')
    print(f"CANCEL SERVICE: Form data - reason='{reason}'", file=sys.stderr)
    
    try:
        credit_amount_str = request.form.get('credit_amount', str(service_item.amount))
        credit_amount = float(credit_amount_str) if credit_amount_str else service_item.amount
        print(f"CANCEL SERVICE: Credit amount = {credit_amount}", file=sys.stderr)
        
        cancellation_fee_str = request.form.get('cancellation_fee', '0')
        cancellation_fee = float(cancellation_fee_str) if cancellation_fee_str else 0
        print(f"CANCEL SERVICE: Cancellation fee = {cancellation_fee}", file=sys.stderr)
    except (ValueError, TypeError) as e:
        print(f"CANCEL SERVICE ERROR: Failed to parse amounts: {e}", file=sys.stderr)
        flash('Invalid credit amount or cancellation fee entered', 'error')
        return redirect(url_for('booking.details', booking_id=booking.id))
    
    # Mark item as cancelled
    service_item.is_cancelled = True
    
    # If the item was invoiced, generate a credit memo
    if service_item.is_invoiced and service_item.invoice_number:
        credit_memo_number = booking.generate_credit_memo_number()
        service_item.credit_memo_number = credit_memo_number
        
        # Create a credit memo with negative amount
        # This is a record of the refund that would be issued
        from datetime import datetime
        credit_memo_date = datetime.utcnow()
        
        # Create a separate invoice record for the credit memo
        # This will be shown as a negative invoice amount
        from app.models.invoice import Invoice
        
        # Use the credit amount entered by user (not the original service amount)
        try:
            final_credit_amount = credit_amount  # Use the user-entered credit amount
            cancellation_fee_amount = cancellation_fee
            
            # The net credit is the credit amount minus cancellation fee
            net_credit_amount = final_credit_amount - cancellation_fee_amount
        except (ValueError, TypeError):
            # Fallback to original amount if parsing fails
            final_credit_amount = service_item.amount
            cancellation_fee_amount = 0
            net_credit_amount = service_item.amount
        
        # Build notes for the credit memo
        credit_notes = f"Credit memo for cancelled service: {service_item.service_type} - {service_item.description}"
        if cancellation_fee_amount > 0:
            credit_notes += f"\nCancellation fee applied: ${cancellation_fee_amount:.2f}"
        if reason:
            credit_notes += f"\nReason: {reason}"
        
        # Create a new invoice record for the credit memo
        credit_memo = Invoice(
            booking_id=booking.id,
            invoice_number=credit_memo_number,
            invoice_date=credit_memo_date,
            total_amount=-net_credit_amount,  # Negative amount for net credit after fees
            notes=credit_notes,
            is_credit_memo=True,
            referenced_invoice=service_item.invoice_number
        )
        db.session.add(credit_memo)
        
        # Credit memo is an invoice document, not a payment
        # Payments are actual money received - credit memos are invoice adjustments
        
        # Link the credit memo to the original invoice in the database
        # This is important for reporting and settlement
        # Find the original invoice this credit memo references
        original_invoice = Invoice.query.filter_by(invoice_number=service_item.invoice_number).first()
        if original_invoice:
            # Add a note to the original invoice about the credit memo
            if original_invoice.notes:
                original_invoice.notes += f"\nCredit memo {credit_memo_number} applied for ${abs(net_credit_amount):.2f}"
            else:
                original_invoice.notes = f"Credit memo {credit_memo_number} applied for ${abs(net_credit_amount):.2f}"
            
            # Update the original invoice's settled amount if we have a settled_amount field
            # If the field doesn't exist, we'll create it in another migration
            print(f"Credit memo {credit_memo_number} linked to invoice {original_invoice.invoice_number}", file=sys.stderr)
        
        # DO NOT change the booking total amount when cancelling services
        # The original invoice amount should remain the same
        # Credits and refunds are handled separately through payment records
        
        # Update payment status
        booking.update_payment_status()
        
        print(f"Generated credit memo {credit_memo_number} for cancelled item {item_id}", file=sys.stderr)
        print(f"Credit memo amount: ${net_credit_amount}", file=sys.stderr)
        flash(f'Credit memo {credit_memo_number} generated for cancelled service item with amount ${abs(net_credit_amount):.2f}', 'success')
    else:
        # Just mark the item as cancelled without credit memo
        print(f"Item {item_id} cancelled but no credit memo generated (not invoiced)", file=sys.stderr)
        
        # DO NOT change the booking total - it should remain as the original invoice amount
        
    # Update item status and save
    try:
        db.session.commit()
        print(f"CANCEL SERVICE: Database commit successful for item {item_id}", file=sys.stderr)
    except Exception as e:
        print(f"CANCEL SERVICE ERROR: Database commit failed: {e}", file=sys.stderr)
        db.session.rollback()
        flash('Failed to cancel service item due to database error', 'error')
        return redirect(url_for('booking.details', booking_id=booking.id))
    
    flash(f'Service item successfully cancelled', 'success')
    print(f"CANCEL SERVICE: Redirecting to booking details for booking {booking.id}", file=sys.stderr)
    
    try:
        redirect_url = url_for('booking.details', booking_id=booking.id)
        print(f"CANCEL SERVICE: Generated redirect URL: {redirect_url}", file=sys.stderr)
        return redirect(redirect_url)
    except Exception as e:
        print(f"CANCEL SERVICE ERROR: Failed to generate redirect URL: {e}", file=sys.stderr)
        flash('Service cancelled but failed to redirect', 'warning')
        return redirect(url_for('main.dashboard'))

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
        supplier_code = request.form.get('supplier', '')
        form_notes = request.form.get('notes', '')
        service_type = request.form.get('service_type', '')
        
        # Get the action type (save_request, confirm, next, complete)
        action = request.form.get('action', 'confirm')
        
        print(f"Action: {action}", file=sys.stderr)
        print(f"confirmation_reference: {confirmation_reference}", file=sys.stderr)
        print(f"supplier_code: {supplier_code}", file=sys.stderr)
        print(f"form_notes: {form_notes}", file=sys.stderr)
        print(f"service_type: {service_type}, actual service type: {service_item.service_type}", file=sys.stderr)
        
        # Look up the supplier object by code if provided
        from app.models.supplier import Supplier
        supplier_object = None
        if supplier_code:
            supplier_object = Supplier.query.filter_by(code=supplier_code).first()
            if supplier_object:
                print(f"Found supplier: {supplier_object.name} (ID: {supplier_object.id})", file=sys.stderr)
            else:
                print(f"No supplier found with code: {supplier_code}", file=sys.stderr)
        
        # Handle different action types
        if action == 'save_request':
            # Save as draft without validation - just save the data
            print("Saving as request (draft mode) - no validation required", file=sys.stderr)
            # Keep current status, don't change to CONFIRMED, but allow it to be confirmable later
            # If service is already CONFIRMED, move it back to IN_PROGRESS so it can be confirmed again
            if service_item.status == STATUS_CONFIRMED:
                service_item.status = STATUS_IN_PROGRESS
                print(f"Moving service item {service_item.id} from CONFIRMED back to IN_PROGRESS for re-confirmation", file=sys.stderr)
        elif action == 'confirm':
            # Full confirmation with validation
            print("Full confirmation mode - applying validation", file=sys.stderr)
            
            # CRITICAL BUSINESS RULE: Service items can only be confirmed if booking is IN_PROGRESS
            if service_item.booking.status != STATUS_IN_PROGRESS:
                flash('Cannot confirm service items until booking operations are started. The booking must be in IN_PROGRESS status first.', 'danger')
                return redirect(url_for('booking.details', booking_id=service_item.booking_id))
            
            # Set item status to CONFIRMED when confirming
            if service_item.status == STATUS_IN_PROGRESS:
                service_item.status = STATUS_CONFIRMED
            elif service_item.status == STATUS_REQUEST:
                # Allow confirmation from REQUEST status too (for the checkbox flow)
                service_item.status = STATUS_CONFIRMED
            elif service_item.status == STATUS_CONFIRMED:
                # Allow re-confirmation of already confirmed items
                service_item.status = STATUS_CONFIRMED
                print(f"Re-confirming already confirmed service item {service_item.id}", file=sys.stderr)
            else:
                flash('Service item must be in REQUEST, IN_PROGRESS, or CONFIRMED status before it can be confirmed.', 'danger')
                return redirect(url_for('booking.details', booking_id=service_item.booking_id))
        
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
        
        # Process cost tracking data (common for all service types)
        cost_amount_str = request.form.get('cost_amount', '')
        cost_currency = request.form.get('cost_currency', 'USD')
        payment_due_date = request.form.get('payment_due_date', '')
        is_paid = 'is_paid' in request.form
        
        # Convert cost amount to float, but keep None for empty values (package pricing)
        cost_amount = None
        if cost_amount_str and cost_amount_str.strip():
            try:
                cost_amount = float(cost_amount_str)
            except ValueError:
                cost_amount = None
        
        print(f"Cost tracking data: amount={cost_amount}, currency={cost_currency}, due_date={payment_due_date}, is_paid={is_paid}", file=sys.stderr)
        
        if service_item.service_type == 'FLIGHT':
            # Handle multi-segment flight confirmation
            flight_type = request.form.get('flight_type', 'one_way')
            print(f"Processing flight confirmation with type: {flight_type}", file=sys.stderr)
            
            # Collect flight segments
            segments = []
            segment_index = 0
            
            # Process all segments from the form
            while f'segments[{segment_index}][airline]' in request.form:
                # Get segment-specific passenger names, types, and ticket numbers
                segment_passenger_names = request.form.getlist(f'segments[{segment_index}][passenger_names][]')
                segment_passenger_types = request.form.getlist(f'segments[{segment_index}][passenger_types][]')
                segment_ticket_numbers = request.form.getlist(f'segments[{segment_index}][ticket_numbers][]')
                
                segment_data = {
                    'airline': request.form.get(f'segments[{segment_index}][airline]', ''),
                    'flight_number': request.form.get(f'segments[{segment_index}][flight_number]', ''),
                    'departure_airport': request.form.get(f'segments[{segment_index}][departure_airport]', ''),
                    'arrival_airport': request.form.get(f'segments[{segment_index}][arrival_airport]', ''),
                    'flight_date': request.form.get(f'segments[{segment_index}][flight_date]', ''),
                    'departure_time': request.form.get(f'segments[{segment_index}][departure_time]', ''),
                    'arrival_time': request.form.get(f'segments[{segment_index}][arrival_time]', ''),
                    'duration': request.form.get(f'segments[{segment_index}][duration]', ''),
                    'connection_type': request.form.get(f'segments[{segment_index}][connection_type]', ''),
                    'aircraft_type': request.form.get(f'segments[{segment_index}][aircraft_type]', ''),
                    'pnr': request.form.get(f'segments[{segment_index}][pnr]', ''),
                    'passenger_names': segment_passenger_names,
                    'passenger_types': segment_passenger_types,
                    'ticket_numbers': segment_ticket_numbers,
                }
                
                # Only add segment if it has essential data
                if segment_data['airline'] and segment_data['flight_number']:
                    segments.append(segment_data)
                    print(f"Added segment {segment_index + 1}: {segment_data['airline']} {segment_data['flight_number']} with {len(segment_passenger_names)} passengers", file=sys.stderr)
                
                segment_index += 1
            
            # If no segments data found, fall back to old single-flight format for backward compatibility
            if not segments:
                segments = [{
                    'airline': request.form.get('airline', ''),
                    'flight_number': request.form.get('flight_number', ''),
                    'departure_airport': request.form.get('departure_airport', ''),
                    'arrival_airport': request.form.get('arrival_airport', ''),
                    'flight_date': request.form.get('flight_date', ''),
                    'departure_time': request.form.get('flight_time', ''),  # Old field name
                    'arrival_time': request.form.get('arrival_time', ''),
                    'duration': request.form.get('duration', ''),
                    'connection_type': request.form.get('connection_type', ''),
                    'aircraft_type': request.form.get('aircraft_type', ''),
                }]
                print("Using legacy single-flight format for backward compatibility", file=sys.stderr)
            
            flight_details = {
                'flight_type': flight_type,
                'segments': segments,
                'travel_class': request.form.get('travel_class', ''),
                'terminal': request.form.get('terminal', ''),
                'baggage_allowance': request.form.get('baggage_allowance', ''),
                'seat_assignment': request.form.get('seat_assignment', ''),
                'ticket_number': request.form.get('ticket_number', ''),
                'pnr': request.form.get('pnr', ''),
                'supplier': supplier_code,
                'supplier_id': supplier_object.id if supplier_object else None,
                'supplier_name': supplier_object.name if supplier_object else 'Unknown Supplier',
                'passenger_count': {
                    'adults': request.form.get('adults', 1),
                    'children': request.form.get('children', 0),
                    'infants': request.form.get('infants', 0)
                },
                # Add cost tracking fields
                'cost_amount': cost_amount,
                'cost_currency': cost_currency,
                'payment_due_date': payment_due_date,
                'is_paid': is_paid,
                'notes': form_notes,
                # Legacy fields for backward compatibility with existing voucher templates
                'airline': segments[0]['airline'] if segments else '',
                'flight_number': segments[0]['flight_number'] if segments else '',
                'departure_airport': segments[0]['departure_airport'] if segments else '',
                'arrival_airport': segments[0]['arrival_airport'] if segments else '',
                'flight_date': segments[0]['flight_date'] if segments else '',
                'flight_time': segments[0]['departure_time'] if segments else '',
                'arrival_time': segments[0]['arrival_time'] if segments else '',
                'duration': segments[0]['duration'] if segments else '',
                'connection_type': segments[0]['connection_type'] if segments else '',
                'aircraft_type': segments[0]['aircraft_type'] if segments else '',
            }
            
            # Get global passenger names, types, and ticket numbers (for backward compatibility)
            global_passenger_names = request.form.getlist('passenger_names[]')
            global_passenger_types = request.form.getlist('passenger_types[]')
            global_ticket_numbers = request.form.getlist('ticket_numbers[]')
            
            # If global passengers provided but no segment-specific passengers, assign globally to all segments
            if global_passenger_names and not any(seg.get('passenger_names') for seg in segments):
                print("Assigning global passengers to all segments for backward compatibility", file=sys.stderr)
                # Ensure we have passenger types for all passengers (default to Adult if missing)
                if len(global_passenger_types) < len(global_passenger_names):
                    global_passenger_types.extend(['Adult'] * (len(global_passenger_names) - len(global_passenger_types)))
                
                for segment in segments:
                    segment['passenger_names'] = global_passenger_names
                    segment['passenger_types'] = global_passenger_types
                    segment['ticket_numbers'] = global_ticket_numbers
                
                flight_details['passenger_names'] = global_passenger_names
                flight_details['passenger_types'] = global_passenger_types
                flight_details['ticket_numbers'] = global_ticket_numbers
            else:
                # Collect all unique passengers from all segments for global list
                all_passengers = set()
                all_passenger_types = []
                all_tickets = []
                
                for segment in segments:
                    seg_passengers = segment.get('passenger_names', [])
                    seg_types = segment.get('passenger_types', [])
                    seg_tickets = segment.get('ticket_numbers', [])
                    
                    # Ensure passenger types array matches passenger names length
                    if len(seg_types) < len(seg_passengers):
                        seg_types.extend(['Adult'] * (len(seg_passengers) - len(seg_types)))
                        segment['passenger_types'] = seg_types
                    
                    for i, passenger in enumerate(seg_passengers):
                        if passenger and passenger not in all_passengers:
                            all_passengers.add(passenger)
                            # Add corresponding passenger type (default to Adult if not provided)
                            passenger_type = seg_types[i] if i < len(seg_types) else 'Adult'
                            all_passenger_types.append(passenger_type)
                    
                    for ticket in seg_tickets:
                        if ticket and ticket not in all_tickets:
                            all_tickets.append(ticket)
                
                flight_details['passenger_names'] = list(all_passengers)
                flight_details['passenger_types'] = all_passenger_types
                flight_details['ticket_numbers'] = all_tickets
                print(f"Collected {len(all_passengers)} unique passengers from all segments", file=sys.stderr)
            
            print(f"Final flight details with {len(segments)} segments prepared for saving", file=sys.stderr)
            print(f"Flight details JSON length: {len(json.dumps(flight_details))}", file=sys.stderr)
            
            # Save the flight details to the document
            document.notes = json.dumps(flight_details)
            
            # Verify the document has the data before saving
            print(f"Document notes set - first 200 chars: {document.notes[:200]}", file=sys.stderr)
        
        elif service_item.service_type == 'HOTEL':
            import sys
            print("Processing HOTEL confirmation form submission", file=sys.stderr)
            
            # Process new room array structure
            rooms_data = []
            room_index = 0
            while f'rooms[{room_index}][room_type]' in request.form:
                room_data = {
                    'room_type': request.form.get(f'rooms[{room_index}][room_type]', ''),
                    'board_basis': request.form.get(f'rooms[{room_index}][board_basis]', 'Room Only'),
                    'adults': int(request.form.get(f'rooms[{room_index}][adults]', '2')),
                    'children': int(request.form.get(f'rooms[{room_index}][children]', '0')),
                    'lead_passenger': request.form.get(f'rooms[{room_index}][lead_passenger]', '')
                }
                rooms_data.append(room_data)
                room_index += 1
            
            print(f"Extracted {len(rooms_data)} rooms from form: {rooms_data}", file=sys.stderr)
            
            hotel_details = {
                'hotel_name': request.form.get('hotel_name', ''),
                'from_date': request.form.get('from_date', ''),
                'to_date': request.form.get('to_date', ''),
                'meal_plan': request.form.get('meal_plan', ''),
                'status': request.form.get('status', ''),
                'cost': request.form.get('cost', ''),
                'currency': request.form.get('currency', 'USD'),
                'supplier': supplier_code,
                'supplier_id': supplier_object.id if supplier_object else None,
                'supplier_name': supplier_object.name if supplier_object else 'Unknown Supplier',
                'special_notes': request.form.get('special_notes', ''),
                'rooms': rooms_data,  # Use new room array structure
                # Add cost tracking fields
                'cost_amount': cost_amount,
                'cost_currency': cost_currency,
                'payment_due_date': payment_due_date,
                'is_paid': is_paid,
                'notes': form_notes
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
                'supplier': supplier_code,
                'supplier_id': supplier_object.id if supplier_object else None,
                'supplier_name': supplier_object.name if supplier_object else 'Unknown Supplier',
                'special_requests': request.form.get('special_requests', ''),
                # Add cost tracking fields
                'cost_amount': cost_amount,
                'cost_currency': cost_currency,
                'payment_due_date': payment_due_date,
                'is_paid': is_paid,
                'notes': form_notes
            }
            
            document.notes = json.dumps(transport_details)
            
        elif service_item.service_type == 'VISA':
            import sys
            print("Processing VISA confirmation form submission", file=sys.stderr)
            print(f"Supplier from form: '{supplier_code}'", file=sys.stderr)
            
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
                'supplier': supplier_code,
                'supplier_id': supplier_object.id if supplier_object else None,
                'supplier_name': supplier_object.name if supplier_object else 'Unknown Supplier',
                # Add cost tracking fields
                'cost_amount': cost_amount,
                'cost_currency': cost_currency,
                'payment_due_date': payment_due_date,
                'is_paid': is_paid,
                'notes': form_notes
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
                'supplier': supplier_code,
                'supplier_id': supplier_object.id if supplier_object else None,
                'supplier_name': supplier_object.name if supplier_object else 'Unknown Supplier',
                # Add cost tracking fields
                'cost_amount': cost_amount,
                'cost_currency': cost_currency,
                'payment_due_date': payment_due_date,
                'is_paid': is_paid,
                'notes': form_notes
            }
            
            document.notes = json.dumps(insurance_details)
        
        # Save changes
        import sys
        print(f"About to save document with notes: {document.notes[:100]}...", file=sys.stderr)
        
        try:
            db.session.add(document)
            db.session.commit()
            print(f"Document successfully saved to database", file=sys.stderr)
            
            # Verify the document was saved by retrieving it again
            saved_doc = Document.query.get(document.id)
            print(f"Document after commit - ID: {saved_doc.id}, Notes length: {len(saved_doc.notes) if saved_doc.notes else 0}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to save document: {e}", file=sys.stderr)
            db.session.rollback()
            flash(f'Failed to save confirmation: {e}', 'danger')
            return redirect(url_for('booking.confirm_service', item_id=item_id))
        
        # Only mark as CONFIRMED if action is 'confirm', not for 'save_request'
        if action == 'confirm':
            print(f"Marking service item {service_item.id} as CONFIRMED", file=sys.stderr)
            service_item.status = STATUS_CONFIRMED
        else:
            print(f"Keeping service item {service_item.id} in current status: {service_item.status}", file=sys.stderr)
        
        try:
            db.session.commit()
            print(f"Service item status successfully updated", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to update service item status: {e}", file=sys.stderr)
            db.session.rollback()
            flash(f'Failed to update service status: {e}', 'danger')
            return redirect(url_for('booking.confirm_service', item_id=item_id))
        
        # Create a supplier payment record based on the confirmation document (only for confirmed items)
        if action == 'confirm':
            try:
                from app.models.supplier import SupplierPayment, Supplier
                from datetime import datetime
                
                # Parse the document notes to get cost information
                confirmation_data = json.loads(document.notes)
                
                # Check if it has cost information (skip for package pricing where cost is None)
                if 'cost_amount' in confirmation_data and confirmation_data['cost_amount'] is not None and confirmation_data['cost_amount'] > 0:
                    cost_amount = float(confirmation_data['cost_amount'])
                    
                    # Get supplier information
                    supplier_id = None
                    if 'supplier_id' in confirmation_data and confirmation_data['supplier_id']:
                        supplier_id = int(confirmation_data['supplier_id'])
                    else:
                        # Try to find supplier by name
                        supplier_name = confirmation_data.get('supplier', 'Direct')
                        supplier = Supplier.query.filter_by(name=supplier_name).first()
                        if supplier:
                            supplier_id = supplier.id
                    
                    if supplier_id:
                        # Check if payment record exists for this document
                        existing_payment = SupplierPayment.query.filter_by(
                            notes=f"Payment for {service_item.service_type} confirmation document #{document.id}"
                        ).first()
                        
                        if not existing_payment:
                            # Get payment due date if available
                            payment_date = datetime.now().date()
                            due_date = payment_date
                            
                            if 'payment_due_date' in confirmation_data and confirmation_data['payment_due_date']:
                                try:
                                    due_date = datetime.strptime(confirmation_data['payment_due_date'], '%Y-%m-%d').date()
                                except ValueError:
                                    pass
                            
                            # Create payment record
                            payment = SupplierPayment(
                                supplier_id=supplier_id,
                                amount=cost_amount,
                                payment_date=payment_date,
                                due_date=due_date,
                                status='PENDING',
                                payment_reference=document.document_number,
                                payment_method='BANK_TRANSFER',
                                notes=f"Payment for {service_item.service_type} confirmation document #{document.id}"
                            )
                            
                            db.session.add(payment)
                            db.session.commit()
                            print(f"Created supplier payment of ${cost_amount} for confirmation document #{document.id}", file=sys.stderr)
                            
                            # Now create a supplier prepayment line to link the payment with the booking and service item
                            try:
                                from app.models.supplier import SupplierPrepaymentLine
                                
                                # Create the prepayment line
                                prepayment_line = SupplierPrepaymentLine(
                                    supplier_payment_id=payment.id,
                                    booking_id=service_item.booking_id,
                                    service_item_id=service_item.id,
                                    amount=cost_amount,
                                    notes=f"Auto-created for {service_item.service_type} confirmation"
                                )
                                
                                # Add additional fields if they exist in the model
                                if hasattr(SupplierPrepaymentLine, 'service_type'):
                                    prepayment_line.service_type = service_item.service_type
                                if hasattr(SupplierPrepaymentLine, 'supplier_name'):
                                    prepayment_line.supplier_name = confirmation_data.get('supplier_name', 'Unknown Supplier')
                                if hasattr(SupplierPrepaymentLine, 'confirmation_reference'):
                                    prepayment_line.confirmation_reference = confirmation_data.get('confirmation_reference', document.document_number)
                                if hasattr(SupplierPrepaymentLine, 'payment_status'):
                                    prepayment_line.payment_status = 'PENDING'
                                
                                db.session.add(prepayment_line)
                                db.session.commit()
                                print(f"Created supplier prepayment line linking payment {payment.id} to booking {service_item.booking_id} and service {service_item.id}", file=sys.stderr)
                            except Exception as e:
                                print(f"Error creating supplier prepayment line: {str(e)}", file=sys.stderr)
            except Exception as e:
                # Log the error but don't fail the response
                print(f"Error creating supplier payment: {str(e)}", file=sys.stderr)
        
        # Set appropriate success message based on action type
        if action == 'save_request':
            flash(f'{service_item.service_type} additional details saved as request', 'success')
        elif action == 'confirm':
            flash(f'{service_item.service_type} confirmation details saved and confirmed', 'success')
        else:
            flash(f'{service_item.service_type} details saved', 'success')
        
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
        
        # Only check for booking completion if we actually confirmed an item (not for save_request)
        if action == 'confirm':
            # Check if all items are now confirmed
            pending_items = ServiceItem.query.filter(
                ServiceItem.booking_id == booking_id,
                ServiceItem.status != STATUS_CONFIRMED
            ).count()
            
            if pending_items == 0:
                # All service items are confirmed, update booking status
                booking = Booking.query.get(booking_id)
                booking.status = STATUS_CONFIRMED
                db.session.commit()
                flash('All services confirmed! Booking is now confirmed.', 'success')
        
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
        'supplier': 'Direct',
        'cost_amount': 0.00,
        'cost_currency': 'USD',
        'payment_due_date': '',
        'is_paid': False,
        'notes': ''
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
                
                # Handle backward compatibility for hotel room structure
                if service_item.service_type == 'HOTEL' and 'rooms' in parsed_data:
                    if isinstance(parsed_data['rooms'], dict) and 'single' in parsed_data['rooms']:
                        # Convert old format to new format
                        old_rooms = parsed_data['rooms']
                        new_rooms = []
                        
                        # Add rooms based on old counts
                        for room_type, count in [('Single Room', old_rooms.get('single', 0)),
                                               ('Double Room', old_rooms.get('double', 0)),
                                               ('Twin Room', old_rooms.get('twin', 0)),
                                               ('Triple Room', old_rooms.get('triple', 0))]:
                            for i in range(int(count)):
                                new_rooms.append({
                                    'room_type': room_type,
                                    'board_basis': parsed_data.get('meal_plan', 'Room Only'),
                                    'adults': 2 if room_type != 'Single Room' else 1,
                                    'children': 0,
                                    'lead_passenger': ''
                                })
                        
                        if old_rooms.get('other'):
                            new_rooms.append({
                                'room_type': old_rooms['other'],
                                'board_basis': parsed_data.get('meal_plan', 'Room Only'),
                                'adults': 2,
                                'children': 0,
                                'lead_passenger': ''
                            })
                        
                        # If no rooms, add default
                        if not new_rooms:
                            new_rooms.append({
                                'room_type': '',
                                'board_basis': 'Room Only',
                                'adults': 2,
                                'children': 0,
                                'lead_passenger': ''
                            })
                        
                        parsed_data['rooms'] = new_rooms
                        print(f"Converted old room format to new: {new_rooms}", file=sys.stderr)
                
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
    
    # Get suppliers from database for the dropdown
    from app.models.supplier import Supplier, SupplierService
    
    # Get all suppliers as base list
    all_suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    
    # Filter suppliers by their SupplierService relationships for the specific service type
    service_type_suppliers = []
    
    # Query suppliers that have services matching the service item type
    suppliers_with_service = db.session.query(Supplier).join(SupplierService).filter(
        Supplier.is_active == True,
        SupplierService.service_type == service_item.service_type
    ).order_by(Supplier.name).all()
    
    # Also include suppliers with matching main supplier_type for backward compatibility
    if service_item.service_type == 'FLIGHT':
        legacy_suppliers = [s for s in all_suppliers if s.supplier_type == 'AIRLINE']
    elif service_item.service_type == 'HOTEL':
        legacy_suppliers = [s for s in all_suppliers if s.supplier_type == 'HOTEL']
    elif service_item.service_type == 'TRANSPORT':
        legacy_suppliers = [s for s in all_suppliers if s.supplier_type == 'TRANSPORT']
    elif service_item.service_type == 'VISA':
        legacy_suppliers = [s for s in all_suppliers if s.supplier_type == 'VISA']
    elif service_item.service_type == 'INSURANCE':
        legacy_suppliers = [s for s in all_suppliers if s.supplier_type == 'INSURANCE']
    else:
        legacy_suppliers = []
    
    # Combine both lists and remove duplicates
    combined_suppliers = suppliers_with_service + legacy_suppliers
    seen_ids = set()
    service_type_suppliers = []
    for supplier in combined_suppliers:
        if supplier.id not in seen_ids:
            service_type_suppliers.append(supplier)
            seen_ids.add(supplier.id)
    
    # If no specific suppliers found, show all suppliers
    if not service_type_suppliers:
        service_type_suppliers = all_suppliers
    
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
                          confirmation_doc=confirmation_doc,
                          suppliers=service_type_suppliers,
                          all_suppliers=all_suppliers)

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
            
            # DO NOT automatically change booking status - status changes should be independent
            # booking.status = STATUS_IN_PROGRESS  # REMOVED - let users control status separately
            
            # Mark ALL service items as invoiced with the invoice details
            for item in booking.service_items:
                item.is_invoiced = True
                item.invoice_number = booking.invoice_number
                item.invoice_date = booking.invoice_date
            
            # Add invoice notes if provided
            notes = form.notes.data or request.form.get('invoice_notes', '')
            
            # Note: Invoice data is stored in the booking table as the primary source
            # The separate invoice table is only used for credit memos and special cases
            print(f"Invoice data stored in booking table: {booking.invoice_number}", file=sys.stderr)
            
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
        
        import sys
        print(f"Processing payment of ${form.amount.data} for booking #{booking.id}", file=sys.stderr)
        
        db.session.add(payment)
        
        # First commit to save the payment
        db.session.commit()
        
        # Now refresh the booking to get the updated payments relationship
        db.session.refresh(booking)
        
        # Now update payment status with the refreshed booking
        booking.update_payment_status()
        
        # Set payment date on booking if not already set
        if not booking.payment_date:
            booking.payment_date = datetime.utcnow()
        
        # Commit again to save the payment status updates
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

@booking_bp.route('/<int:booking_id>/upload_document', methods=['POST'])
def upload_document(booking_id):
    """Upload a document for a service item"""
    booking = Booking.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        service_item_id = request.form.get('service_item_id')
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')
        notes = request.form.get('notes', '')
        extracted_data = request.form.get('extracted_data', '')
        
        # Validate the service item exists and belongs to this booking
        service_item = ServiceItem.query.get_or_404(service_item_id)
        if service_item.booking_id != booking.id:
            flash('Invalid service item', 'danger')
            return redirect(url_for('booking.details', booking_id=booking.id))
        
        # Handle file upload if provided
        file = request.files.get('document_file')
        file_path = None
        
        if file and file.filename:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join('static', 'uploads', 'documents', str(booking.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # If it's a ticket, check if we should analyze it
            if document_type == 'TICKET' and not extracted_data:
                try:
                    # Process image for AI analysis if it's a supported format
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        # Read file and convert to base64
                        with open(file_path, 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        # Analyze the image with OpenAI
                        analysis_results = analyze_flight_ticket(img_data)
                        
                        # Add the analysis results to the notes field as JSON
                        if notes:
                            notes += "\n\n"
                        
                        notes += f"AI Analysis Results:\n"
                        notes += f"Flight: {analysis_results.get('flight_number', 'Unknown')}\n"
                        notes += f"Airline: {analysis_results.get('airline', 'Unknown')}\n"
                        notes += f"From: {analysis_results.get('departure_airport', 'Unknown')} ({analysis_results.get('departure_code', '')})\n"
                        notes += f"To: {analysis_results.get('arrival_airport', 'Unknown')} ({analysis_results.get('arrival_code', '')})\n"
                        notes += f"Date: {analysis_results.get('departure_date', 'Unknown')}\n"
                        notes += f"Time: {analysis_results.get('departure_time', 'Unknown')}\n"
                        
                        # Use the analyzed ticket number if available and not manually provided
                        if not document_number and analysis_results.get('ticket_numbers'):
                            document_number = analysis_results.get('ticket_numbers')[0]
                        
                        # Use the analyzed booking reference if available and not in notes
                        if analysis_results.get('booking_reference') and 'booking reference' not in notes.lower():
                            notes += f"Booking Reference: {analysis_results.get('booking_reference')}\n"
                except Exception as e:
                    flash(f'Error analyzing ticket: {str(e)}', 'warning')
                    print(f"Error in ticket analysis: {str(e)}")
        
        # Create a new document
        document = Document(
            service_item_id=service_item.id,
            document_type=document_type,
            file_path=file_path,
            document_number=document_number,
            notes=notes
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Document uploaded successfully', 'success')
    
    return redirect(url_for('booking.details', booking_id=booking.id))

@booking_bp.route('/api/analyze_ticket', methods=['POST'])
def analyze_ticket_api():
    """API endpoint for analyzing ticket images with AI"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'Invalid file'}), 400
    
    # Check if the file is an image
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({'error': 'File must be an image (JPG, JPEG, PNG)'}), 400
    
    try:
        # Read file and convert to base64
        file_data = file.read()
        img_data = base64.b64encode(file_data).decode('utf-8')
        
        # Analyze the image with OpenAI
        analysis_results = analyze_flight_ticket(img_data)
        
        return jsonify({
            'success': True,
            'results': analysis_results
        })
    except Exception as e:
        print(f"Error in API ticket analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/api/scan-hotel-voucher', methods=['POST'])
def scan_hotel_voucher():
    """API endpoint for analyzing hotel voucher images with AI"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'Invalid file'}), 400
        
        # Check if the file is an image or PDF
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            return jsonify({'error': 'File must be an image (JPG, JPEG, PNG) or PDF'}), 400
        
        # Handle different file types
        if file.filename.lower().endswith('.pdf'):
            # For PDF files, convert to images first
            import tempfile
            import os
            from pdf2image import convert_from_bytes
            
            file_data = file.read()
            
            # Convert PDF to images
            images = convert_from_bytes(file_data)
            if not images:
                return jsonify({'error': 'Could not process PDF file'}), 400
            
            # Use the first page for analysis
            import io
            img_buffer = io.BytesIO()
            images[0].save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        else:
            # For image files
            file_data = file.read()
            img_data = base64.b64encode(file_data).decode('utf-8')
        
        # Analyze with OpenAI
        from app.utils.openai_helper import analyze_hotel_voucher
        analysis_results = analyze_hotel_voucher(img_data)
        
        return jsonify({
            'success': True,
            'data': analysis_results
        })
    except Exception as e:
        print(f"Error in hotel voucher analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/booking/<int:booking_id>/add_credit_line', methods=['POST'])
def add_credit_line(booking_id):
    """Add a manual credit line to a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    try:
        credit_amount = float(request.form.get('credit_amount', 0))
        credit_reason = request.form.get('credit_reason', '')
        notes = request.form.get('notes', '')
        
        if credit_amount <= 0:
            flash('Credit amount must be greater than zero', 'danger')
            return redirect(url_for('booking.details', booking_id=booking_id))
        
        # Generate a credit memo number
        credit_memo_number = booking.generate_credit_memo_number()
        
        # Credit memo is an invoice document, not a payment
        # Payments represent actual money received - credits are invoice adjustments
        from datetime import datetime
        
        # Create invoice record for the credit memo if booking is invoiced
        if booking.invoice_number:
            from app.models.invoice import Invoice
            credit_memo = Invoice(
                booking_id=booking.id,
                invoice_number=credit_memo_number,
                invoice_date=datetime.utcnow(),
                total_amount=-credit_amount,
                notes=f"Manual Credit Line - {credit_reason}: {notes}",
                is_credit_memo=True,
                referenced_invoice=booking.invoice_number
            )
            db.session.add(credit_memo)
        
        db.session.commit()
        flash(f'Credit line of ${credit_amount:.2f} successfully added', 'success')
        
    except ValueError:
        flash('Invalid credit amount entered', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding credit line: {str(e)}', 'danger')
    
    return redirect(url_for('booking.details', booking_id=booking_id))


@booking_bp.route('/scan-flight-document', methods=['POST'])
@login_required
def scan_flight_document():
    """API endpoint to scan flight confirmation documents using AI"""
    try:
        if 'document' not in request.files:
            return jsonify({'success': False, 'error': 'No document uploaded'})
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Read file data
        file_data = file.read()
        
        # Analyze the document using OpenAI
        from app.utils.openai_helper import analyze_document
        result = analyze_document(file_data, file.filename)
        
        if result and ('segments' in result and result['segments']) or any(key in result for key in ['flight_number', 'airline']):
            return jsonify({
                'success': True, 
                'flight_data': result,
                'message': 'Document analyzed successfully'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'No flight information found in document'
            })
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error processing document: {str(e)}'
        })