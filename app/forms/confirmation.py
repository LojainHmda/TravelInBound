from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import datetime, date

class ServiceConfirmationBaseForm(FlaskForm):
    """Base form for service confirmations with supplier cost tracking"""
    confirmation_reference = StringField('Confirmation Reference', validators=[DataRequired()])
    supplier_id = SelectField('Supplier', validators=[DataRequired()], coerce=int)
    
    # Supplier cost fields
    cost_amount = FloatField('Cost Amount (Supplier)', validators=[DataRequired(), NumberRange(min=0)])
    cost_currency = SelectField('Currency', choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP')
    ], default='USD')
    payment_due_date = DateField('Payment Due Date', format='%Y-%m-%d', 
        validators=[Optional()], default=date.today)
    
    # Hidden fields to store the selling amount from the service item
    selling_amount = HiddenField('Selling Amount')
    selling_currency = HiddenField('Selling Currency')
    
    # Additional notes
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Save Confirmation')

class SupplierPaymentForm(FlaskForm):
    """Form for recording payments to suppliers"""
    supplier_id = SelectField('Supplier', validators=[DataRequired()], coerce=int)
    service_confirmation_id = SelectField('Service Confirmation', validators=[Optional()], coerce=int)
    amount = FloatField('Payment Amount', validators=[DataRequired(), NumberRange(min=0)])
    payment_date = DateField('Payment Date', format='%Y-%m-%d', 
        validators=[DataRequired()], default=date.today)
    payment_reference = StringField('Payment Reference', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CHECK', 'Check'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Record Payment')

class SupplierStatementForm(FlaskForm):
    """Form for generating supplier statements"""
    supplier_id = SelectField('Supplier', validators=[DataRequired()], coerce=int)
    from_date = DateField('From Date', format='%Y-%m-%d', 
        validators=[Optional()], default=lambda: date.today().replace(day=1))
    to_date = DateField('To Date', format='%Y-%m-%d', 
        validators=[Optional()], default=date.today)
    status = SelectField('Payment Status', choices=[
        ('ALL', 'All'),
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid')
    ], default='ALL')
    
    submit = SubmitField('Generate Statement')