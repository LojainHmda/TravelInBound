from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class ServiceConfirmationBaseForm(FlaskForm):
    """Base form for service confirmations with supplier cost tracking"""
    confirmation_reference = StringField('Confirmation Reference', validators=[DataRequired()])
    supplier_id = SelectField('Supplier', validators=[DataRequired()], coerce=int)
    
    cost_amount = FloatField('Cost Amount (Supplier)', validators=[DataRequired(), NumberRange(min=0)])
    cost_currency = SelectField('Currency', choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP')
    ], default='USD')
    payment_due_date = DateField('Payment Due Date', format='%Y-%m-%d', 
        validators=[Optional()], default=date.today)
    
    selling_amount = HiddenField('Selling Amount')
    selling_currency = HiddenField('Selling Currency')
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Save Confirmation')