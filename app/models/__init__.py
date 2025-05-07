# Define constants for service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'

# Define constants for status
STATUS_REQUEST = 'REQUEST'
STATUS_BOOKED = 'BOOKED'
STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_FULFILLED = 'FULFILLED'
STATUS_COMPLETED = 'COMPLETED'

# Import models
from app.models.user import User, Agent, create_test_data
from app.models.booking import Booking, Payment, PAYMENT_NONE, PAYMENT_PARTIAL, PAYMENT_FULL
from app.models.service import ServiceItem, Document, ServiceConfirmation
from app.models.supplier import Supplier, SupplierDocument
from app.models.customer import Customer, CustomerDocument