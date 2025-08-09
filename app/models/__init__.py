# Define constants for service types
SERVICE_FLIGHT = 'FLIGHT'
SERVICE_HOTEL = 'HOTEL'
SERVICE_TRANSPORT = 'TRANSPORT'
SERVICE_VISA = 'VISA'
SERVICE_INSURANCE = 'INSURANCE'
SERVICE_RESTAURANT = 'RESTAURANT'  # For inbound meal services
SERVICE_GUIDE = 'GUIDE'  # For inbound guide services

# Define constants for status
STATUS_REQUEST = 'REQUEST'
STATUS_BOOKED = 'BOOKED'  # Keep for backward compatibility but no longer used in new workflow
STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_CONFIRMED = 'CONFIRMED'
STATUS_COMPLETED = 'COMPLETED'  # Keep for backward compatibility

# Import models
from app.models.user import User, Agent, create_test_data
from app.models.booking import Booking, Payment, PAYMENT_NONE, PAYMENT_PARTIAL, PAYMENT_FULL
from app.models.supplier import Supplier, SupplierService, SupplierPayment, SupplierPrepaymentLine
from app.models.customer import Customer, CustomerDocument
from app.models.service import ServiceConfirmation, ServiceItem, Document
from app.models.oauth import OAuth  # Add OAuth model

# Import finance models
from app.models.finance import (
    ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric,
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES, EXPENSE_CATEGORY_SALARIES,
    EXPENSE_CATEGORY_MARKETING, EXPENSE_CATEGORY_INSURANCE, EXPENSE_CATEGORY_SUPPLIES,
    EXPENSE_CATEGORY_TRAVEL, EXPENSE_CATEGORY_TAXES, EXPENSE_CATEGORY_SOFTWARE,
    EXPENSE_CATEGORY_TELECOM, EXPENSE_CATEGORY_MAINTENANCE, EXPENSE_CATEGORY_OTHER,
    PAYMENT_METHOD_CASH, PAYMENT_METHOD_CREDIT_CARD, PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_CHECK, PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_OTHER,
    RECURRENCE_NONE, RECURRENCE_DAILY, RECURRENCE_WEEKLY, RECURRENCE_MONTHLY,
    RECURRENCE_QUARTERLY, RECURRENCE_YEARLY
)

# Import inbound models
from app.models.inbound import (
    InboundRequest, ItineraryRow, InboundHotel, InboundTransport, 
    InboundMeal, InboundGuide, COST_UNIT_PER_PERSON, COST_UNIT_PER_GROUP,
    SERVICE_FLAG_HOTEL, SERVICE_FLAG_GUIDE, SERVICE_FLAG_TRANSPORT, 
    SERVICE_FLAG_MEAL, SERVICE_FLAG_AIRPORT
)
from app.models.inbound import (
    InboundRequest, ItineraryRow, InboundHotel, InboundTransport, 
    InboundMeal, InboundGuide, COST_UNIT_PER_PERSON, COST_UNIT_PER_GROUP,
    SERVICE_FLAG_HOTEL, SERVICE_FLAG_GUIDE, SERVICE_FLAG_TRANSPORT, 
    SERVICE_FLAG_MEAL, SERVICE_FLAG_AIRPORT
)