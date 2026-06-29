from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from datetime import datetime
import sys
from app.models import ServiceItem, Document, ServiceConfirmation
from app.forms.confirmation import ServiceConfirmationBaseForm

# Create blueprint
confirmation_bp = Blueprint('confirmation', __name__, url_prefix='/confirmations')

@confirmation_bp.route('/service/<int:item_id>/supplier', methods=['GET', 'POST'])
def add_supplier_confirmation(item_id):
    """Add or update supplier details and costs for a service confirmation"""
    # Get the service item
    service_item = ServiceItem.query.get_or_404(item_id)
    
    # Get existing confirmation if available
    confirmation = ServiceConfirmation.query.filter_by(service_item_id=item_id).first()
    
    # Get confirmation document if available
    confirmation_doc = Document.query.filter_by(
        service_item_id=item_id, document_type='CONFIRMATION'
    ).first()
    
    # Initialize form with existing data or defaults
    form = ServiceConfirmationBaseForm(obj=confirmation)
    
    # Set selling amount from service item
    if request.method == 'GET':
        form.selling_amount.data = service_item.amount
        form.selling_currency.data = 'USD'  # Default
    
    # Process form submission
    if form.validate_on_submit():
        if not confirmation:
            # Create new confirmation
            confirmation = ServiceConfirmation(
                service_item_id=service_item.id,
                supplier_id=form.supplier_id.data,
                confirmation_reference=form.confirmation_reference.data,
                cost_amount=form.cost_amount.data,
                cost_currency=form.cost_currency.data,
                payment_due_date=form.payment_due_date.data,
                selling_amount=form.selling_amount.data,
                selling_currency=form.selling_currency.data,
                notes=form.notes.data
            )
            db.session.add(confirmation)
        else:
            # Update existing confirmation
            form.populate_obj(confirmation)
        
        # Update service item status to BOOKED if it's still in REQUEST or IN_PROGRESS
        if service_item.status in ['REQUEST', 'IN_PROGRESS']:
            service_item.status = 'BOOKED'
        
        db.session.commit()
        
        # Directly create a Supplier Prepayment Line to track supplier costs
        from app.models.supplier import SupplierPrepaymentLine
        from app.models.service import Document
        
        # Check if document exists
        confirmation_doc = Document.query.filter_by(
            service_item_id=service_item.id, 
            document_type='CONFIRMATION'
        ).first()
        
        # Get the supplier details
        from app.models.supplier import Supplier
        supplier = Supplier.query.get(confirmation.supplier_id)
        supplier_name = supplier.name if supplier else "Unknown Supplier"
        
        # Create the prepayment line directly - with no link to a payment
        prepayment_line = SupplierPrepaymentLine(
            supplier_payment_id=None,  # Will NOT be linked to a payment
            booking_id=service_item.booking_id,
            service_item_id=service_item.id,
            amount=confirmation.cost_amount,
            supplier_name=supplier_name,
            service_type=service_item.service_type,
            confirmation_reference=confirmation_doc.document_number if confirmation_doc else None,
            payment_status='PENDING',
            notes=f"Supplier cost for {service_item.service_type} confirmation {confirmation.confirmation_reference}"
        )
        db.session.add(prepayment_line)
        db.session.commit()
        
        # Log the creation of the supplier cost
        print(f"Created supplier cost line of ${confirmation.cost_amount} for booking #{service_item.booking_id}", file=sys.stderr)
        
        flash('Supplier cost recorded and linked to booking successfully', 'success')
        
        flash('Supplier confirmation details saved successfully', 'success')
        return redirect(url_for('booking.details', booking_id=service_item.booking_id))
    
    # Get suppliers for dropdown
    from app.models.supplier import Supplier
    suppliers = [(s.id, f"{s.name} ({s.code})") for s in Supplier.query.order_by(Supplier.name).all()]
    form.supplier_id.choices = suppliers
    
    return render_template(
        'confirmation/supplier_form.html',
        form=form,
        service_item=service_item,
        confirmation=confirmation,
        confirmation_doc=confirmation_doc
    )