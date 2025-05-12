from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, FloatField, SelectField, DateField,
    SubmitField, HiddenField, ValidationError
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import date, datetime, timedelta

class SupplierPaymentForm(FlaskForm):
    """Form for creating and updating supplier payments"""
    service_confirmation_id = SelectField('Service Confirmation', validators=[Optional()], coerce=int)
    amount = FloatField('Payment Amount', validators=[DataRequired(), NumberRange(min=0.01)], default=0.0)
    
    # Payment details
    payment_method = SelectField('Payment Method', choices=[
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CHECK', 'Check'),
        ('CASH', 'Cash'),
        ('PAYPAL', 'PayPal'),
        ('OTHER', 'Other')
    ], validators=[DataRequired()])
    payment_date = DateField('Payment Date', validators=[Optional()], default=date.today)
    payment_reference = StringField('Payment Reference', validators=[Optional(), Length(max=100)])
    
    # Invoice details
    invoice_number = StringField('Invoice Number', validators=[Optional(), Length(max=100)])
    invoice_date = DateField('Invoice Date', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    
    status = SelectField('Status', choices=[
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled')
    ], validators=[DataRequired()], default='PENDING')
    
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Payment')
    
    def validate_due_date(self, field):
        """Validate that due date is after invoice date if both are provided"""
        if field.data and self.invoice_date.data and field.data < self.invoice_date.data:
            raise ValidationError('Due date must be on or after the invoice date')
            
    def populate_from_confirmation(self, confirmation):
        """Populate form fields from a service confirmation"""
        if confirmation:
            self.amount.data = confirmation.cost_amount
            # Default due date to 30 days from today if not set
            if not self.due_date.data:
                self.due_date.data = date.today() + timedelta(days=30)


class SupplierInvoiceFilterForm(FlaskForm):
    """Form for filtering supplier invoices"""
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled')
    ], validators=[Optional()], default='')
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    min_amount = FloatField('Min Amount', validators=[Optional(), NumberRange(min=0)])
    max_amount = FloatField('Max Amount', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Apply Filters')