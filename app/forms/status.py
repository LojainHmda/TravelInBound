from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

from app.models.service import (
    STATUS_REQUEST, STATUS_QUOTED, STATUS_CONFIRMED, STATUS_PENDING, STATUS_COMPLETED
)

class UpdateServiceStatusForm(FlaskForm):
    """Form for updating the status of a service item"""
    status = SelectField('Status', choices=[
        (STATUS_REQUEST, 'New Request'),
        (STATUS_QUOTED, 'Quoted'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_PENDING, 'Processing'),
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