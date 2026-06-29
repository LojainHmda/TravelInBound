from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, Regexp, ValidationError
import json
import os


def get_customer_type_choices():
    """Return customer type choices - using a function to avoid caching issues"""
    return [
        ('Direct', 'Direct'),
        ('Travel Agent', 'Travel Agent'),
        ('Corporate', 'Corporate'),
        ('Other', 'Other')
    ]


def load_custom_payment_terms():
    """Load custom payment terms from global config file"""
    try:
        from flask import current_app, has_app_context

        # Debug: log what we're trying
        debug_log = []
        debug_log.append(f"has_app_context: {has_app_context()}")

        # Try Flask app context first (most reliable)
        if has_app_context():
            global_path = os.path.join(current_app.instance_path, 'global_supplier_option_values.json')
            debug_log.append(f"Flask path: {global_path}")
            debug_log.append(f"Flask path exists: {os.path.exists(global_path)}")
            if os.path.exists(global_path):
                with open(global_path, 'r', encoding='utf-8') as f:
                    values_map = json.load(f)
                custom_values = values_map.get('customer_payment_terms', [])
                if isinstance(custom_values, list):
                    with open('/tmp/payment_terms_debug.log', 'a') as log_f:
                        log_f.write(f"SUCCESS via Flask: {custom_values}\n")
                    return [str(v).strip() for v in custom_values if str(v).strip()]

        # Fallback: construct from __file__ location
        this_file = os.path.abspath(__file__)
        app_forms_dir = os.path.dirname(this_file)
        app_dir = os.path.dirname(app_forms_dir)
        project_root = os.path.dirname(app_dir)
        json_path = os.path.join(project_root, 'instance', 'global_supplier_option_values.json')

        debug_log.append(f"Fallback __file__: {this_file}")
        debug_log.append(f"Fallback path: {json_path}")
        debug_log.append(f"Fallback path exists: {os.path.exists(json_path)}")

        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                values_map = json.load(f)
            custom_values = values_map.get('customer_payment_terms', [])
            if isinstance(custom_values, list):
                with open('/tmp/payment_terms_debug.log', 'a') as log_f:
                    log_f.write(f"SUCCESS via fallback: {custom_values}\n")
                    log_f.write("Debug info:\n")
                    for line in debug_log:
                        log_f.write(f"  {line}\n")
                return [str(v).strip() for v in custom_values if str(v).strip()]

        # If we reach here, log failure
        with open('/tmp/payment_terms_debug.log', 'a') as log_f:
            log_f.write(f"FAILED - neither path worked\n")
            for line in debug_log:
                log_f.write(f"  {line}\n")

    except Exception as e:
        with open('/tmp/payment_terms_debug.log', 'a') as log_f:
            log_f.write(f"EXCEPTION: {str(e)}\n")

    return []


def get_customer_payment_terms_choices():
    """Return all payment term choices including custom values"""
    base_choices = [
        ('Cash before arrival', 'Cash before arrival'),
        ('Credit', 'Credit'),
        ('NET 15', 'NET 15'),
        ('NET 30', 'NET 30'),
        ('NET 45', 'NET 45'),
        ('NET 60', 'NET 60'),
        ('Prepaid', 'Prepaid'),
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Cliq', 'Cliq'),
    ]

    # Load and add custom values
    custom_values = load_custom_payment_terms()
    for val in custom_values:
        if val not in [c[0] for c in base_choices]:
            base_choices.append((val, val))

    return [('', 'Select payment terms...')] + sorted(base_choices) + [('Other', 'Other')]


class DynamicPaymentTermsField(SelectField):
    """SelectField that accepts standard payment terms and any user-defined custom values"""

    def validate(self, form, extra_validators=None):
        """Override validate to accept custom payment terms without strict choices validation"""
        # Accept empty values if Optional validator allows
        if not self.data:
            return

        # Accept any non-empty value - it's either standard or a custom value from the modal
        # The template ensures it's a reasonable length, and the API validated it when saved
        return

    def pre_validate(self, form, extra_validators=None):
        """Accept standard payment terms and any custom values entered via the modal"""
        # Skip validation for empty values (Optional validator handles this)
        if not self.data:
            return

        # Standard payment terms - always valid
        standard_values = {
            'Cash before arrival', 'Credit', 'NET 15', 'NET 30', 'NET 45',
            'NET 60', 'Prepaid', 'Cash on Delivery', 'Cliq', 'Other'
        }

        # If it's a standard value, it's valid
        if self.data in standard_values:
            return

        # For non-standard values, check if they're in our stored custom values
        try:
            custom_values = set(load_custom_payment_terms())
            if self.data in custom_values:
                return
        except Exception:
            pass

        # Accept any non-empty string value that's a reasonable length
        # This allows custom values added via the modal to pass validation
        if self.data and len(self.data) <= 100:
            # Accept it - it's a legitimate custom value from the modal
            return

        # Reject invalid values
        raise ValidationError('Not a valid choice.')


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
    phone = StringField('Phone', validators=[DataRequired(), Length(min=1, max=20), Regexp(r'^[0-9 +]+$', message='Only digits (0–9), spaces, and + are allowed.')])
    customer_type = SelectField('Customer Type', choices=get_customer_type_choices, default='Direct')
    # StringField for payment_terms - accepts any value entered via dropdown or modal
    # The template renders a SELECT element with JavaScript for custom value entry
    payment_terms = StringField(
        'Payment Terms',
        validators=[Optional(), Length(max=100)],
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