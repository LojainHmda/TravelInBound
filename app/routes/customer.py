from datetime import datetime
import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, current_app, send_file
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError, OperationalError
from app.extensions import db, csrf
from app.forms.customer import CustomerForm, CustomerDocumentForm, CustomerSearchForm
from app.models.customer import Customer, CustomerDocument
from app.models.booking import Booking
from app.models.inbound import InboundRequest
from app.utils import is_valid_phone, PHONE_ERROR
from app.services.passport_scanner import PassportScanner

# Create blueprint
customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

# Ensure upload directory exists
def ensure_upload_dir(directory):
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def _apply_customer_financial_from_form(form, customer):
    """Match supplier popups: Cliq maps alias → bank_account; else use bank fields."""
    pt = (form.payment_terms.data or '').strip()
    if pt == 'Cliq':
        ca = (form.cliq_alias.data or '').strip()
        customer.bank_name = 'Cliq'
        customer.bank_account = ca or None
        customer.cliq_alias = ca or None
    else:
        customer.bank_name = (form.bank_name.data or '').strip() or None
        customer.bank_account = (form.bank_account.data or '').strip() or None
        customer.cliq_alias = None


@customer_bp.route('/')
@login_required
def list_customers():
    """Display list of customers with filtering options"""
    # Get filter parameters (Customer Type only)
    customer_type = request.args.get('customer_type', '')
    
    # Create base query
    customers_query = Customer.query
    
    # Apply filters
    if customer_type:
        customers_query = customers_query.filter(Customer.customer_type == customer_type)
    
    # Get results - order by first name, then last name
    customers = customers_query.order_by(Customer.first_name, Customer.last_name).all()
    
    # Prepare search form (used for customer type choices in the template)
    form = CustomerSearchForm()
    
    return render_template(
        'customer/list.html',
        customers=customers,
        form=form,
        customer_type=customer_type
    )

@customer_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    """Create a new customer"""
    form = CustomerForm()
    # Force set customer type choices - override any cached values
    form.customer_type.choices = [
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Direct', 'Direct'),
        ('Other', 'Other')
    ]
    # Load payment terms with all predefined + custom values for validation
    from app.forms.customer import get_customer_payment_terms_choices
    form.payment_terms.choices = get_customer_payment_terms_choices()
    form.customer_type.default = 'Direct'
    # Clear any cached formdata
    if hasattr(form.customer_type, '_formdata'):
        form.customer_type._formdata = None

    # First attempt validation
    if form.is_submitted():
        form.validate()
        # Custom values from the modal should be accepted - clear "Not a valid choice" errors
        if form.payment_terms.data:
            form.payment_terms.errors = [e for e in form.payment_terms.errors if 'not a valid choice' not in str(e).lower()]
            # Also remove from form.errors dict if it exists
            if 'payment_terms' in form.errors and not form.payment_terms.errors:
                del form.errors['payment_terms']

    if form.validate_on_submit():
        customer = Customer(
            first_name=(form.agent_name.data or '').strip(),
            last_name='',
            email=(form.email.data or '').strip(),
            phone=(form.phone.data or '').strip(),
            address=None,
            city=None,
            country=None,
            customer_type=form.customer_type.data,
            company_name=(form.contact_person.data or '').strip() or None,
            payment_terms=(form.payment_terms.data or '').strip() or None,
            tax_number=None,
            notes=None,
        )
        _apply_customer_financial_from_form(form, customer)

        try:
            db.session.add(customer)
            db.session.commit()
            
            flash(f'Customer {customer.name} created successfully', 'success')
            return redirect(url_for('customer.view_customer', customer_id=customer.id))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: customer.phone' in str(e) or 'duplicate key value violates unique constraint' in str(e) or 'uq_customer_phone' in str(e):
                form.phone.errors.append('This phone number is already registered to another customer.')
                flash('Phone number already exists. Please use a different phone number.', 'error')
            else:
                flash('An error occurred while creating the customer. Please try again.', 'error')
    
    # CRITICAL: Always ensure choices are set before rendering
    form.customer_type.choices = [
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Direct', 'Direct'),
        ('Other', 'Other')
    ]
    # Clear cached formdata to force rebuild
    if hasattr(form.customer_type, '_formdata'):
        form.customer_type._formdata = None
    # Also clear the _choices attribute if it exists
    if hasattr(form.customer_type, '_choices'):
        delattr(form.customer_type, '_choices')
    return render_template(
        'customer/edit.html', form=form, is_new=True, customer=None
    )

@customer_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    """Edit an existing customer"""
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm()
    # CRITICAL: Set choices BEFORE any form processing
    form.customer_type.choices = [
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Direct', 'Direct'),
        ('Other', 'Other')
    ]
    # Load payment terms with all predefined + custom values for validation
    from app.forms.customer import get_customer_payment_terms_choices
    form.payment_terms.choices = get_customer_payment_terms_choices()

    if request.method == 'GET':
        form.agent_name.data = customer.first_name
        form.contact_person.data = customer.company_name or ''
        form.email.data = customer.email
        form.phone.data = customer.phone
        form.customer_type.data = customer.customer_type
        form.payment_terms.data = customer.payment_terms or ''
        pt_fin = (customer.payment_terms or '').strip()
        if pt_fin == 'Cliq':
            form.bank_name.data = ''
            form.bank_account.data = ''
            alias = (
                (customer.cliq_alias or '').strip()
                or (customer.bank_account or '').strip()
            )
            form.cliq_alias.data = alias
        else:
            form.bank_name.data = customer.bank_name or ''
            form.bank_account.data = customer.bank_account or ''
            form.cliq_alias.data = ''

    # Custom values from the modal should be accepted - clear "Not a valid choice" errors
    if form.is_submitted():
        form.validate()
        if form.payment_terms.data:
            form.payment_terms.errors = [e for e in form.payment_terms.errors if 'not a valid choice' not in str(e).lower()]
            if 'payment_terms' in form.errors and not form.payment_terms.errors:
                del form.errors['payment_terms']

    if form.validate_on_submit():
        try:
            customer.first_name = (form.agent_name.data or '').strip()
            customer.company_name = (form.contact_person.data or '').strip() or None
            customer.email = (form.email.data or '').strip()
            customer.phone = (form.phone.data or '').strip()
            customer.customer_type = form.customer_type.data
            customer.payment_terms = (form.payment_terms.data or '').strip() or None
            _apply_customer_financial_from_form(form, customer)
            db.session.commit()
            
            flash(f'Customer {customer.name} updated successfully', 'success')
            return redirect(url_for('customer.view_customer', customer_id=customer.id))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: customer.phone' in str(e) or 'duplicate key value violates unique constraint' in str(e) or 'uq_customer_phone' in str(e):
                form.phone.errors.append('This phone number is already registered to another customer.')
                flash('Phone number already exists. Please use a different phone number.', 'error')
            else:
                flash('An error occurred while updating the customer. Please try again.', 'error')
    
    # CRITICAL: Always ensure choices are set before rendering
    form.customer_type.choices = [
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Direct', 'Direct'),
        ('Other', 'Other')
    ]
    # Clear cached formdata to force rebuild
    if hasattr(form.customer_type, '_formdata'):
        form.customer_type._formdata = None
    # Also clear the _choices attribute if it exists
    if hasattr(form.customer_type, '_choices'):
        delattr(form.customer_type, '_choices')
    return render_template('customer/edit.html', form=form, customer=customer, is_new=False)


@customer_bp.route('/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    """Remove customer; clear nullable FKs on bookings/inbound requests; delete document files."""
    customer_row = Customer.query.get_or_404(customer_id)
    name = customer_row.name
    cid = customer_row.id

    db.session.expunge(customer_row)

    static_root = os.path.join(current_app.root_path, 'static')
    try:
        docs = CustomerDocument.query.filter(CustomerDocument.customer_id == cid).all()
        for document in docs:
            if document.file_path:
                fp = os.path.join(static_root, document.file_path)
                if os.path.isfile(fp):
                    try:
                        os.remove(fp)
                    except OSError:
                        pass
        CustomerDocument.query.filter(CustomerDocument.customer_id == cid).delete(
            synchronize_session='fetch'
        )

        Booking.query.filter(Booking.customer_id == cid).update(
            {Booking.customer_id: None},
            synchronize_session=False,
        )
        InboundRequest.query.filter(InboundRequest.customer_id == cid).update(
            {InboundRequest.customer_id: None},
            synchronize_session=False,
        )

        db.session.execute(delete(Customer).where(Customer.id == cid))
        db.session.commit()
        flash(f'Customer {name} was removed.', 'success')
    except IntegrityError as exc:
        db.session.rollback()
        current_app.logger.warning('delete_customer integrity: %s', exc.orig or exc)
        flash(
            'Unable to delete: records in another table still reference this customer.',
            'danger',
        )
    except OperationalError as exc:
        db.session.rollback()
        err = str(exc.orig or exc).lower()
        current_app.logger.warning('delete_customer operational: %s', exc.orig or exc)
        if 'foreign' in err or 'constraint' in err:
            flash(
                'Unable to delete: the database refused because something still '
                'links to this customer (see server log).',
                'danger',
            )
        else:
            flash('Could not remove customer due to a database error.', 'danger')
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception('delete_customer')
        if current_app.debug:
            flash(
                f'Could not remove customer: {exc!s}',
                'danger',
            )
        else:
            flash(
                'Could not remove customer. Enable debug logging or check '
                'the server log for the exact error.',
                'danger',
            )
    return redirect(url_for('customer.list_customers'))


@customer_bp.route('/<int:customer_id>')
@login_required
def view_customer(customer_id):
    """View customer details"""
    customer = Customer.query.get_or_404(customer_id)
    document_form = CustomerDocumentForm()
    
    return render_template(
        'customer/view.html',
        customer=customer,
        document_form=document_form,
        now=datetime.utcnow()  # Pass current date for expiry checks
    )

@customer_bp.route('/<int:customer_id>/upload-document', methods=['POST'])
@login_required
def upload_document(customer_id):
    """Upload a document for a customer"""
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerDocumentForm()
    
    if form.validate_on_submit():
        # Process the file upload
        file = form.file.data
        if file:
            # Create unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Ensure upload directory exists
            upload_dir = os.path.join(current_app.root_path, 'static/uploads/customer_documents')
            ensure_upload_dir(upload_dir)
            
            # Save the file
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            
            # Create relative path for storage
            relative_path = f'uploads/customer_documents/{unique_filename}'
            
            # Create document record
            document = CustomerDocument(
                customer_id=customer.id,
                document_type=form.document_type.data,
                document_number=form.document_number.data,
                issue_date=form.issue_date.data,
                expiry_date=form.expiry_date.data,
                issuing_country=form.issuing_country.data,
                notes=form.notes.data,
                file_path=relative_path,
                upload_date=datetime.utcnow()
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash(f'Document uploaded successfully', 'success')
        else:
            flash('No file uploaded', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('customer.view_customer', customer_id=customer.id))

@customer_bp.route('/<int:customer_id>/delete-document/<int:document_id>', methods=['POST'])
@login_required
def delete_document(customer_id, document_id):
    """Delete a customer document"""
    document = CustomerDocument.query.get_or_404(document_id)
    
    # Check if document belongs to the specified customer
    if document.customer_id != customer_id:
        flash('Document not found', 'danger')
        return redirect(url_for('customer.view_customer', customer_id=customer_id))
    
    # Get the file path
    file_path = os.path.join(current_app.root_path, 'static', document.file_path)
    
    # Delete the file if it exists
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete the database record
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted successfully', 'success')
    return redirect(url_for('customer.view_customer', customer_id=customer_id))

@customer_bp.route('/<int:customer_id>/document/<int:document_id>')
@login_required
def view_document(customer_id, document_id):
    """Serve a customer document file"""
    document = CustomerDocument.query.get_or_404(document_id)
    
    # Check if document belongs to the specified customer
    if document.customer_id != customer_id:
        flash('Document not found', 'danger')
        return redirect(url_for('customer.view_customer', customer_id=customer_id))
    
    # Get the full file path
    file_path = os.path.join(current_app.root_path, 'static', document.file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        flash('Document file not found', 'danger')
        return redirect(url_for('customer.view_customer', customer_id=customer_id))
    
    # Serve the file
    return send_file(file_path)

@customer_bp.route('/api/list')

def api_list_customers():
    """API endpoint to return customers as JSON"""
    try:
        customers = Customer.query.order_by(Customer.first_name, Customer.last_name).all()
        
        customers_list = [{
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'phone': c.phone,
            'customer_type': c.customer_type,
            'company_name': c.company_name,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'updated_at': c.updated_at.isoformat() if c.updated_at else None,
            'booking_count': len(c.bookings) if hasattr(c, 'bookings') and c.bookings else 0
        } for c in customers]
        
        return jsonify(customers_list)
    except Exception as e:
        print(f"Error in api_list_customers: {e}")
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/api/scan-passport', methods=['POST'])
def scan_passport():
    """API endpoint to extract customer data from passport image"""
    
    try:
        print(f"DEBUG: Scanning passport, request files: {list(request.files.keys())}")
        
        if 'passport_image' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No passport image provided'
            }), 400
        
        file = request.files['passport_image']
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No file selected'
            }), 400
        
        # Read the file data
        file_content = file.read()
        if not file_content:
            return jsonify({
                'success': False, 
                'error': 'Empty file uploaded'
            }), 400
        
        print(f"DEBUG: File size: {len(file_content)} bytes")
        
        # Initialize passport scanner and extract data with raw file data
        scanner = PassportScanner()
        extracted_data = scanner.extract_passport_data(file_content, file.filename or '')
        
        print(f"DEBUG: Extracted data: {extracted_data}")
        
        if extracted_data and any(v for v in extracted_data.values() if v):
            return jsonify({
                'success': True,
                'data': extracted_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unable to extract passport data from the image'
            })
            
    except Exception as e:
        print(f"DEBUG: Exception in scan_passport: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error processing passport image: {str(e)}'
        }), 500

@customer_bp.route('/api/search')

def api_search_customers():
    """API endpoint to search customers with filters"""
    # Get search parameters
    query = request.args.get('query', '')
    customer_type = request.args.get('customer_type', '')
    
    # Create base query
    customers_query = Customer.query
    
    # Apply filters
    if query:
        customers_query = customers_query.filter(
            db.or_(
                Customer.first_name.ilike(f'%{query}%'),
                Customer.last_name.ilike(f'%{query}%'),
                Customer.email.ilike(f'%{query}%'),
                Customer.phone.ilike(f'%{query}%'),
                Customer.company_name.ilike(f'%{query}%')
            )
        )
    
    if customer_type:
        customers_query = customers_query.filter(Customer.customer_type == customer_type)
    
    # Limit results
    limit = request.args.get('limit', 10, type=int)
    customers = customers_query.order_by(Customer.first_name, Customer.last_name).limit(limit).all()
    
    # Format for select2
    results = [{
        'id': str(c.id),
        'text': f"{c.name} ({c.email})",
        'name': c.name,
        'email': c.email,
        'phone': c.phone,
        'customer_type': c.customer_type,
        'company_name': c.company_name or ''
    } for c in customers]
    
    return jsonify({'results': results})

@customer_bp.route('/api/create', methods=['POST'])
@csrf.exempt
def api_create_customer():
    """API endpoint to create a new customer via AJAX"""
    data = request.json
    
    # Validate required fields (email is now optional)
    if not data or not data.get('first_name'):
        return jsonify({
            'success': False,
            'error': 'First name is required'
        }), 400
    
    # Check if customer with this email already exists (only if email provided)
    if data.get('email'):
        existing_customer = Customer.query.filter_by(email=data.get('email')).first()
        if existing_customer:
            return jsonify({
                'success': False,
                'error': 'A customer with this email already exists',
                'customer': {
                    'id': existing_customer.id,
                    'name': existing_customer.name,
                    'email': existing_customer.email
                }
            }), 400
    
    # Validate phone format
    if data.get('phone') and not is_valid_phone(data.get('phone')):
        return jsonify({'success': False, 'error': PHONE_ERROR}), 400

    # Check if customer with this phone already exists (only if phone provided)
    if data.get('phone'):
        existing_phone = Customer.query.filter_by(phone=data.get('phone')).first()
        if existing_phone:
            return jsonify({
                'success': False,
                'error': 'A customer with this phone number already exists'
            }), 400
    
    # Create a new customer
    try:
        customer = Customer(
            first_name=data.get('first_name'),
            last_name=data.get('last_name', ''),
            email=data.get('email'),
            phone=data.get('phone'),
            customer_type=data.get('customer_type', 'Direct'),
            company_name=data.get('company_name', ''),
            tax_number=data.get('tax_number', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            country=data.get('country', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Customer created successfully',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error creating customer: {str(e)}'
        }), 500