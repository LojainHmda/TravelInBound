from datetime import datetime, date
from app import db
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED

# Cost units for pricing
COST_UNIT_PER_PERSON = 'PER_PERSON'
COST_UNIT_PER_GROUP = 'PER_GROUP'

# Service flag types
SERVICE_FLAG_HOTEL = 'HOTEL'
SERVICE_FLAG_GUIDE = 'GUIDE'  # M&G/Guide
SERVICE_FLAG_TRANSPORT = 'TRANSPORT'
SERVICE_FLAG_MEAL = 'MEAL'
SERVICE_FLAG_AIRPORT = 'AIRPORT'

class InboundRequest(db.Model):
    """Main inbound tour operator request with itinerary-first approach"""
    __tablename__ = 'inbound_request'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(20), unique=True, nullable=False)  # INB-YYYYMM-####
    
    # Header fields
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    no_of_days = db.Column(db.Integer, nullable=False)
    
    # Client information
    customer_type = db.Column(db.String(20), nullable=False, default='AGENCY')  # AGENCY, GROUP, COMPANY, CORPORATE
    contact_name = db.Column(db.String(100), nullable=False)
    agent_ref = db.Column(db.String(50), nullable=True)
    nationality = db.Column(db.String(50), nullable=False)
    pax = db.Column(db.Integer, nullable=False, default=1)
    special_note = db.Column(db.Text, nullable=True)
    
    # Status and tracking
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # Link to customer
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)  # Link to normal booking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Total pricing
    total_amount = db.Column(db.Float, default=0.0)
    total_currency = db.Column(db.String(3), default='USD')
    
    # Relationships
    itinerary_rows = db.relationship('ItineraryRow', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_hotels = db.relationship('InboundHotel', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_transports = db.relationship('InboundTransport', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_meals = db.relationship('InboundMeal', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_guides = db.relationship('InboundGuide', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_cash_expenses = db.relationship('InboundCashExpense', backref='request', lazy=True, cascade="all, delete-orphan")
    booking = db.relationship('Booking', backref='inbound_request', lazy=True)
    
    def __repr__(self):
        return f'<InboundRequest {self.request_number}>'
    
    @classmethod
    def generate_request_number(cls):
        """Generate auto request number in format INB-YYYYMM-####"""
        now = datetime.now()
        prefix = f"INB-{now.strftime('%Y%m')}"
        
        # Find the highest number for current month
        latest = cls.query.filter(
            cls.request_number.like(f"{prefix}-%")
        ).order_by(cls.request_number.desc()).first()
        
        if latest:
            # Extract the number and increment
            try:
                last_num = int(latest.request_number.split('-')[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}-{next_num:04d}"
    
    def calculate_total(self):
        """Calculate total amount from all itinerary rows"""
        total = 0.0
        # Use query instead of relationship to avoid SQLAlchemy iteration error
        from app.models.inbound import ItineraryRow
        rows = ItineraryRow.query.filter_by(request_id=self.id).all()
        for row in rows:
            if row.cost_unit == COST_UNIT_PER_PERSON:
                total += (row.base_cost or 0) * self.pax
            else:  # PER_GROUP
                total += row.base_cost or 0
        
        self.total_amount = total
        return total
    
    def calculate_days(self):
        """Calculate number of days between from_date and to_date"""
        if self.from_date and self.to_date:
            delta = self.to_date - self.from_date
            self.no_of_days = delta.days + 1  # Include both start and end days
        return self.no_of_days

class ItineraryRow(db.Model):
    """Individual itinerary items with service flags and costing"""
    __tablename__ = 'itinerary_row'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    # Date and description
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Costing
    base_cost = db.Column(db.Float, default=0.0)
    cost_unit = db.Column(db.String(20), default=COST_UNIT_PER_PERSON)  # PER_PERSON or PER_GROUP
    currency = db.Column(db.String(3), default='USD')
    
    # Service flags
    flag_hotel = db.Column(db.Boolean, default=False)
    flag_guide = db.Column(db.Boolean, default=False)  # M&G/Guide
    flag_transport = db.Column(db.Boolean, default=False)
    flag_meal = db.Column(db.Boolean, default=False)
    flag_airport = db.Column(db.Boolean, default=False)
    
    # Hotel room distribution (when flag_hotel is True)
    hotel_single_rooms = db.Column(db.Integer, default=0)
    hotel_double_rooms = db.Column(db.Integer, default=0)
    hotel_triple_rooms = db.Column(db.Integer, default=0)
    hotel_other_rooms = db.Column(db.Integer, default=0)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ItineraryRow {self.date} - {self.description[:50]}>'
    
    def calculate_row_cost(self, pax_count):
        """Calculate the actual cost for this row based on cost unit and pax"""
        if self.cost_unit == COST_UNIT_PER_PERSON:
            return (self.base_cost or 0) * pax_count
        else:  # PER_GROUP
            return self.base_cost or 0

class InboundHotel(db.Model):
    """Hotel services generated from itinerary flags"""
    __tablename__ = 'inbound_hotel'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    source_itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary_row.id'), nullable=True)  # Link to generating itinerary
    
    # Hotel details
    hotel_name = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    nights = db.Column(db.Integer, nullable=False, default=1)
    room_type = db.Column(db.String(100), nullable=True)
    meal_plan = db.Column(db.String(50), nullable=True, default='BB')  # BB, HB, FB, AI
    
    # Costing
    cost_per_night = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    # Status
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    is_locked = db.Column(db.Boolean, default=False)  # Lock when status >= CONFIRMED
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundHotel {self.hotel_name} - {self.check_in_date}>'

class InboundTransport(db.Model):
    """Transport services generated from itinerary flags"""
    __tablename__ = 'inbound_transport'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    source_itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary_row.id'), nullable=True)
    
    # Transport details
    date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # For multi-day transport services
    vehicle_type = db.Column(db.String(100), nullable=True)
    pickup_location = db.Column(db.String(200), nullable=True)
    dropoff_location = db.Column(db.String(200), nullable=True)
    pickup_time = db.Column(db.Time, nullable=True)
    is_airport_transfer = db.Column(db.Boolean, default=False)
    
    # Costing
    cost = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    # Status
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundTransport {self.vehicle_type} - {self.date}>'

class InboundMeal(db.Model):
    """Meal services generated from itinerary flags"""
    __tablename__ = 'inbound_meal'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    source_itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary_row.id'), nullable=True)
    
    # Meal details
    date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # For multi-day meal packages
    meal_type = db.Column(db.String(50), nullable=True)  # Breakfast, Lunch, Dinner
    restaurant = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    meal_time = db.Column(db.Time, nullable=True)
    
    # Costing
    cost_per_person = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    # Status
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundMeal {self.meal_type} - {self.date}>'

class InboundGuide(db.Model):
    """Guide services generated from itinerary flags (M&G)"""
    __tablename__ = 'inbound_guide'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    source_itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary_row.id'), nullable=True)
    
    # Guide details
    date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # For multi-day guide services
    guide_name = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(50), nullable=True)
    service_type = db.Column(db.String(100), nullable=True)  # Meet & Greet, Tour Guide, etc.
    duration_hours = db.Column(db.Float, nullable=True)
    meeting_point = db.Column(db.String(200), nullable=True)
    meeting_time = db.Column(db.Time, nullable=True)
    
    # Costing
    cost = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    # Status
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundGuide {self.guide_name} - {self.date}>'

class InboundCashExpense(db.Model):
    """Cash expenses for inbound tours (tips, entrance fees, misc costs)"""
    __tablename__ = 'inbound_cash_expense'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    # Expense details
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Tips, Entrance Fees, Parking, Misc
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=True)
    
    # Costing
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    is_per_person = db.Column(db.Boolean, default=False)  # True if per person, False if total
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundCashExpense {self.category} - {self.date}>'
    
    def calculate_total_cost(self, pax_count):
        """Calculate total cost based on whether it's per person or total"""
        if self.is_per_person:
            return (self.amount or 0) * pax_count
        else:
            return self.amount or 0