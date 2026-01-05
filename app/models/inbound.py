from datetime import datetime, date
from app import db
from app.models import STATUS_REQUEST, STATUS_QUOTED, STATUS_RESERVED, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED

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
    request_number = db.Column(db.String(20), unique=True, nullable=False)  # Internal reference (IN-MM-####)
    document_sequence = db.Column(db.String(20), unique=True, nullable=True)  # Official sequence (INB-MM-XXXX) - generated on save
    
    # Header fields
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    no_of_days = db.Column(db.Integer, nullable=False)
    
    # Arrival/Departure details (kept for backward compatibility, use ArrivalDeparture model for multiple entries)
    arrival_point = db.Column(db.String(150), nullable=True)  # e.g., "Queen Alia Airport", "Sheikh Hussein Border"
    departure_point = db.Column(db.String(150), nullable=True)
    arrival_time = db.Column(db.Time, nullable=True)
    departure_time = db.Column(db.Time, nullable=True)
    
    # New arrival/departure fields
    visa_type = db.Column(db.String(50), nullable=True, default='NOT_INCLUDED')  # FREE, RESTRICTED, INCLUDED, NOT_INCLUDED
    arrival_driver_name = db.Column(db.String(200), nullable=True)
    meeting_assistance = db.Column(db.Boolean, default=False)  # Meeting & Assistance for departure
    departure_tax = db.Column(db.String(50), nullable=True, default='NOT_INCLUDED')  # INCLUDED, NOT_INCLUDED
    
    # Client information
    customer_type = db.Column(db.String(20), nullable=False, default='AGENCY')  # AGENCY, GROUP, COMPANY, CORPORATE
    contact_name = db.Column(db.String(100), nullable=False)
    agent_ref = db.Column(db.String(50), nullable=True)
    nationality = db.Column(db.String(50), nullable=False)
    pax = db.Column(db.Integer, nullable=False, default=1)
    special_note = db.Column(db.Text, nullable=True)
    
    # Status and tracking
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    is_saved = db.Column(db.Boolean, default=False)  # True when user explicitly saves with final sequence number
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # Link to customer
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)  # Link to normal booking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Total pricing
    total_amount = db.Column(db.Float, default=0.0)
    total_currency = db.Column(db.String(3), default='USD')
    pricing_mode = db.Column(db.String(20), default='ITEMIZED')  # ITEMIZED or LUMPSUM
    
    # Relationships
    customer = db.relationship('Customer', backref='inbound_requests', lazy=True)
    itinerary_rows = db.relationship('ItineraryRow', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_hotels = db.relationship('InboundHotel', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_transports = db.relationship('InboundTransport', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_meals = db.relationship('InboundMeal', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_guides = db.relationship('InboundGuide', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_cash_expenses = db.relationship('InboundCashExpense', backref='request', lazy=True, cascade="all, delete-orphan")
    inbound_optionals = db.relationship('InboundOptional', backref='request', lazy=True, cascade="all, delete-orphan")
    arrival_departures = db.relationship('ArrivalDeparture', backref='request', lazy=True, cascade="all, delete-orphan")
    arrival_batches = db.relationship('ArrivalBatch', backref='request', lazy=True, cascade="all, delete-orphan")
    departure_batches = db.relationship('DepartureBatch', backref='request', lazy=True, cascade="all, delete-orphan")
    quotations = db.relationship('InboundQuotation', backref='request', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('InboundDocument', backref='request', lazy=True, cascade="all, delete-orphan")
    booking = db.relationship('Booking', backref='inbound_request', lazy=True)
    
    def __repr__(self):
        return f'<InboundRequest {self.request_number}>'
    
    @classmethod
    def generate_request_number(cls, from_date=None):
        """Generate auto request number in format IN-MM-#### based on trip start month"""
        # Use provided from_date or current date
        date_to_use = from_date if from_date else datetime.now().date()
        prefix = f"IN-{date_to_use.strftime('%m')}"
        
        # Find the highest number for this month
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
    
    @classmethod
    def generate_document_sequence(cls, from_date=None):
        """Generate official document sequence in format INB-MM-XXXX based on trip start month"""
        # Use provided from_date or current date
        date_to_use = from_date if from_date else datetime.now().date()
        prefix = f"INB-{date_to_use.strftime('%m')}"
        
        # Find the highest sequence number for this month
        latest = cls.query.filter(
            cls.document_sequence.like(f"{prefix}-%")
        ).order_by(cls.document_sequence.desc()).first()
        
        if latest and latest.document_sequence:
            # Extract the number and increment
            try:
                last_num = int(latest.document_sequence.split('-')[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}-{next_num:04d}"
    
    def assign_document_sequence(self):
        """Assign document sequence if not already assigned - call this when saving"""
        if not self.document_sequence:
            self.document_sequence = InboundRequest.generate_document_sequence(self.from_date)
        return self.document_sequence
    
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
    flag_drive = db.Column(db.Boolean, default=False)
    
    # Hotel room distribution (when flag_hotel is True)
    hotel_single_rooms = db.Column(db.Integer, default=0)
    hotel_double_rooms = db.Column(db.Integer, default=0)
    hotel_triple_rooms = db.Column(db.Integer, default=0)
    hotel_other_rooms = db.Column(db.Integer, default=0)
    
    # Additional fields for itinerary display
    restaurant = db.Column(db.String(200), nullable=True)
    cash_expense = db.Column(db.Float, default=0.0)
    comment = db.Column(db.Text, nullable=True)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ItineraryRow {self.date} - {self.description[:50]}>'
    
    @property
    def itinerary_date(self):
        """Alias for date field for template compatibility"""
        return self.date
    
    @property
    def day_number(self):
        """Calculate day number from request's from_date"""
        if self.request and self.request.from_date and self.date:
            return (self.date - self.request.from_date).days + 1
        return 1
    
    def calculate_row_cost(self, pax_count):
        """Calculate the actual cost for this row based on cost unit and pax"""
        if self.cost_unit == COST_UNIT_PER_PERSON:
            return (self.base_cost or 0) * pax_count
        else:  # PER_GROUP
            return self.base_cost or 0
    
    @property
    def linked_hotel(self):
        """Get the hotel linked to this itinerary row (row-specific or global fallback)"""
        if self.request:
            # First try row-specific match
            for hotel in self.request.inbound_hotels:
                if hotel.source_itinerary_id == self.id:
                    return hotel
            # Fall back to global hotel (source_itinerary_id=None)
            for hotel in self.request.inbound_hotels:
                if hotel.source_itinerary_id is None:
                    return hotel
        return None
    
    @property
    def linked_transport(self):
        """Get the transport linked to this itinerary row (row-specific or global fallback)"""
        if self.request:
            # First try row-specific match
            for transport in self.request.inbound_transports:
                if transport.source_itinerary_id == self.id:
                    return transport
            # Fall back to global transport (source_itinerary_id=None)
            for transport in self.request.inbound_transports:
                if transport.source_itinerary_id is None:
                    return transport
        return None
    
    @property
    def linked_guide(self):
        """Get the guide linked to this itinerary row (row-specific or global fallback)"""
        if self.request:
            # First try row-specific match
            for guide in self.request.inbound_guides:
                if guide.source_itinerary_id == self.id:
                    return guide
            # Fall back to global guide (source_itinerary_id=None)
            for guide in self.request.inbound_guides:
                if guide.source_itinerary_id is None:
                    return guide
        return None
    
    @property
    def linked_meal(self):
        """Get the meal linked to this itinerary row (row-specific or global fallback)"""
        if self.request:
            # First try row-specific match
            for meal in self.request.inbound_meals:
                if meal.source_itinerary_id == self.id:
                    return meal
            # Fall back to global meal (source_itinerary_id=None)
            for meal in self.request.inbound_meals:
                if meal.source_itinerary_id is None:
                    return meal
        return None
    
    @property
    def total_service_cost(self):
        """Calculate total cost from all linked services for this itinerary row"""
        total = 0.0
        
        # Use linked properties
        if self.linked_hotel:
            total += self.linked_hotel.total_cost or 0.0
        if self.linked_transport:
            total += self.linked_transport.cost or 0.0
        if self.linked_guide:
            total += self.linked_guide.cost or 0.0
        if self.linked_meal:
            total += self.linked_meal.total_cost or 0.0
        
        # If no service costs, fall back to base_cost
        if total == 0.0:
            return self.base_cost or 0.0
        
        return total

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
    hotel_category = db.Column(db.String(100), nullable=True)  # Custom admin-defined category
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    nights = db.Column(db.Integer, nullable=False, default=1)
    room_type = db.Column(db.String(100), nullable=True)
    meal_plan = db.Column(db.String(50), nullable=True, default='BB')  # BB, HB, FB, AI
    
    # Room distribution
    single_rooms = db.Column(db.Integer, default=0)
    double_rooms = db.Column(db.Integer, default=0)
    triple_rooms = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    
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
    
    # Relationships
    rooms = db.relationship('HotelRoom', backref='hotel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InboundHotel {self.hotel_name} - {self.check_in_date}>'
    
    def get_aggregate_status(self):
        """Calculate aggregate status from room statuses"""
        if not self.rooms:
            return self.status
        
        room_statuses = [room.status for room in self.rooms]  # type: ignore
        
        # If all rooms are CONFIRMED, hotel is CONFIRMED
        if all(s == STATUS_CONFIRMED for s in room_statuses):
            return STATUS_CONFIRMED
        # If any room is RESERVED or CONFIRMED, hotel is RESERVED
        elif any(s in [STATUS_RESERVED, STATUS_CONFIRMED] for s in room_statuses):
            return STATUS_RESERVED
        # Otherwise, hotel is REQUEST
        else:
            return STATUS_REQUEST

class HotelRoom(db.Model):
    """Individual hotel rooms for room-level confirmation tracking
    
    Note: Check-in and check-out dates cascade from the parent hotel level.
    Use room.check_in_date and room.check_out_date properties to access hotel dates.
    """
    __tablename__ = 'hotel_room'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('inbound_hotel.id', ondelete='CASCADE'), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # SINGLE, DOUBLE, TRIPLE, OTHER
    room_count = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    supplier_name = db.Column(db.String(200), nullable=True)
    cost_per_room = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    notes = db.Column(db.Text, nullable=True)
    confirmation = db.Column(db.String(200), nullable=True)  # Confirmation code/number from supplier
    
    # Room details for guest assignment
    room_option = db.Column(db.String(100), nullable=True)  # e.g., Sea View, Premium, Standard
    board_basis = db.Column(db.String(20), nullable=True)  # BB, HB, FB, RO
    dietary_requirements = db.Column(db.String(200), nullable=True)  # e.g., Vegetarian, Halal
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    guest_names = db.Column(db.Text, nullable=True)  # Lead passenger/guest names for this room
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def check_in_date(self):
        """Cascade check-in date from parent hotel"""
        return self.hotel.check_in_date if self.hotel else None
    
    @property
    def check_out_date(self):
        """Cascade check-out date from parent hotel"""
        return self.hotel.check_out_date if self.hotel else None
    
    @property
    def nights(self):
        """Cascade nights from parent hotel, calculated from dates if hotel reference missing"""
        if self.hotel:
            return self.hotel.nights
        # Fallback: calculate from dates if somehow hotel reference is missing
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return None
    
    def __repr__(self):
        return f'<HotelRoom {self.room_type} x{self.room_count} - {self.status}>'

class InboundTransport(db.Model):
    """Transport services generated from itinerary flags"""
    __tablename__ = 'inbound_transport'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    source_itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary_row.id'), nullable=True)
    
    # Transport details
    date = db.Column(db.Date, nullable=False)  # From Date
    end_date = db.Column(db.Date, nullable=True)  # To Date (for multi-day transport services)
    pax = db.Column(db.Integer, default=0)  # Passenger count
    vehicle_type = db.Column(db.String(100), nullable=True)
    supplier = db.Column(db.String(200), nullable=True)  # Supplier/company name
    driver_name = db.Column(db.String(200), nullable=True)  # Driver assigned to this transport
    driver_phone = db.Column(db.String(50), nullable=True)  # Driver phone number
    pickup_location = db.Column(db.String(200), nullable=True)  # Pickup point
    dropoff_location = db.Column(db.String(200), nullable=True)  # Drop-off point
    pickup_time = db.Column(db.Time, nullable=True)
    note = db.Column(db.Text, nullable=True)  # Additional notes
    is_airport_transfer = db.Column(db.Boolean, default=False)
    is_arrival = db.Column(db.Boolean, default=False)  # Flag for arrival transfer (shows in Arrivals section of voucher)
    is_departure = db.Column(db.Boolean, default=False)  # Flag for departure transfer (shows in Departures section of voucher)
    
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
    guide_name = db.Column(db.String(100), nullable=True)  # Name
    telephone_number = db.Column(db.String(50), nullable=True)  # Telephone Number
    language = db.Column(db.String(50), nullable=True)  # Language
    national_id = db.Column(db.String(100), nullable=True)  # National ID
    tax_number = db.Column(db.String(100), nullable=True)  # Tax Number
    profile_photo = db.Column(db.String(500), nullable=True)  # Profile Photo URL/path
    service_type = db.Column(db.String(100), nullable=True)  # Meet & Greet, Tour Guide, etc.
    duration_hours = db.Column(db.Float, nullable=True)  # Keep for legacy, hide in UI
    meeting_point = db.Column(db.String(200), nullable=True)  # Keep for legacy, hide in UI
    meeting_time = db.Column(db.Time, nullable=True)
    additional_comments = db.Column(db.Text, nullable=True)  # Additional comments
    internal_comments = db.Column(db.Text, nullable=True)  # Internal comments (not printed)
    
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
    end_date = db.Column(db.Date, nullable=True)  # For multi-day expenses
    category = db.Column(db.String(100), nullable=True)  # Tips, Entrance Fees, Parking, Misc
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=True)
    driver_name = db.Column(db.String(200), nullable=True)  # Driver who holds the cash
    
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

class ArrivalDeparture(db.Model):
    """Multiple arrivals and departures per booking - batch-based (each record contains both arrival and departure for a group)"""
    __tablename__ = 'arrival_departure'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    transport_id = db.Column(db.Integer, db.ForeignKey('inbound_transport.id'), nullable=True)  # Link to transport record
    
    # Batch identification
    batch_name = db.Column(db.String(100), nullable=True)  # e.g., "Group A", "Family 1"
    pax_count = db.Column(db.Integer, nullable=True)  # Number of passengers in this batch
    
    # Arrival details
    arrival_date = db.Column(db.Date, nullable=True)  # Which itinerary day for arrival
    arrival_point = db.Column(db.String(150), nullable=True)  # e.g., "Queen Alia Airport"
    arrival_time = db.Column(db.Time, nullable=True)
    visa_status = db.Column(db.String(50), default='NOT_INCLUDED')  # VISA_FREE, RESTRICTED, INCLUDED, NOT_INCLUDED
    visa_type = db.Column(db.String(50), default='NOT_INCLUDED')  # Legacy field for backward compatibility
    arrival_driver_name = db.Column(db.String(200), nullable=True)
    
    # Departure details
    departure_date = db.Column(db.Date, nullable=True)  # Which itinerary day for departure
    departure_point = db.Column(db.String(150), nullable=True)
    departure_time = db.Column(db.Time, nullable=True)
    meet_assist = db.Column(db.Boolean, default=False)  # Meet & Assist for departure
    meeting_assistance = db.Column(db.Boolean, default=False)  # Legacy field
    representative_name = db.Column(db.String(200), nullable=True)  # Representative name for Meet & Assist
    departure_tax = db.Column(db.String(50), default='NOT_INCLUDED')  # INCLUDED, NOT_INCLUDED
    
    # Legacy fields (for backwards compatibility)
    type = db.Column(db.String(20), nullable=True)  # ARRIVAL, DEPARTURE
    date = db.Column(db.Date, nullable=True)
    time = db.Column(db.Time, nullable=True)
    point = db.Column(db.String(150), nullable=True)
    driver_name = db.Column(db.String(200), nullable=True)
    flight_number = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to transport
    transport = db.relationship('InboundTransport', backref='arrival_departure_link', foreign_keys=[transport_id])
    
    def __repr__(self):
        batch_label = self.batch_name or f'Batch {self.id}'
        return f'<ArrivalDeparture {batch_label}>'


class ArrivalBatch(db.Model):
    """Simple arrivals-only batch management"""
    __tablename__ = 'arrival_batch'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    batch_name = db.Column(db.String(100), nullable=True)
    arrival_date = db.Column(db.Date, nullable=False)
    arrival_point = db.Column(db.String(200), nullable=True)
    arrival_time = db.Column(db.Time, nullable=True)
    driver_name = db.Column(db.String(200), nullable=True)  # Keep for legacy but hide in UI
    vehicle_details = db.Column(db.String(200), nullable=True)
    pax_count = db.Column(db.Integer, default=0)
    flight_number = db.Column(db.String(50), nullable=True)
    
    # NEW FIELDS for ARD 1
    visa_status = db.Column(db.String(50), default='NOT_INCLUDED')  # VISA_FREE, RESTRICTED, INCLUDED, NOT_INCLUDED
    meet_assist = db.Column(db.Boolean, default=False)  # Meet & Assist Yes/No
    representative_name = db.Column(db.String(200), nullable=True)  # Representative Name for Meet & Assist
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ArrivalBatch {self.batch_name or self.id}>'

class DepartureBatch(db.Model):
    """Simple departures-only batch management"""
    __tablename__ = 'departure_batch'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    batch_name = db.Column(db.String(100), nullable=True)
    departure_date = db.Column(db.Date, nullable=False)
    departure_point = db.Column(db.String(200), nullable=True)
    departure_time = db.Column(db.Time, nullable=True)
    driver_name = db.Column(db.String(200), nullable=True)  # Keep for legacy but hide in UI
    vehicle_details = db.Column(db.String(200), nullable=True)
    pax_count = db.Column(db.Integer, default=0)
    flight_number = db.Column(db.String(50), nullable=True)
    meet_greet = db.Column(db.Boolean, default=False)  # Legacy field
    
    # NEW FIELDS for ARD 1
    meet_assist = db.Column(db.Boolean, default=False)  # Meet & Assist Yes/No
    representative_name = db.Column(db.String(200), nullable=True)  # Representative Name for Meet & Assist
    departure_tax = db.Column(db.String(50), default='NOT_INCLUDED')  # INCLUDED, NOT_INCLUDED
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DepartureBatch {self.batch_name or self.id}>'

class InboundOptional(db.Model):
    """Optional/Extra services purchased independently by passenger - not restricted to itinerary dates"""
    __tablename__ = 'inbound_optional'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    # Optional service details
    service_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True)  # Optional - flexible dates outside itinerary
    location = db.Column(db.String(200), nullable=True)
    supplier = db.Column(db.String(200), nullable=True)
    
    # Costing
    cost_per_person = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    # Status
    status = db.Column(db.String(20), default=STATUS_REQUEST)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundOptional {self.service_name}>'

class HotelCategory(db.Model):
    """Admin-defined hotel categories for classification"""
    __tablename__ = 'hotel_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., "5-Star", "4-Star", "Boutique", "Budget"
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)  # For custom ordering
    is_active = db.Column(db.Boolean, default=True)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HotelCategory {self.name}>'

class InboundQuotation(db.Model):
    """Quotation header for inbound requests"""
    __tablename__ = 'inbound_quotation'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    # Quotation metadata
    quotation_number = db.Column(db.String(50), unique=True, nullable=False)  # QUOT-YYYYMM-####
    version = db.Column(db.Integer, default=1)  # Version tracking for revised quotes
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, SENT, APPROVED, REJECTED
    
    # Quotation details
    valid_until = db.Column(db.Date, nullable=True)  # Quote validity date
    notes = db.Column(db.Text, nullable=True)  # Additional notes or terms
    subtotal = db.Column(db.Numeric(12, 2), default=0.00)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)  # Tax percentage
    tax_amount = db.Column(db.Numeric(12, 2), default=0.00)
    total_amount = db.Column(db.Numeric(12, 2), default=0.00)
    currency = db.Column(db.String(3), default='USD')
    
    # Unique constraint on version per request
    __table_args__ = (
        db.UniqueConstraint('request_id', 'version', name='uq_request_version'),
    )
    
    # Tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)  # When quotation was sent
    approved_at = db.Column(db.DateTime, nullable=True)  # When quotation was approved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quotation_items = db.relationship('InboundQuotationItem', backref='quotation', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('QuotationAttachment', backref='quotation', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<InboundQuotation {self.quotation_number}>'
    
    @classmethod
    def generate_quotation_number(cls):
        """Generate auto quotation number in format QUOT-YYYYMM-####"""
        now = datetime.now()
        prefix = f"QUOT-{now.strftime('%Y%m')}"
        
        # Find the highest number for current month
        latest = cls.query.filter(
            cls.quotation_number.like(f"{prefix}-%")
        ).order_by(cls.quotation_number.desc()).first()
        
        if latest:
            try:
                last_num = int(latest.quotation_number.split('-')[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}-{next_num:04d}"
    
    def calculate_total(self):
        """Calculate quotation total from line items"""
        from app.models.inbound import InboundQuotationItem
        items = InboundQuotationItem.query.filter_by(quotation_id=self.id).all()
        
        self.subtotal = sum(item.line_total or 0 for item in items)
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount
        
        return self.total_amount


class InboundQuotationItem(db.Model):
    """Individual line items in a quotation"""
    __tablename__ = 'inbound_quotation_item'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('inbound_quotation.id'), nullable=False)
    
    # Line item details
    item_order = db.Column(db.Integer, default=0)  # Display order
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    unit_price = db.Column(db.Numeric(12, 2), default=0.00)
    line_total = db.Column(db.Numeric(12, 2), default=0.00)  # quantity * unit_price
    
    # Optional categorization
    category = db.Column(db.String(50), nullable=True)  # e.g., 'Hotel', 'Transport', 'Guide'
    notes = db.Column(db.Text, nullable=True)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuotationItem {self.description[:30]}>'
    
    def calculate_line_total(self):
        """Calculate line total"""
        self.line_total = (self.quantity or 0) * (self.unit_price or 0)
        return self.line_total


class QuotationAttachment(db.Model):
    """Attachments for quotations (PDFs, images, etc.)"""
    __tablename__ = 'quotation_attachment'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('inbound_quotation.id'), nullable=False)
    
    # File details
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)  # Relative path in uploads/quotations/
    file_size = db.Column(db.Integer, nullable=True)  # File size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Metadata
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuotationAttachment {self.filename}>'


class InboundDocument(db.Model):
    """Document attachments for inbound requests (passports, confirmations, tickets, etc.)"""
    __tablename__ = 'inbound_document'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id'), nullable=False)
    
    # Document type categorization
    document_type = db.Column(db.String(50), nullable=False, default='OTHER')  # PASSPORT, VISA, TICKET, CONFIRMATION, VOUCHER, CONTRACT, OTHER
    
    # File details
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)  # Original uploaded filename
    filepath = db.Column(db.String(500), nullable=False)  # Relative path in uploads/inbound_documents/
    file_size = db.Column(db.Integer, nullable=True)  # File size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Metadata
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InboundDocument {self.document_type}: {self.original_filename}>'
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.original_filename:
            return self.original_filename.rsplit('.', 1)[-1].lower() if '.' in self.original_filename else ''
        return ''
    
    @property
    def is_image(self):
        """Check if document is an image"""
        return self.file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    @property
    def is_pdf(self):
        """Check if document is a PDF"""
        return self.file_extension == 'pdf'