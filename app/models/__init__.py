# Define constants for service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

# Define constants for status - new status flow
STATUS_PLANNED = 'PLANNED'         # Itinerary shared with customer
STATUS_PREPAID = 'PREPAID'         # Payment received
STATUS_QUEUED = 'QUEUED'           # Waiting to be processed
STATUS_PROCESSING = 'PROCESSING'   # Confirmation in progress
STATUS_CONFIRMED = 'CONFIRMED'     # All components booked
STATUS_CLOSED = 'CLOSED'           # Manually closed

# Legacy status constants (keeping for backward compatibility)
STATUS_REQUEST = 'REQUEST'     # Initial booking request state (now PLANNED)
STATUS_BOOKED = 'BOOKED'       # Confirmed booking (now PREPAID)
STATUS_IN_PROGRESS = 'IN_PROGRESS'  # Operations started (now PROCESSING)
STATUS_FULFILLED = 'FULFILLED'     # Services delivered (now CONFIRMED)
STATUS_COMPLETED = 'COMPLETED'      # All services fulfilled (now CONFIRMED)

# Import models
from app.models.user import User, Agent, create_test_data
from app.models.booking import Booking, Payment, PAYMENT_NONE, PAYMENT_PARTIAL, PAYMENT_FULL

# Import supplier and customer models
from app.models.supplier import Supplier, SupplierService, SupplierPayment
from app.models.customer import Customer, CustomerDocument

# Import service models
from app.models.service import ServiceConfirmation, ServiceItem, Document
from app.models.service import (
    STATUS_PLANNED, STATUS_PREPAID, STATUS_QUEUED, 
    STATUS_PROCESSING, STATUS_CONFIRMED, STATUS_CLOSED,
    STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_FULFILLED, STATUS_COMPLETED
)
from app.models.service import SERVICE_FLIGHT, SERVICE_HOTEL, SERVICE_TRANSPORT, SERVICE_VISA, SERVICE_INSURANCE