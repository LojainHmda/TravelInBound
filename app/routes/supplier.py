from datetime import datetime, date
import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, jsonify, current_app
)
from werkzeug.utils import secure_filename
from app import db
from app.forms.supplier import SupplierForm, SupplierPaymentForm, SupplierStatementForm
from app.models.supplier import Supplier, SupplierService, SupplierPayment
from app.models.service import ServiceConfirmation
from sqlalchemy import func, desc

# Create blueprint
supplier_bp = Blueprint('supplier', __name__, url_prefix='/suppliers')

# Ensure upload directory exists
def ensure_upload_dir(directory):
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

@supplier_bp.route('/')
def list_suppliers():
    """Display list of suppliers with filtering options"""
    # Get search parameters
    query = request.args.get('query', '')
    supplier_type = request.args.get('supplier_type', '')
    country = request.args.get('country', '')
    
    # Create base query
    suppliers_query = Supplier.query
    
    # Apply filters
    if query:
        suppliers_query = suppliers_query.filter(
            Supplier.name.ilike(f'%{query}%') |
            Supplier.email.ilike(f'%{query}%') |
            Supplier.code.ilike(f'%{query}%') |
            Supplier.website.ilike(f'%{query}%')
        )
    
    if supplier_type:
        suppliers_query = suppliers_query.filter(Supplier.supplier_type == supplier_type)
    
    if country:
        suppliers_query = suppliers_query.filter(Supplier.country == country)
    
    # Get results with unpaid balance information
    suppliers = suppliers_query.order_by(Supplier.name).all()
    
    # Calculate unpaid balances
    for supplier in suppliers:
        supplier.unpaid_balance = supplier.get_unpaid_balance()
    
    # Prepare search form with country options
    form = SupplierForm()
    
    # Get unique countries for dropdown
    countries = [(c.country, c.country) for c in Supplier.query.filter(
        Supplier.country.isnot(None)
    ).with_entities(Supplier.country).distinct().order_by(Supplier.country)]
    
    # Add 'All Countries' option at the start
    form.country.choices = [('', 'All Countries')] + countries
    
    return render_template(
        'supplier/list.html',
        suppliers=suppliers,
        form=form,
        query=query,
        supplier_type=supplier_type,
        country=country
    )

@supplier_bp.route('/new', methods=['GET', 'POST'])
def new_supplier():
    """Create a new supplier"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            code=form.code.data,
            supplier_type=form.supplier_type.data,
            email=form.email.data,
            phone=form.phone.data,
            website=form.website.data,
            contact_person=form.contact_person.data,
            address=form.address.data,
            city=form.city.data,
            country=form.country.data,
            payment_terms=form.payment_terms.data,
            default_currency=form.default_currency.data,
            bank_name=form.bank_name.data,
            bank_account=form.bank_account.data,
            tax_number=form.tax_number.data,
            notes=form.notes.data
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash(f'Supplier {supplier.name} created successfully', 'success')
        return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
    
    return render_template('supplier/edit.html', form=form, is_new=True)

@supplier_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    """Edit an existing supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        
        flash(f'Supplier {supplier.name} updated successfully', 'success')
        return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
    
    return render_template('supplier/edit.html', form=form, supplier=supplier, is_new=False)

@supplier_bp.route('/<int:supplier_id>')
def view_supplier(supplier_id):
    """View supplier details"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Get active service confirmations for this supplier
    confirmations = ServiceConfirmation.query.filter_by(
        supplier_id=supplier.id
    ).order_by(ServiceConfirmation.created_at.desc()).limit(5).all()
    
    # Get recent payments
    payments = SupplierPayment.query.filter_by(
        supplier_id=supplier.id
    ).order_by(SupplierPayment.payment_date.desc()).limit(5).all()
    
    # Initialize payment form
    payment_form = SupplierPaymentForm()
    payment_form.supplier_id.data = supplier.id
    
    # Get unpaid service confirmations for dropdown
    unpaid_confirmations = [(str(sc.id), f"{sc.confirmation_reference} - {sc.service_item.service_type} - ${sc.cost_amount:.2f}") 
                          for sc in ServiceConfirmation.query.filter_by(
                              supplier_id=supplier.id,
                              is_paid=False
                          ).order_by(ServiceConfirmation.created_at).all()]
    
    # Add general payment option
    payment_form.service_confirmation_id.choices = [('', 'General Payment')] + unpaid_confirmations
    
    return render_template(
        'supplier/view.html',
        supplier=supplier,
        confirmations=confirmations,
        payments=payments,
        payment_form=payment_form,
        unpaid_balance=supplier.get_unpaid_balance()
    )

@supplier_bp.route('/<int:supplier_id>/add-payment', methods=['POST'])
def add_payment(supplier_id):
    """Add a payment to a supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierPaymentForm()
    
    # Get unpaid service confirmations for dropdown
    unpaid_confirmations = [(str(sc.id), f"{sc.confirmation_reference} - {sc.service_item.service_type} - ${sc.cost_amount:.2f}") 
                          for sc in ServiceConfirmation.query.filter_by(
                              supplier_id=supplier.id,
                              is_paid=False
                          ).order_by(ServiceConfirmation.created_at).all()]
    
    # Add general payment option
    form.service_confirmation_id.choices = [('', 'General Payment')] + unpaid_confirmations
    
    if form.validate_on_submit():
        payment = SupplierPayment(
            supplier_id=supplier.id,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            payment_reference=form.payment_reference.data,
            payment_method=form.payment_method.data,
            notes=form.notes.data
        )
        
        # If specific service confirmation, link and mark as paid if full amount
        if form.service_confirmation_id.data:
            confirmation_id = int(form.service_confirmation_id.data)
            payment.service_confirmation_id = confirmation_id
            
            # Check if this payment covers the confirmation amount
            confirmation = ServiceConfirmation.query.get(confirmation_id)
            if confirmation and payment.amount >= confirmation.cost_amount:
                confirmation.is_paid = True
                confirmation.payment_date = form.payment_date.data
        
        db.session.add(payment)
        db.session.commit()
        
        flash(f'Payment of ${payment.amount:.2f} recorded successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))

@supplier_bp.route('/statements')
def supplier_statements():
    """Page to generate supplier statements"""
    form = SupplierStatementForm()
    
    # Get suppliers for dropdown
    suppliers = [(str(s.id), s.name) for s in Supplier.query.order_by(Supplier.name).all()]
    form.supplier_id.choices = suppliers
    
    return render_template('supplier/statements_index.html', form=form)

@supplier_bp.route('/generate-statement', methods=['POST'])
def generate_statement():
    """Generate a statement for a supplier"""
    form = SupplierStatementForm()
    
    # Get suppliers for dropdown
    suppliers = [(str(s.id), s.name) for s in Supplier.query.order_by(Supplier.name).all()]
    form.supplier_id.choices = suppliers
    
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data
        
        # Build query parameters for the supplier_statement view
        from_date = form.from_date.data.strftime('%Y-%m-%d') if form.from_date.data else ''
        to_date = form.to_date.data.strftime('%Y-%m-%d') if form.to_date.data else ''
        status = form.status.data
        
        # Debug log
        import sys
        print(f"Redirecting to supplier statement for supplier_id={supplier_id}, from={from_date}, to={to_date}, status={status}", file=sys.stderr)
        
        # Redirect to the supplier statement view with filters
        return redirect(url_for(
            'supplier.supplier_statement', 
            supplier_id=supplier_id,
            from_date=from_date,
            to_date=to_date,
            status=status
        ))
    
    # If form validation fails, go back to the statements index page
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'danger')
            
    return redirect(url_for('supplier.supplier_statements'))

@supplier_bp.route('/statement/<int:supplier_id>')
def supplier_statement(supplier_id):
    """View statement for a specific supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Get query parameters
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    status = request.args.get('status', 'ALL')
    
    # Parse dates
    from datetime import datetime, date
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date() if from_date_str else None
    except (ValueError, TypeError):
        from_date = date.today().replace(day=1)  # First day of current month
        
    try:
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date() if to_date_str else None
    except (ValueError, TypeError):
        to_date = date.today()
    
    # Query for service confirmations
    from models import Document
    
    # Find all confirmation documents for this supplier
    confirmations = []
    
    # Get all documents of type CONFIRMATION
    confirmation_docs = Document.query.filter_by(document_type='CONFIRMATION').all()
    
    for doc in confirmation_docs:
        try:
            if doc.notes:
                # Parse the JSON data
                import json
                data = json.loads(doc.notes)
                
                # Check if this document is for our supplier
                if data.get('supplier_id') == supplier.id:
                    # Create a confirmation object from document data
                    confirmation = {
                        'id': doc.id,
                        'confirmation_reference': doc.document_number,
                        'service_item': doc.service_item,
                        'confirmation_date': doc.upload_date,
                        'cost_amount': data.get('cost_amount', 0.0),
                        'cost_currency': data.get('cost_currency', 'USD'),
                        'payment_due_date': data.get('payment_due_date'),
                        'is_paid': data.get('is_paid', False)
                    }
                    
                    # Parse payment_due_date if it's a string
                    if isinstance(confirmation['payment_due_date'], str) and confirmation['payment_due_date']:
                        try:
                            confirmation['payment_due_date'] = datetime.strptime(
                                confirmation['payment_due_date'], '%Y-%m-%d'
                            ).date()
                        except ValueError:
                            confirmation['payment_due_date'] = None
                    
                    # Apply date filters
                    if from_date and doc.upload_date.date() < from_date:
                        continue
                    if to_date and doc.upload_date.date() > to_date:
                        continue
                    
                    # Apply status filter
                    if status == 'PAID' and not confirmation['is_paid']:
                        continue
                    if status == 'UNPAID' and confirmation['is_paid']:
                        continue
                    
                    confirmations.append(confirmation)
        except Exception as e:
            # Log error but continue processing other documents
            import sys
            print(f"Error processing document {doc.id}: {str(e)}", file=sys.stderr)
            continue
    
    # Calculate totals
    total_amount = sum(c['cost_amount'] for c in confirmations)
    paid_amount = sum(c['cost_amount'] for c in confirmations if c['is_paid'])
    unpaid_amount = total_amount - paid_amount
    
    # Get today's date for comparing overdue payments
    today = date.today()
    
    # Render the statement
    return render_template(
        'supplier/statement.html',
        supplier=supplier,
        confirmations=confirmations,
        from_date=from_date,
        to_date=to_date,
        status=status,
        total_amount=total_amount,
        paid_amount=paid_amount,
        unpaid_amount=unpaid_amount,
        today=today
    )

@supplier_bp.route('/api/list')
def api_list_suppliers():
    """API endpoint to return suppliers as JSON"""
    suppliers = Supplier.query.order_by(Supplier.name).all()
    
    suppliers_list = [{
        'id': s.id,
        'name': s.name,
        'code': s.code,
        'email': s.email,
        'supplier_type': s.supplier_type
    } for s in suppliers]
    
    return jsonify(suppliers_list)