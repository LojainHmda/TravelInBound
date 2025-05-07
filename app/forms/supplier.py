from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField, FileField
from wtforms.validators import DataRequired, Email, Optional, Length
from datetime import datetime

class SupplierForm(FlaskForm):
    """Form for creating and editing suppliers"""
    name = StringField('Supplier Name', validators=[DataRequired(), Length(min=3, max=100)])
    code = StringField('Supplier Code', validators=[DataRequired(), Length(min=2, max=20)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=50)])
    country = StringField('Country', validators=[Optional(), Length(max=50)])
    website = StringField('Website', validators=[Optional(), Length(max=255)])
    payment_terms = StringField('Payment Terms', validators=[Optional(), Length(max=100)])
    account_number = StringField('Account Number', validators=[Optional(), Length(max=50)])
    tax_number = StringField('Tax Number', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Supplier')

class SupplierDocumentForm(FlaskForm):
    """Form for uploading supplier documents"""
    document_type = SelectField('Document Type', choices=[
        ('CONTRACT', 'Contract'),
        ('AGREEMENT', 'Agreement'),
        ('INVOICE', 'Invoice'),
        ('RECEIPT', 'Payment Receipt'),
        ('LICENSE', 'License/Certification'),
        ('OTHER', 'Other Document')
    ], validators=[DataRequired()])
    document_number = StringField('Document Number', validators=[DataRequired(), Length(max=100)])
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[Optional()])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    file = FileField('Upload Document', validators=[DataRequired()])
    submit = SubmitField('Upload Document')

class SupplierSearchForm(FlaskForm):
    """Form for searching suppliers"""
    query = StringField('Search Suppliers', validators=[Optional()])
    country = SelectField('Country', validators=[Optional()], choices=[('', 'All Countries')])
    service_type = SelectField('Service Type', validators=[Optional()], choices=[
        ('', 'All Services'),
        ('FLIGHT', 'Flight'),
        ('HOTEL', 'Hotel'),
        ('TRANSPORT', 'Transport'),
        ('VISA', 'Visa'),
        ('INSURANCE', 'Insurance')
    ])
    submit = SubmitField('Search')