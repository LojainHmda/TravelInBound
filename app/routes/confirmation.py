from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from datetime import datetime
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
        
        # Create or update a SupplierPayment record to track in finance module
        from app.models.supplier import SupplierPayment
        
        # Check if a payment record already exists for this confirmation
        supplier_payment = SupplierPayment.query.filter_by(service_confirmation_id=confirmation.id).first()
        
        if not supplier_payment:
            # Create a new supplier payment record
            supplier_payment = SupplierPayment(
                supplier_id=confirmation.supplier_id,
                service_confirmation_id=confirmation.id,
                amount=confirmation.cost_amount,
                payment_date=confirmation.payment_due_date or datetime.now().date(),
                due_date=confirmation.payment_due_date,
                status='PENDING',
                notes=f"Automatic payment record for {service_item.service_type} confirmation {confirmation.confirmation_reference}"
            )
            db.session.add(supplier_payment)
            db.session.commit()
            
            # Now create a prepayment line to link this payment with the booking
            from app.models.supplier import SupplierPrepaymentLine
            
            # Create the prepayment line
            prepayment_line = SupplierPrepaymentLine(
                supplier_payment_id=supplier_payment.id,
                booking_id=service_item.booking_id,
                service_item_id=service_item.id,
                amount=confirmation.cost_amount,
                notes=f"Auto-created for {service_item.service_type} confirmation {confirmation.confirmation_reference}"
            )
            db.session.add(prepayment_line)
            db.session.commit()
            
            flash('Supplier payment and booking link created successfully', 'success')
        
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