import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.customer import Customer, CustomerDocument
from app.models.booking import Booking
from app.forms.customer import CustomerForm, CustomerDocumentForm, CustomerSearchForm

# Create a blueprint for customer-related routes
customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

# Helper function to handle file uploads
def save_file(file, directory='uploads/customer_documents'):
    """Save an uploaded file to the specified directory and return the file path"""
    if not file:
        return None
        
    # Create the directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'static', directory)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(directory, unique_filename)
    
    # Save the file
    file.save(os.path.join(current_app.root_path, 'static', file_path))
    
    return file_path

@customer_bp.route('/')
def list_customers():
    """Display a list of customers"""
    form = CustomerSearchForm()
    
    # Get search parameters
    query = request.args.get('query', '')
    customer_type = request.args.get('customer_type', '')
    country = request.args.get('country', '')
    
    # Base query
    customers_query = Customer.query
    
    # Apply filters
    if query:
        customers_query = customers_query.filter(Customer.name.ilike(f'%{query}%') | 
                                              Customer.email.ilike(f'%{query}%') |
                                              Customer.phone.ilike(f'%{query}%'))
    
    if customer_type:
        customers_query = customers_query.filter(Customer.customer_type == customer_type)
    
    if country:
        customers_query = customers_query.filter(Customer.country == country)
    
    # Get all unique countries for the dropdown
    countries = db.session.query(Customer.country).distinct().order_by(Customer.country).all()
    form.country.choices = [('', 'All Countries')] + [(c[0], c[0]) for c in countries if c[0]]
    
    # Get customers
    customers = customers_query.order_by(Customer.name).all()
    
    return render_template('customer/list.html', 
                          customers=customers,
                          form=form,
                          query=query,
                          customer_type=customer_type,
                          country=country)

@customer_bp.route('/new', methods=['GET', 'POST'])
def new_customer():
    """Create a new customer"""
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
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
        
        flash(f'Customer {customer.name} has been created', 'success')
        return redirect(url_for('customer.view_customer', customer_id=customer.id))
    
    return render_template('customer/edit.html', form=form, title='New Customer')

@customer_bp.route('/<int:customer_id>', methods=['GET'])
def view_customer(customer_id):
    """View customer details"""
    customer = Customer.query.get_or_404(customer_id)
    
    # Get customer's documents
    documents = CustomerDocument.query.filter_by(customer_id=customer_id).order_by(CustomerDocument.upload_date.desc()).all()
    
    # Get bookings related to this customer
    bookings = Booking.query.filter_by(user_id=customer_id).order_by(Booking.created_at.desc()).all()
    
    # Prepare document upload form
    document_form = CustomerDocumentForm()
    
    return render_template('customer/view.html',
                          customer=customer,
                          documents=documents,
                          bookings=bookings,
                          document_form=document_form)

@customer_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    """Edit an existing customer"""
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    
    if form.validate_on_submit():
        form.populate_obj(customer)
        db.session.commit()
        
        flash(f'Customer {customer.name} has been updated', 'success')
        return redirect(url_for('customer.view_customer', customer_id=customer.id))
    
    return render_template('customer/edit.html', form=form, customer=customer, title='Edit Customer')

@customer_bp.route('/<int:customer_id>/documents/upload', methods=['POST'])
def upload_document(customer_id):
    """Upload a document for a customer"""
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerDocumentForm()
    
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_file(form.file.data)
        
        if file_path:
            # Create the document record
            document = CustomerDocument(
                customer_id=customer_id,
                document_type=form.document_type.data,
                document_number=form.document_number.data,
                issue_date=form.issue_date.data,
                expiry_date=form.expiry_date.data,
                issuing_country=form.issuing_country.data,
                file_path=file_path,
                notes=form.notes.data,
                upload_date=datetime.utcnow()
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash(f'Document {document.document_type} has been uploaded', 'success')
        else:
            flash('Error uploading document', 'danger')
    else:
        for field, errors in form.errors.items():
            flash(f'{field}: {", ".join(errors)}', 'danger')
    
    return redirect(url_for('customer.view_customer', customer_id=customer_id))

@customer_bp.route('/api/list', methods=['GET'])
def customer_api_list():
    """API endpoint to get customer list for dynamic dropdowns"""
    customers = Customer.query.order_by(Customer.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'email': c.email} for c in customers])