from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models.service import ServiceItem, Document, ServiceConfirmation
from app.models.supplier import Supplier
from app.forms.confirmation import ServiceConfirmationBaseForm, SupplierPaymentForm
from app.forms.status import UpdateServiceStatusForm
from app.models import STATUS_FULFILLED
import json
import sys
from datetime import datetime

# Create a blueprint for confirmation-related routes
confirmation_bp = Blueprint('confirmation', __name__, url_prefix='/confirmations')

@confirmation_bp.route('/<int:item_id>/supplier', methods=['GET', 'POST'])
def add_supplier_confirmation(item_id):
    """Add or update supplier details and costs for a service confirmation"""
    service_item = ServiceItem.query.get_or_404(item_id)
    
    # Get existing confirmation document if available
    confirmation_doc = Document.query.filter_by(
        service_item_id=service_item.id, 
        document_type='CONFIRMATION'
    ).first()
    
    # Get existing service confirmation record if available
    service_confirmation = ServiceConfirmation.query.filter_by(
        service_item_id=service_item.id
    ).first()
    
    # Prepare the form
    form = ServiceConfirmationBaseForm()
    
    # Get all suppliers for the dropdown
    suppliers = Supplier.query.order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    # Pre-populate the form with existing data if available
    if request.method == 'GET' and service_confirmation:
        form.confirmation_reference.data = service_confirmation.confirmation_reference
        form.supplier_id.data = service_confirmation.supplier_id
        form.cost_amount.data = service_confirmation.cost_amount
        form.cost_currency.data = service_confirmation.cost_currency
        form.payment_due_date.data = service_confirmation.payment_due_date
        form.notes.data = service_confirmation.notes
    
    # Always set the selling amount from the service item
    form.selling_amount.data = service_item.amount
    form.selling_currency.data = 'USD'  # Default currency
    
    if form.validate_on_submit():
        # Create or update the service confirmation record
        if not service_confirmation:
            service_confirmation = ServiceConfirmation(
                service_item_id=service_item.id,
                supplier_id=form.supplier_id.data,
                confirmation_reference=form.confirmation_reference.data,
                cost_amount=form.cost_amount.data,
                cost_currency=form.cost_currency.data,
                selling_amount=service_item.amount,
                selling_currency=form.selling_currency.data,
                payment_due_date=form.payment_due_date.data,
                notes=form.notes.data
            )
            db.session.add(service_confirmation)
        else:
            service_confirmation.supplier_id = form.supplier_id.data
            service_confirmation.confirmation_reference = form.confirmation_reference.data
            service_confirmation.cost_amount = form.cost_amount.data
            service_confirmation.cost_currency = form.cost_currency.data
            service_confirmation.selling_amount = service_item.amount
            service_confirmation.selling_currency = form.selling_currency.data
            service_confirmation.payment_due_date = form.payment_due_date.data
            service_confirmation.notes = form.notes.data
        
        # Calculate the margin
        service_confirmation.calculate_margin()
        
        # If there's a confirmation document, link it to the service confirmation
        if confirmation_doc:
            service_confirmation.document_id = confirmation_doc.id
        
        db.session.commit()
        
        # Mark service item as fulfilled if it's not already
        if service_item.status != STATUS_FULFILLED:
            service_item.status = STATUS_FULFILLED
            db.session.commit()
            
        flash('Supplier confirmation details have been saved', 'success')
        return redirect(url_for('booking.details', booking_id=service_item.booking_id))
    
    return render_template('confirmation/supplier_form.html',
                          form=form,
                          service_item=service_item,
                          confirmation_doc=confirmation_doc,
                          service_confirmation=service_confirmation)

@confirmation_bp.route('/api/supplier/<int:supplier_id>', methods=['GET'])
def get_supplier_details(supplier_id):
    """API endpoint to get supplier details"""
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify({
        'id': supplier.id,
        'name': supplier.name,
        'code': supplier.code,
        'payment_terms': supplier.payment_terms
    })

@confirmation_bp.route('/api/service/<int:item_id>', methods=['GET'])
def get_confirmation_details(item_id):
    """API endpoint to get service confirmation details"""
    service_confirmation = ServiceConfirmation.query.filter_by(service_item_id=item_id).first()
    
    if not service_confirmation:
        return jsonify({
            'found': False,
            'message': 'No confirmation record found'
        })
    
    supplier = Supplier.query.get(service_confirmation.supplier_id)
    
    return jsonify({
        'found': True,
        'confirmation_id': service_confirmation.id,
        'confirmation_reference': service_confirmation.confirmation_reference,
        'supplier_id': service_confirmation.supplier_id,
        'supplier_name': supplier.name if supplier else 'Unknown',
        'cost_amount': service_confirmation.cost_amount,
        'cost_currency': service_confirmation.cost_currency,
        'selling_amount': service_confirmation.selling_amount,
        'selling_currency': service_confirmation.selling_currency,
        'margin': service_confirmation.margin,
        'margin_percentage': service_confirmation.margin_percentage,
        'is_paid': service_confirmation.is_paid,
        'payment_due_date': service_confirmation.payment_due_date.strftime('%Y-%m-%d') if service_confirmation.payment_due_date else None
    })