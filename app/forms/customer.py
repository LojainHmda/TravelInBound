from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length
from app.data.nationalities import NATIONALITIES

class CustomerForm(FlaskForm):
    """Form for creating and editing customers"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=100)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=1, max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=50)])
    country = StringField('Country', validators=[Optional(), Length(max=50)])
    passport_number = StringField('Passport Number', validators=[Optional(), Length(max=50)])
    passport_expiry = DateField('Passport Expiry', format='%Y-%m-%d', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    # Use nationalities from the data file, with a default empty option
    nationality = SelectField('Nationality', 
                             choices=[('', 'Select Nationality')] + NATIONALITIES,
                             validators=[Optional()])
    customer_type = SelectField('Customer Type', choices=[
        ('Individual', 'Individual'),
        ('Corporate', 'Corporate'),
        ('Group', 'Group')
    ], default='Individual')
    company_name = StringField('Company Name', validators=[Optional(), Length(max=100)])
    tax_number = StringField('Tax Number', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Customer')

class CustomerDocumentForm(FlaskForm):
    """Form for uploading customer documents"""
    document_type = SelectField('Document Type', choices=[
        ('PASSPORT', 'Passport'),
        ('VISA', 'Visa'),
        ('ID_CARD', 'ID Card'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('TRAVEL_INSURANCE', 'Travel Insurance'),
        ('MEDICAL_CERTIFICATE', 'Medical Certificate'),
        ('OTHER', 'Other Document')
    ], validators=[DataRequired()])
    document_number = StringField('Document Number', validators=[DataRequired(), Length(max=100)])
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[Optional()])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    issuing_country = StringField('Issuing Country', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    file = FileField('Upload Document', validators=[FileRequired()])
    submit = SubmitField('Upload Document')

class CustomerSearchForm(FlaskForm):
    """Form for searching customers"""
    query = StringField('Search Customers', validators=[Optional()])
    customer_type = SelectField('Customer Type', validators=[Optional()], choices=[
        ('', 'All Types'),
        ('Individual', 'Individual'),
        ('Corporate', 'Corporate'),
        ('Group', 'Group')
    ])
    country = SelectField('Country', validators=[Optional()], choices=[('', 'All Countries')])
    submit = SubmitField('Search')