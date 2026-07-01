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
    """Load custom payment terms from global_supplier_option_values.json.

    Returns a list of user-defined custom payment terms, or an empty list if none
    exist or if the config file cannot be read.
    """
    try:
        from flask import current_app, has_app_context

        # Try Flask app context first (most reliable in request context)
        if has_app_context():
            config_path = os.path.join(current_app.instance_path, 'global_supplier_option_values.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                custom_values = config.get('customer_payment_terms', [])
                if isinstance(custom_values, list):
                    return [str(v).strip() for v in custom_values if str(v).strip()]

        # Fallback: locate config via file path (handles cases without app context)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(module_dir)
        project_root = os.path.dirname(app_dir)
        config_path = os.path.join(project_root, 'instance', 'global_supplier_option_values.json')

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            custom_values = config.get('customer_payment_terms', [])
            if isinstance(custom_values, list):
                return [str(v).strip() for v in custom_values if str(v).strip()]

    except (IOError, json.JSONDecodeError, KeyError):
        # Config file unavailable or malformed; return empty list
        # This prevents form initialization from crashing
        pass

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


class PaymentTermsField(SelectField):
    """SelectField for customer payment terms supporting standard and custom values.

    Dynamically loads choices from both predefined payment terms and custom terms
    stored in the global configuration. Validates submitted values against both
    sets to ensure only recognized payment terms are accepted.
    """

    # Standard payment terms that are always available
    STANDARD_TERMS = {
        'Cash before arrival',
        'Credit',
        'NET 15',
        'NET 30',
        'NET 45',
        'NET 60',
        'Prepaid',
        'Cash on Delivery',
        'Cliq',
        'Other',
    }

    def iter_choices(self):
        """Dynamically iterate all available payment term choices."""
        for value, label in get_customer_payment_terms_choices():
            yield value, label, self.coerce(value) == self.data

    def pre_validate(self, form):
        """Validate that the selected payment term is standard or custom.

        Allows empty selection (handled by Optional validator) and checks
        that non-empty values are either standard terms or custom terms
        that have been defined in the global configuration.
        """
        if not self.data:
            # Empty selection is valid if Optional validator permits it
            return

        # Load all valid payment terms (standard + custom)
        custom_terms = set(load_custom_payment_terms())
        valid_terms = self.STANDARD_TERMS | custom_terms

        if self.data in valid_terms:
            return

        # Invalid payment term
        raise ValidationError('Selected payment term is not recognized.')


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
    payment_terms = PaymentTermsField(
        'Payment Terms',
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