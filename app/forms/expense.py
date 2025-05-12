from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, FloatField, SelectField, BooleanField, 
    DateField, SubmitField, HiddenField, FileField, ValidationError
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import date
from models import (
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES, EXPENSE_CATEGORY_SALARIES,
    EXPENSE_CATEGORY_MARKETING, EXPENSE_CATEGORY_INSURANCE, EXPENSE_CATEGORY_SUPPLIES,
    EXPENSE_CATEGORY_TRAVEL, EXPENSE_CATEGORY_TAXES, EXPENSE_CATEGORY_SOFTWARE,
    EXPENSE_CATEGORY_TELECOM, EXPENSE_CATEGORY_MAINTENANCE, EXPENSE_CATEGORY_OTHER,
    PAYMENT_METHOD_CASH, PAYMENT_METHOD_CREDIT_CARD, PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_CHECK, PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_OTHER,
    RECURRENCE_NONE, RECURRENCE_DAILY, RECURRENCE_WEEKLY, RECURRENCE_MONTHLY,
    RECURRENCE_QUARTERLY, RECURRENCE_YEARLY
)

class ExpenseCategoryForm(FlaskForm):
    """Form for managing expense categories"""
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Category Code', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=255)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')

class ExpenseForm(FlaskForm):
    """Form for creating and editing expenses"""
    title = StringField('Expense Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    
    date_incurred = DateField('Date Incurred', validators=[DataRequired()], default=date.today)
    payment_date = DateField('Payment Date', validators=[Optional()])
    
    payment_method = SelectField('Payment Method', choices=[
        (PAYMENT_METHOD_CASH, 'Cash'),
        (PAYMENT_METHOD_CREDIT_CARD, 'Credit Card'),
        (PAYMENT_METHOD_BANK_TRANSFER, 'Bank Transfer'),
        (PAYMENT_METHOD_CHECK, 'Check'),
        (PAYMENT_METHOD_PAYPAL, 'PayPal'),
        (PAYMENT_METHOD_OTHER, 'Other')
    ])
    
    reference_number = StringField('Reference/Invoice Number', validators=[Optional(), Length(max=100)])
    vendor_name = StringField('Vendor/Supplier', validators=[Optional(), Length(max=100)])
    is_paid = BooleanField('Mark as Paid', default=False)
    
    # Recurrence fields
    is_recurring = BooleanField('Recurring Expense', default=False)
    recurrence_type = SelectField('Recurrence Type', choices=[
        (RECURRENCE_NONE, 'One-time'),
        (RECURRENCE_DAILY, 'Daily'),
        (RECURRENCE_WEEKLY, 'Weekly'),
        (RECURRENCE_MONTHLY, 'Monthly'),
        (RECURRENCE_QUARTERLY, 'Quarterly'),
        (RECURRENCE_YEARLY, 'Yearly')
    ], default=RECURRENCE_NONE)
    recurrence_ends = DateField('Recurrence End Date', validators=[Optional()])
    
    # Form actions
    submit = SubmitField('Save Expense')
    
    def validate_recurrence_ends(self, field):
        """Validate that recurrence end date is after incurred date"""
        if self.is_recurring.data and field.data and self.date_incurred.data:
            if field.data <= self.date_incurred.data:
                raise ValidationError('Recurrence end date must be after the incurred date.')

class ExpenseAttachmentForm(FlaskForm):
    """Form for uploading expense attachments"""
    file = FileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload Attachment')

class ExpenseFilterForm(FlaskForm):
    """Form for filtering expenses in reports and listings"""
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()], default=0)
    payment_status = SelectField('Payment Status', choices=[
        ('', 'All'),
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid')
    ], validators=[Optional()], default='')
    
    vendor_name = StringField('Vendor/Supplier', validators=[Optional()])
    min_amount = FloatField('Min Amount', validators=[Optional(), NumberRange(min=0)])
    max_amount = FloatField('Max Amount', validators=[Optional(), NumberRange(min=0)])
    
    submit = SubmitField('Apply Filters')
    export = SubmitField('Export to CSV')

class FinancialReportFilterForm(FlaskForm):
    """Form for filtering financial reports"""
    report_type = SelectField('Report Type', choices=[
        ('profit_loss', 'Profit & Loss Statement'),
        ('expense_summary', 'Expense Summary'),
        ('revenue_summary', 'Revenue Summary'),
        ('supplier_payments', 'Supplier Payments')
    ], validators=[DataRequired()], default='profit_loss')
    
    date_range = SelectField('Period', choices=[
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'), 
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
        ('custom', 'Custom Range')
    ], validators=[DataRequired()], default='this_month')
    
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    group_by = SelectField('Group By', choices=[
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year')
    ], validators=[Optional()], default='month')
    
    include_details = BooleanField('Include Details', default=False)
    
    submit = SubmitField('Generate Report')
    export = SubmitField('Export Report')