from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, FloatField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

from models import (
    SERVICE_FLIGHT, SERVICE_HOTEL, SERVICE_TRANSPORT, 
    SERVICE_VISA, SERVICE_INSURANCE, STATUS_REQUEST, 
    STATUS_INVOICE, STATUS_IN_PROGRESS, STATUS_COMPLETED
)

class NewBookingForm(FlaskForm):
    reference_number = StringField('Reference Number', validators=[DataRequired(), Length(min=4, max=20)])
    
    # Service selection checkboxes
    flight_service = BooleanField('Flight')
    hotel_service = BooleanField('Hotel')
    transport_service = BooleanField('Transport')
    visa_service = BooleanField('Visa')
    insurance_service = BooleanField('Insurance')
    
    submit = SubmitField('Create Booking Request')

class ServiceItemForm(FlaskForm):
    service_type = SelectField('Service Type', choices=[
        (SERVICE_FLIGHT, 'Flight'),
        (SERVICE_HOTEL, 'Hotel'),
        (SERVICE_TRANSPORT, 'Transport'),
        (SERVICE_VISA, 'Visa'),
        (SERVICE_INSURANCE, 'Insurance')
    ], validators=[DataRequired()])
    
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    
    submit = SubmitField('Add Service Item')

class UpdateServiceStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        (STATUS_REQUEST, 'Request'),
        (STATUS_INVOICE, 'Invoice'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed')
    ], validators=[DataRequired()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Update Status')

class DocumentUploadForm(FlaskForm):
    document_type = SelectField('Document Type', choices=[
        ('TICKET', 'Ticket'),
        ('CONFIRMATION', 'Booking Confirmation'),
        ('VISA', 'Visa Document'),
        ('INSURANCE', 'Insurance Policy'),
        ('OTHER', 'Other Document')
    ], validators=[DataRequired()])
    
    document_number = StringField('Document Number', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Upload Document')
