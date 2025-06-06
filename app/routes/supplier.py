from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.supplier import Supplier, SupplierPayment, SupplierPrepaymentLine
from app.forms.supplier import SupplierForm, SupplierPaymentForm
from datetime import datetime

supplier = Blueprint('supplier', __name__, url_prefix='/supplier')

@supplier.route('/')
@login_required
def list_suppliers():
    """List all suppliers"""
    query = request.args.get('query', '')
    service_type = request.args.get('service_type', '')
    
    # Build query
    suppliers_query = Supplier.query.filter(Supplier.is_active == True)
    
    if query:
        suppliers_query = suppliers_query.filter(
            db.or_(
                Supplier.name.ilike(f'%{query}%'),
                Supplier.code.ilike(f'%{query}%'),
                Supplier.email.ilike(f'%{query}%')
            )
        )
    
    if service_type:
        suppliers_query = suppliers_query.filter(
            Supplier.service_types.like(f'%{service_type}%')
        )
    
    suppliers = suppliers_query.order_by(Supplier.name).all()
    
    return render_template('supplier/list.html', 
                         suppliers=suppliers, 
                         query=query, 
                         service_type=service_type)

@supplier.route('/new', methods=['GET', 'POST'])
@login_required
def new_supplier():
    """Create a new supplier"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        try:
            # Collect selected service types from checkboxes
            service_types = []
            if form.service_flight.data:
                service_types.append('FLIGHT')
            if form.service_hotel.data:
                service_types.append('HOTEL')
            if form.service_transport.data:
                service_types.append('TRANSPORT')
            if form.service_visa.data:
                service_types.append('VISA')
            if form.service_insurance.data:
                service_types.append('INSURANCE')
            if form.service_tour.data:
                service_types.append('TOUR')
            if form.service_other.data:
                service_types.append('OTHER')
            
            supplier = Supplier(
                name=form.name.data,
                code=form.code.data,
                contact_person=form.contact_person.data,
                email=form.email.data,
                phone=form.phone.data,
                website=form.website.data,
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
            
            # Set service types using the new method
            supplier.set_service_types(service_types)
            
            db.session.add(supplier)
            db.session.commit()
            
            flash('Supplier created successfully!', 'success')
            return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating supplier: {str(e)}', 'error')
    
    return render_template('supplier/edit.html', form=form, supplier=None, is_new=True)

@supplier.route('/<int:supplier_id>')
@login_required
def view_supplier(supplier_id):
    """View supplier details"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Get recent payments
    recent_payments = SupplierPayment.query.filter_by(supplier_id=supplier_id)\
                                          .order_by(SupplierPayment.payment_date.desc())\
                                          .limit(10).all()
    
    # Calculate totals
    total_payments = db.session.query(db.func.sum(SupplierPayment.amount))\
                              .filter_by(supplier_id=supplier_id).scalar() or 0
    
    return render_template('supplier/view.html', 
                         supplier=supplier, 
                         recent_payments=recent_payments,
                         total_payments=total_payments)

@supplier.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    """Edit supplier details"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    # Set checkbox values based on current service types
    if request.method == 'GET':
        service_types = supplier.get_service_types_list()
        form.service_flight.data = 'FLIGHT' in service_types
        form.service_hotel.data = 'HOTEL' in service_types
        form.service_transport.data = 'TRANSPORT' in service_types
        form.service_visa.data = 'VISA' in service_types
        form.service_insurance.data = 'INSURANCE' in service_types
        form.service_tour.data = 'TOUR' in service_types
        form.service_other.data = 'OTHER' in service_types
    
    if form.validate_on_submit():
        try:
            # Collect selected service types from checkboxes
            service_types = []
            if form.service_flight.data:
                service_types.append('FLIGHT')
            if form.service_hotel.data:
                service_types.append('HOTEL')
            if form.service_transport.data:
                service_types.append('TRANSPORT')
            if form.service_visa.data:
                service_types.append('VISA')
            if form.service_insurance.data:
                service_types.append('INSURANCE')
            if form.service_tour.data:
                service_types.append('TOUR')
            if form.service_other.data:
                service_types.append('OTHER')
            
            # Update supplier fields
            supplier.name = form.name.data
            supplier.code = form.code.data
            supplier.contact_person = form.contact_person.data
            supplier.email = form.email.data
            supplier.phone = form.phone.data
            supplier.website = form.website.data
            supplier.address = form.address.data
            supplier.city = form.city.data
            supplier.country = form.country.data
            supplier.payment_terms = form.payment_terms.data
            supplier.default_currency = form.default_currency.data
            supplier.bank_name = form.bank_name.data
            supplier.bank_account = form.bank_account.data
            supplier.tax_number = form.tax_number.data
            supplier.notes = form.notes.data
            
            # Update service types
            supplier.set_service_types(service_types)
            
            db.session.commit()
            
            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating supplier: {str(e)}', 'error')
    
    return render_template('supplier/edit.html', form=form, supplier=supplier, is_new=False)

@supplier.route('/<int:supplier_id>/payments')
@login_required
def supplier_payments(supplier_id):
    """List payments for a supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    payments = SupplierPayment.query.filter_by(supplier_id=supplier_id)\
                                   .order_by(SupplierPayment.payment_date.desc()).all()
    
    total_payments = sum(payment.amount for payment in payments)
    
    return render_template('supplier/payments.html', 
                         supplier=supplier, 
                         payments=payments,
                         total_payments=total_payments)

@supplier.route('/<int:supplier_id>/new-payment', methods=['GET', 'POST'])
@login_required
def new_payment(supplier_id):
    """Create a new payment for supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierPaymentForm()
    
    # Set supplier choices and default
    form.supplier_id.choices = [(supplier.id, supplier.name)]
    form.supplier_id.data = supplier.id
    
    if form.validate_on_submit():
        try:
            payment = SupplierPayment(
                supplier_id=form.supplier_id.data,
                service_confirmation_id=form.service_confirmation_id.data if form.service_confirmation_id.data else None,
                amount=form.amount.data,
                payment_date=form.payment_date.data,
                payment_reference=form.payment_reference.data,
                payment_method=form.payment_method.data,
                notes=form.notes.data,
                status='PAID'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('supplier.view_supplier', supplier_id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'error')
    
    return render_template('supplier/create_payment.html', 
                         form=form, 
                         supplier=supplier)