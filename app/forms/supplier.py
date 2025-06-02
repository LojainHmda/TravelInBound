from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange

class SupplierForm(FlaskForm):
    """Form for creating and editing suppliers"""
    name = StringField('Supplier Name', validators=[DataRequired(), Length(min=3, max=100)])
    code = StringField('Supplier Code', validators=[DataRequired(), Length(min=2, max=20)])
    supplier_type = SelectField('Supplier Type', choices=[
        ('AIRLINE', 'Airline'),
        ('HOTEL', 'Hotel'),
        ('TRANSPORT', 'Transport'),
        ('VISA', 'Visa Service'),
        ('INSURANCE', 'Insurance'),
        ('TOUR_OPERATOR', 'Tour Operator'),
        ('OTHER', 'Other')
    ])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    website = StringField('Website', validators=[Optional(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=50)])
    country = StringField('Country', validators=[Optional(), Length(max=50)])
    payment_terms = StringField('Payment Terms', validators=[Optional(), Length(max=100)])
    default_currency = SelectField('Default Currency', choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP')
    ], default='USD')
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=100)])
    bank_account = StringField('Bank Account', validators=[Optional(), Length(max=100)])
    tax_number = StringField('Tax Number', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Supplier')


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


class SupplierDocumentForm(FlaskForm):
    """Form for uploading supplier documents"""
    document_type = SelectField('Document Type', choices=[
        ('CONTRACT', 'Contract'),
        ('INVOICE', 'Invoice'),
        ('AGREEMENT', 'Agreement'),
        ('CERTIFICATE', 'Certificate'),
        ('OTHER', 'Other')
    ], validators=[DataRequired()])
    
    document_number = StringField('Document Number', validators=[DataRequired(), Length(max=100)])
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[Optional()])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    file = FileField('Document File', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Only PDF, Word, and image files allowed!')
    ])
    submit = SubmitField('Upload Document')