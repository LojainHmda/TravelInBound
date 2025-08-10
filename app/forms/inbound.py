from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField, TextAreaField, FloatField, BooleanField, TimeField
from wtforms.validators import DataRequired, NumberRange, Optional
from app.data.nationalities import NATIONALITIES

class InboundRequestForm(FlaskForm):
    """Form for creating new inbound tour requests"""
    
    # Header fields
    from_date = DateField('From Date', validators=[DataRequired()])
    to_date = DateField('To Date', validators=[DataRequired()])
    no_of_days = IntegerField('No. of Days', validators=[Optional(), NumberRange(min=1)])
    
    # Client information
    customer = SelectField('Select Customer', validators=[DataRequired()])
    agent = StringField('Agent', validators=[DataRequired()])
    contact_name = StringField('Contact Name', validators=[DataRequired()])
    agent_ref = StringField('Agent Ref', validators=[Optional()])
    nationality = SelectField('Nationality', choices=[(nat, nat) for nat in NATIONALITIES], validators=[DataRequired()])
    pax = IntegerField('Pax', validators=[DataRequired(), NumberRange(min=1)])
    special_note = TextAreaField('Special Note', validators=[Optional()])

class ItineraryRowForm(FlaskForm):
    """Form for individual itinerary rows"""
    
    date = DateField('Date', validators=[DataRequired()])
    description = TextAreaField('Itinerary Description', validators=[DataRequired()])
    
    # Costing
    base_cost = FloatField('Base Cost', validators=[Optional(), NumberRange(min=0)])
    cost_unit = SelectField('Cost Unit', 
                           choices=[('PER_PERSON', 'Per Person'), ('PER_GROUP', 'Per Group')],
                           default='PER_PERSON')
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('JOD', 'JOD')],
                          default='USD')
    
    # Service flags
    flag_hotel = BooleanField('Hotel')
    flag_guide = BooleanField('M&G/Guide')
    flag_transport = BooleanField('Transport')
    flag_meal = BooleanField('Meal')
    flag_airport = BooleanField('Airport')

class InboundHotelForm(FlaskForm):
    """Form for hotel service items"""
    
    hotel_name = StringField('Hotel Name', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    check_in_date = DateField('Check-in Date', validators=[DataRequired()])
    check_out_date = DateField('Check-out Date', validators=[DataRequired()])
    nights = IntegerField('Nights', validators=[DataRequired(), NumberRange(min=1)])
    room_type = StringField('Room Type', validators=[Optional()])
    meal_plan = SelectField('Meal Plan', 
                           choices=[('BB', 'Bed & Breakfast'), ('HB', 'Half Board'), 
                                   ('FB', 'Full Board'), ('AI', 'All Inclusive')],
                           default='BB')
    
    # Costing
    cost_per_night = FloatField('Cost per Night', validators=[Optional(), NumberRange(min=0)])
    total_cost = FloatField('Total Cost', validators=[Optional(), NumberRange(min=0)])
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('JOD', 'JOD')],
                          default='USD')

class InboundTransportForm(FlaskForm):
    """Form for transport service items"""
    
    date = DateField('Date', validators=[DataRequired()])
    vehicle_type = StringField('Vehicle Type', validators=[Optional()])
    pickup_location = StringField('Pickup Location', validators=[Optional()])
    dropoff_location = StringField('Dropoff Location', validators=[Optional()])
    pickup_time = TimeField('Pickup Time', validators=[Optional()])
    is_airport_transfer = BooleanField('Airport Transfer')
    
    # Costing
    cost = FloatField('Cost', validators=[Optional(), NumberRange(min=0)])
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('JOD', 'JOD')],
                          default='USD')

class InboundMealForm(FlaskForm):
    """Form for meal service items"""
    
    date = DateField('Date', validators=[DataRequired()])
    meal_type = SelectField('Meal Type', 
                           choices=[('Breakfast', 'Breakfast'), ('Lunch', 'Lunch'), 
                                   ('Dinner', 'Dinner'), ('Snack', 'Snack')],
                           validators=[Optional()])
    restaurant = StringField('Restaurant', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    meal_time = TimeField('Meal Time', validators=[Optional()])
    
    # Costing
    cost_per_person = FloatField('Cost per Person', validators=[Optional(), NumberRange(min=0)])
    total_cost = FloatField('Total Cost', validators=[Optional(), NumberRange(min=0)])
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('JOD', 'JOD')],
                          default='USD')

class InboundGuideForm(FlaskForm):
    """Form for guide service items"""
    
    date = DateField('Date', validators=[DataRequired()])
    guide_name = StringField('Guide Name', validators=[Optional()])
    language = StringField('Language', validators=[Optional()])
    service_type = SelectField('Service Type', 
                              choices=[('Meet & Greet', 'Meet & Greet'), 
                                      ('Tour Guide', 'Tour Guide'),
                                      ('Transfer Guide', 'Transfer Guide')],
                              validators=[Optional()])
    duration_hours = FloatField('Duration (Hours)', validators=[Optional(), NumberRange(min=0)])
    meeting_point = StringField('Meeting Point', validators=[Optional()])
    meeting_time = TimeField('Meeting Time', validators=[Optional()])
    
    # Costing
    cost = FloatField('Cost', validators=[Optional(), NumberRange(min=0)])
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('JOD', 'JOD')],
                          default='USD')