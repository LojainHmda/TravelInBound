from flask_wtf import FlaskForm
from wtforms import FloatField, StringField, TextAreaField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Optional

class GenerateInvoiceForm(FlaskForm):
    """Form for generating an invoice"""
    total_amount = FloatField('Total Amount', validators=[DataRequired()])
    notes = TextAreaField('Invoice Notes', validators=[Optional()])
    submit = SubmitField('Generate Invoice')

class PaymentForm(FlaskForm):
    """Form for processing payments"""
    amount = FloatField('Payment Amount', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('CREDIT_CARD', 'Credit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('PAYPAL', 'PayPal'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other')
    ], validators=[DataRequired()])
    transaction_id = StringField('Transaction ID', validators=[Optional()])
    payment_date = DateField('Payment Date', validators=[DataRequired()], format='%Y-%m-%d')
    notes = TextAreaField('Payment Notes', validators=[Optional()])
    submit = SubmitField('Process Payment')
    
    def validate_amount(self, field):
        """Validate that payment amount doesn't exceed the invoice amount"""
        from flask import request
        from app.models.booking import Booking
        
        if request.method == 'POST':
            booking_id = request.view_args.get('booking_id')
            if booking_id:
                booking = Booking.query.get(booking_id)
                if booking:
                    total_paid = sum(payment.amount for payment in booking.payments)
                    remaining = booking.total_amount - total_paid
                    
                    if field.data > remaining:
                        from wtforms.validators import ValidationError
                        raise ValidationError(f'Payment amount cannot exceed remaining balance (${remaining:.2f}).')