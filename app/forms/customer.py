from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length

def get_customer_type_choices():
    """Return customer type choices - using a function to avoid caching issues"""
    return [
        ('Direct', 'Direct'),
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Other', 'Other')
    ]


def get_customer_payment_terms_choices():
    return [
        ('', 'Select payment terms...'),
        ('Cash before arrival', 'Cash before arrival'),
        ('Credit', 'Credit'),
        ('NET 15', 'NET 15'),
        ('NET 30', 'NET 30'),
        ('NET 45', 'NET 45'),
        ('NET 60', 'NET 60'),
        ('Prepaid', 'Prepaid'),
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Cliq', 'Cliq'),
        ('Other', 'Other'),
    ]


class CustomerForm(FlaskForm):
    """Form for creating and editing customers"""
    agent_name = StringField(
        'Agent Name',
        validators=[DataRequired(), Length(min=1, max=120)],
    )
    contact_person = StringField(
        'Contact Person',
        validators=[Optional(), Length(max=100)],
    )
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=1, max=20)])
    customer_type = SelectField('Customer Type', choices=get_customer_type_choices, default='Direct')
    payment_terms = SelectField(
        'Payment Terms',
        choices=get_customer_payment_terms_choices,
        validators=[Optional()],
    )
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=120)])
    bank_account = StringField('Bank Account', validators=[Optional(), Length(max=255)])
    cliq_alias = StringField('Cliq number / Alias', validators=[Optional(), Length(max=255)])
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
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Direct', 'Direct'),
        ('Other', 'Other')
    ])
    country = SelectField('Country', validators=[Optional()], choices=[('', 'All Countries')])
    submit = SubmitField('Search')