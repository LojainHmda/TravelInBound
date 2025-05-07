import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.supplier import Supplier, SupplierDocument
from app.models.service import ServiceConfirmation
from app.forms.supplier import SupplierForm, SupplierDocumentForm, SupplierSearchForm
from app.forms.confirmation import SupplierPaymentForm, SupplierStatementForm
from sqlalchemy import func

# Create a blueprint for supplier-related routes
supplier_bp = Blueprint('supplier', __name__, url_prefix='/suppliers')

# Helper function to handle file uploads
def save_file(file, directory='uploads/supplier_documents'):
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

@supplier_bp.route('/')
def list_suppliers():
    """Display a list of suppliers"""
    form = SupplierSearchForm()
    
    # Get search parameters
    query = request.args.get('query', '')
    country = request.args.get('country', '')
    service_type = request.args.get('service_type', '')
    
    # Base query
    suppliers_query = Supplier.query
    
    # Apply filters
    if query:
        suppliers_query = suppliers_query.filter(Supplier.name.ilike(f'%{query}%') | 
                                               Supplier.code.ilike(f'%{query}%') |
                                               Supplier.contact_person.ilike(f'%{query}%') |
                                               Supplier.email.ilike(f'%{query}%'))
    
    if country:
        suppliers_query = suppliers_query.filter(Supplier.country == country)
    
    # If service_type is specified, filter by suppliers that provide that service
    if service_type:
        suppliers_query = suppliers_query.join(ServiceConfirmation).filter(
            ServiceConfirmation.service_item.has(service_type=service_type)
        ).distinct()
    
    # Get all unique countries for the dropdown
    countries = db.session.query(Supplier.country).distinct().order_by(Supplier.country).all()
    form.country.choices = [('', 'All Countries')] + [(c[0], c[0]) for c in countries if c[0]]
    
    # Get suppliers and their balances
    suppliers = suppliers_query.order_by(Supplier.name).all()
    
    return render_template('supplier/list.html', 
                          suppliers=suppliers,
                          form=form,
                          query=query,
                          country=country,
                          service_type=service_type)

@supplier_bp.route('/new', methods=['GET', 'POST'])
def new_supplier():
    """Create a new supplier"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            code=form.code.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            country=form.country.data,
            website=form.website.data,
            payment_terms=form.payment_terms.data,
            account_number=form.account_number.data,
            tax_number=form.tax_number.data,
            notes=form.notes.data
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash(f'Supplier {supplier.name} has been created', 'success')
        return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
    
    return render_template('supplier/edit.html', form=form, title='New Supplier')

@supplier_bp.route('/<int:supplier_id>', methods=['GET'])
def view_supplier(supplier_id):
    """View supplier details"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Get supplier's documents
    documents = SupplierDocument.query.filter_by(supplier_id=supplier_id).order_by(SupplierDocument.upload_date.desc()).all()
    
    # Get service confirmations related to this supplier
    confirmations = (ServiceConfirmation.query
                    .filter_by(supplier_id=supplier_id)
                    .order_by(ServiceConfirmation.confirmation_date.desc())
                    .all())
    
    # Calculate unpaid balance
    unpaid_balance = supplier.get_balance()
    
    # Prepare document upload form
    document_form = SupplierDocumentForm()
    
    # Prepare statement form
    statement_form = SupplierStatementForm()
    statement_form.supplier_id.choices = [(supplier.id, supplier.name)]
    statement_form.supplier_id.default = supplier.id
    
    # Prepare payment form
    payment_form = SupplierPaymentForm()
    payment_form.supplier_id.choices = [(supplier.id, supplier.name)]
    payment_form.supplier_id.default = supplier.id
    
    # Get list of unpaid confirmations for payment form
    unpaid_confirmations = (ServiceConfirmation.query
                          .filter_by(supplier_id=supplier_id, is_paid=False)
                          .order_by(ServiceConfirmation.confirmation_date.desc())
                          .all())
    
    payment_form.service_confirmation_id.choices = [('', 'General Payment')] + [
        (c.id, f'{c.confirmation_reference} - {c.service_item.service_type} ({c.cost_amount} {c.cost_currency})')
        for c in unpaid_confirmations
    ]
    
    return render_template('supplier/view.html',
                          supplier=supplier,
                          documents=documents,
                          confirmations=confirmations,
                          unpaid_balance=unpaid_balance,
                          document_form=document_form,
                          payment_form=payment_form,
                          statement_form=statement_form)

@supplier_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    """Edit an existing supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        
        flash(f'Supplier {supplier.name} has been updated', 'success')
        return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
    
    return render_template('supplier/edit.html', form=form, supplier=supplier, title='Edit Supplier')

@supplier_bp.route('/<int:supplier_id>/documents/upload', methods=['POST'])
def upload_document(supplier_id):
    """Upload a document for a supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierDocumentForm()
    
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_file(form.file.data)
        
        if file_path:
            # Create the document record
            document = SupplierDocument(
                supplier_id=supplier_id,
                document_type=form.document_type.data,
                document_number=form.document_number.data,
                issue_date=form.issue_date.data,
                expiry_date=form.expiry_date.data,
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
    
    return redirect(url_for('supplier.view_supplier', supplier_id=supplier_id))

@supplier_bp.route('/<int:supplier_id>/statement', methods=['GET', 'POST'])
def supplier_statement(supplier_id):
    """Generate a statement of account for a supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierStatementForm()
    form.supplier_id.choices = [(supplier.id, supplier.name)]
    form.supplier_id.default = supplier.id
    
    # Default date range is current month
    from_date = request.form.get('from_date') or request.args.get('from_date')
    to_date = request.form.get('to_date') or request.args.get('to_date')
    status = request.form.get('status') or request.args.get('status', 'ALL')
    
    # Get confirmation records
    query = ServiceConfirmation.query.filter(ServiceConfirmation.supplier_id == supplier_id)
    
    if from_date:
        query = query.filter(ServiceConfirmation.confirmation_date >= from_date)
    
    if to_date:
        query = query.filter(ServiceConfirmation.confirmation_date <= to_date)
    
    if status == 'PAID':
        query = query.filter(ServiceConfirmation.is_paid == True)
    elif status == 'UNPAID':
        query = query.filter(ServiceConfirmation.is_paid == False)
    
    confirmations = query.order_by(ServiceConfirmation.confirmation_date).all()
    
    # Calculate totals
    total_amount = sum(c.cost_amount for c in confirmations)
    paid_amount = sum(c.cost_amount for c in confirmations if c.is_paid)
    unpaid_amount = sum(c.cost_amount for c in confirmations if not c.is_paid)
    
    return render_template('supplier/statement.html',
                          supplier=supplier,
                          confirmations=confirmations,
                          form=form,
                          from_date=from_date,
                          to_date=to_date,
                          status=status,
                          total_amount=total_amount,
                          paid_amount=paid_amount,
                          unpaid_amount=unpaid_amount)

@supplier_bp.route('/<int:supplier_id>/payment', methods=['POST'])
def record_payment(supplier_id):
    """Record a payment to a supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierPaymentForm()
    
    # Set up form choices
    form.supplier_id.choices = [(supplier.id, supplier.name)]
    
    unpaid_confirmations = (ServiceConfirmation.query
                          .filter_by(supplier_id=supplier_id, is_paid=False)
                          .order_by(ServiceConfirmation.confirmation_date.desc())
                          .all())
    
    form.service_confirmation_id.choices = [('', 'General Payment')] + [
        (c.id, f'{c.confirmation_reference} - {c.service_item.service_type} ({c.cost_amount} {c.cost_currency})')
        for c in unpaid_confirmations
    ]
    
    if form.validate_on_submit():
        # If a specific confirmation was selected, mark it as paid
        if form.service_confirmation_id.data:
            confirmation = ServiceConfirmation.query.get(form.service_confirmation_id.data)
            if confirmation:
                confirmation.is_paid = True
                confirmation.payment_date = form.payment_date.data
                confirmation.payment_reference = form.payment_reference.data
                db.session.commit()
                
                flash(f'Payment of {confirmation.cost_amount} {confirmation.cost_currency} recorded for {confirmation.confirmation_reference}', 'success')
        else:
            # Record general payment (not tied to a specific confirmation)
            flash(f'General payment of {form.amount.data} recorded', 'success')
    else:
        for field, errors in form.errors.items():
            flash(f'{field}: {", ".join(errors)}', 'danger')
    
    return redirect(url_for('supplier.view_supplier', supplier_id=supplier_id))

@supplier_bp.route('/api/list', methods=['GET'])
def supplier_api_list():
    """API endpoint to get supplier list for dynamic dropdowns"""
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify([{'id': s.id, 'name': s.name, 'code': s.code} for s in suppliers])