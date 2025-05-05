from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

from app.models import (
    STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_FULFILLED, STATUS_COMPLETED
)

class UpdateServiceStatusForm(FlaskForm):
    """Form for updating the status of a service item"""
    status = SelectField('Status', choices=[
        (STATUS_REQUEST, 'Request'),
        (STATUS_BOOKED, 'Booked'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_FULFILLED, 'Fulfilled'),
        (STATUS_COMPLETED, 'Completed')
    ], validators=[DataRequired()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Update Status')

class DocumentUploadForm(FlaskForm):
    """Form for uploading documents related to service items"""
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