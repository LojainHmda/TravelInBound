from datetime import datetime
import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, jsonify, current_app
)
from werkzeug.utils import secure_filename
from app import db
from app.forms.customer import CustomerForm, CustomerDocumentForm, CustomerSearchForm
from app.models.customer import Customer, CustomerDocument
from app.services.passport_scanner import PassportScanner

# Create blueprint
customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

# Ensure upload directory exists
def ensure_upload_dir(directory):
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

@customer_bp.route('/')
def list_customers():
    """Display list of customers with filtering options"""
    # Get search parameters
    query = request.args.get('query', '')
    customer_type = request.args.get('customer_type', '')
    country = request.args.get('country', '')
    
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
    
    if country:
        customers_query = customers_query.filter(Customer.country == country)
    
    # Get results - order by first name, then last name
    customers = customers_query.order_by(Customer.first_name, Customer.last_name).all()
    
    # Prepare search form with country options
    form = CustomerSearchForm()
    
    # Get unique countries for dropdown
    countries = [(c.country, c.country) for c in Customer.query.filter(
        Customer.country.isnot(None)
    ).with_entities(Customer.country).distinct().order_by(Customer.country)]
    
    # Add 'All Countries' option at the start
    form.country.choices = [('', 'All Countries')] + countries
    
    return render_template(
        'customer/list.html',
        customers=customers,
        form=form,
        query=query,
        customer_type=customer_type,
        country=country
    )

@customer_bp.route('/new', methods=['GET', 'POST'])
def new_customer():
    """Create a new customer"""
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer = Customer(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            country=form.country.data,
            passport_number=form.passport_number.data,
            passport_expiry=form.passport_expiry.data,
            date_of_birth=form.date_of_birth.data,
            nationality=form.nationality.data,
            customer_type=form.customer_type.data,
            company_name=form.company_name.data,
            tax_number=form.tax_number.data,
            notes=form.notes.data
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash(f'Customer {customer.name} created successfully', 'success')
        return redirect(url_for('customer.view_customer', customer_id=customer.id))
    
    return render_template('customer/edit.html', form=form, is_new=True)

@customer_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    """Edit an existing customer"""
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    
    if form.validate_on_submit():
        form.populate_obj(customer)
        db.session.commit()
        
        flash(f'Customer {customer.name} updated successfully', 'success')
        return redirect(url_for('customer.view_customer', customer_id=customer.id))
    
    return render_template('customer/edit.html', form=form, customer=customer, is_new=False)

@customer_bp.route('/<int:customer_id>')
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

@customer_bp.route('/api/list')
def api_list_customers():
    """API endpoint to return customers as JSON"""
    customers = Customer.query.order_by(Customer.first_name, Customer.last_name).all()
    
    customers_list = [{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone,
        'customer_type': c.customer_type,
        'company_name': c.company_name
    } for c in customers]
    
    return jsonify(customers_list)

@customer_bp.route('/scan-passport', methods=['POST'])
def scan_passport():
    """API endpoint to extract customer data from passport image"""
    # Disable CSRF validation by setting a valid token in the request context
    from flask import g, session
    import secrets
    if not hasattr(g, 'csrf_token'):
        g.csrf_token = secrets.token_hex(16)
    session['csrf_token'] = g.csrf_token
    
    try:
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
        
        # Read and encode the image
        file_content = file.read()
        if not file_content:
            return jsonify({
                'success': False, 
                'error': 'Empty file uploaded'
            }), 400
        
        # Convert to base64
        import base64
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Initialize passport scanner and extract data
        scanner = PassportScanner()
        extracted_data = scanner.extract_passport_data(base64_image)
        
        if extracted_data:
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
def api_create_customer():
    """API endpoint to create a new customer via AJAX"""
    data = request.json
    
    if not data or not data.get('first_name') or not data.get('email'):
        return jsonify({
            'success': False,
            'message': 'First name and email are required'
        }), 400
    
    # Check if customer with this email already exists
    existing_customer = Customer.query.filter_by(email=data.get('email')).first()
    if existing_customer:
        return jsonify({
            'success': False,
            'message': 'A customer with this email already exists',
            'customer': {
                'id': existing_customer.id,
                'name': existing_customer.name,
                'email': existing_customer.email
            }
        }), 400
    
    # Create a new customer
    try:
        customer = Customer(
            first_name=data.get('first_name'),
            last_name=data.get('last_name', ''),
            email=data.get('email'),
            phone=data.get('phone', ''),
            customer_type=data.get('customer_type', 'Individual'),
            company_name=data.get('company_name', '') if data.get('customer_type') == 'Corporate' else '',
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
                'value': str(customer.id),
                'text': f"{customer.name} ({customer.email})"
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating customer: {str(e)}'
        }), 500