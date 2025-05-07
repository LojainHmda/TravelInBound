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
    
    return render_template('supplier/statement.html', form=form)

@supplier_bp.route('/generate-statement', methods=['POST'])
def generate_statement():
    """Generate a statement for a supplier"""
    form = SupplierStatementForm()
    
    # Get suppliers for dropdown
    suppliers = [(str(s.id), s.name) for s in Supplier.query.order_by(Supplier.name).all()]
    form.supplier_id.choices = suppliers
    
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data
        supplier = Supplier.query.get_or_404(supplier_id)
        
        from_date = form.from_date.data or date(1900, 1, 1)
        to_date = form.to_date.data or date.today()
        status = form.status.data
        
        # Query service confirmations
        confirmations_query = ServiceConfirmation.query.filter_by(
            supplier_id=supplier_id
        ).filter(
            ServiceConfirmation.created_at.between(from_date, to_date)
        )
        
        # Apply status filter
        if status == 'PAID':
            confirmations_query = confirmations_query.filter_by(is_paid=True)
        elif status == 'UNPAID':
            confirmations_query = confirmations_query.filter_by(is_paid=False)
        
        confirmations = confirmations_query.order_by(ServiceConfirmation.created_at).all()
        
        # Query payments
        payments_query = SupplierPayment.query.filter_by(
            supplier_id=supplier_id
        ).filter(
            SupplierPayment.payment_date.between(from_date, to_date)
        )
        
        payments = payments_query.order_by(SupplierPayment.payment_date).all()
        
        # Calculate totals
        total_owed = sum(c.cost_amount for c in confirmations)
        total_paid = sum(p.amount for p in payments)
        balance = total_owed - total_paid
        
        # Get unpaid confirmations for dropdown
        unpaid_confirmations = [(str(sc.id), f"{sc.confirmation_reference} - {sc.service_item.service_type} - ${sc.cost_amount:.2f}") 
                              for sc in ServiceConfirmation.query.filter_by(
                                  supplier_id=supplier_id,
                                  is_paid=False
                              ).order_by(ServiceConfirmation.created_at).all()]
        
        # Initialize payment form
        payment_form = SupplierPaymentForm()
        payment_form.supplier_id.data = supplier_id
        
        # Add general payment option
        payment_form.service_confirmation_id.choices = [('', 'General Payment')] + unpaid_confirmations
        
        return render_template(
            'supplier/statement_result.html',
            supplier=supplier,
            confirmations=confirmations,
            payments=payments,
            from_date=from_date,
            to_date=to_date,
            status=status,
            total_owed=total_owed,
            total_paid=total_paid,
            balance=balance,
            payment_form=payment_form
        )
    
    return render_template('supplier/statement.html', form=form)

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