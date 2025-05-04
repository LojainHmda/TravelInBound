from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, FloatField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

from app.models import (
    SERVICE_FLIGHT, SERVICE_HOTEL, SERVICE_TRANSPORT, 
    SERVICE_VISA, SERVICE_INSURANCE, STATUS_REQUEST, 
    STATUS_INVOICE, STATUS_IN_PROGRESS, STATUS_COMPLETED
)

class BookingRequestForm(FlaskForm):
    """Form for creating a new booking with itinerary items - like the example image"""
    # Customer selection
    customer = SelectField('Select Customer', validators=[DataRequired()])
    
    # Reference/Request ID - system generated
    request_id = StringField('Request ID', render_kw={'readonly': True})
    
    # Service Item Fields
    service_type = SelectField('Service Type', choices=[
        (SERVICE_FLIGHT, 'Flight'),
        (SERVICE_HOTEL, 'Hotel'),
        (SERVICE_TRANSPORT, 'Transport'),
        (SERVICE_VISA, 'Visa'),
        (SERVICE_INSURANCE, 'Insurance')
    ])
    
    from_date = DateField('From Date', validators=[DataRequired()])
    to_date = DateField('To Date', validators=[DataRequired()])
    description = TextAreaField('Description')
    amount = FloatField('Amount')
    currency = SelectField('Currency', choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP')
    ], default='USD')
    
    # Deposit amount
    deposit_amount = FloatField('Deposit Amount')
    
    submit = SubmitField('Create Booking Request')
    add_item = SubmitField('Add Item')

class NewBookingForm(FlaskForm):
    """Legacy form for creating a booking with service checkboxes"""
    reference_number = StringField('Reference Number', validators=[DataRequired(), Length(min=4, max=20)])
    
    # Service selection checkboxes
    flight_service = BooleanField('Flight')
    hotel_service = BooleanField('Hotel')
    transport_service = BooleanField('Transport')
    visa_service = BooleanField('Visa')
    insurance_service = BooleanField('Insurance')
    
    submit = SubmitField('Create Booking Request')

class ServiceItemForm(FlaskForm):
    """Form for adding a service item to an existing booking"""
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