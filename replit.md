# TravelBookPro - Comprehensive Travel Management System

## Overview

TravelBookPro is a Flask-based web application designed for travel agencies to manage booking operations, customer requests, service confirmations, and financial operations. The system provides a complete workflow from initial customer requests through service confirmations and financial tracking.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **Database**: PostgreSQL 16 with SQLAlchemy ORM
- **Authentication**: Flask-Login with OAuth support (Replit Auth integration)
- **Forms**: Flask-WTF for form handling and CSRF protection
- **Deployment**: Gunicorn WSGI server on Replit with autoscale deployment

### Frontend Architecture
- **Template Engine**: Jinja2 templates
- **Styling**: Bootstrap 5 with custom CSS
- **JavaScript**: Vanilla JS for interactive features
- **Icons**: FontAwesome 6
- **UI Components**: Bootstrap modals, tabs, and responsive design

### Database Design
- **ORM**: SQLAlchemy with declarative base model
- **Migration Strategy**: Direct SQL migrations for schema updates
- **Connection Pooling**: Configured with pool recycling and pre-ping

## Key Components

### Core Models
1. **User Management**: User, Agent, OAuth models for authentication
2. **Booking System**: Booking, ServiceItem, Document models for travel requests
3. **Customer Management**: Customer, CustomerDocument models
4. **Supplier Management**: Supplier, SupplierService, SupplierPayment, SupplierPrepaymentLine models
5. **Financial Tracking**: Payment, ExpenseCategory, Expense, FinancialMetric models
6. **Service Confirmations**: ServiceConfirmation model linking services to suppliers

### Business Logic
- **Booking Workflow**: REQUEST → BOOKED → IN-PROGRESS → CONFIRMED status progression
- **Service Types**: Flight, Hotel, Transport, Visa, Insurance
- **Financial Operations**: Invoice generation, payment tracking, supplier cost management
- **Document Management**: File uploads for tickets, confirmations, and other documents

### Blueprint Structure
- **Main Routes**: Core application routes and dashboard
- **Booking Blueprint**: Booking management operations
- **Voucher Blueprint**: Travel document generation
- **Auth Blueprint**: User authentication and authorization
- **Finance Module**: Expense tracking and financial reporting

## Data Flow

### Booking Creation Process
1. Customer request initiated with unique reference number
2. Service items added to booking (flights, hotels, etc.)
3. Documents uploaded for each service
4. Supplier confirmations recorded with cost information
5. Invoice generated and payment tracked
6. Service status updated through workflow stages

### Financial Integration
1. Service confirmations create supplier payment records
2. Prepayment lines link payments to specific bookings
3. Expense tracking for operational costs
4. Financial metrics calculation for reporting

### Document Processing
- File upload handling for various document types
- Ticket analysis functionality for automated data extraction
- Document categorization (TICKET, CONFIRMATION, INVOICE, etc.)

## External Dependencies

### Python Packages
- **Flask**: Web framework and extensions
- **SQLAlchemy**: Database ORM
- **psycopg2-binary**: PostgreSQL adapter
- **Flask-Dance**: OAuth integration
- **OpenAI**: AI-powered chat functionality
- **PDF processing**: pdf2image, pypdf2, pillow for document handling
- **Reporting**: reportlab for PDF generation
- **Communication**: twilio for SMS integration

### Frontend Libraries
- **Bootstrap 5**: UI framework
- **FontAwesome**: Icon library
- **Chart.js**: Data visualization (referenced in performance monitoring)

### Development Tools
- **Nix packages**: System-level dependencies including PostgreSQL, image processing libraries
- **Python tools**: Various development and production packages

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with PostgreSQL 16
- **Process Management**: Gunicorn with auto-reload for development
- **Port Configuration**: Main app on port 5000, performance monitoring on port 9000
- **Environment**: Autoscale deployment target

### Database Configuration
- **Connection**: Environment-based DATABASE_URL configuration
- **Pool Settings**: Connection recycling and health checks
- **Schema Management**: Direct SQL migrations for production updates

### Development Workflow
- **Hot Reload**: Gunicorn with reload flag for development
- **Performance Monitoring**: Dedicated monitoring server on port 9000
- **Error Handling**: Comprehensive logging and error tracking

## Recent Changes
- July 5, 2025: ENHANCED MULTI-SEGMENT FLIGHT SCANNING - Fixed JavaScript errors and improved AI extraction
  - Increased OpenAI token limit from 2000 to 3000 tokens for complete multi-segment extraction
  - Fixed JavaScript syntax errors in populateCommonFields function with proper try-catch blocks
  - Made populateFlightDetailsFromTicket globally accessible to resolve modal function calling issues
  - Enhanced logging to show successful extraction of all 4 Qatar Airways segments (QR 405, QR 846, QR 837, QR 402)
  - Fixed form field mapping to properly populate airline, flight number, airports, dates, and times
  - Added automatic UI creation for additional flight segments beyond the first segment
  - Enhanced autocomplete reinitialization for dynamically added fields
  - Fixed booking reference and passenger name population from AI extraction
- July 5, 2025: CRITICAL WORKFLOW FIXES - Resolved auto-invoicing bug and status cascade issues
  - Fixed critical bug where service items were automatically marked as "INVOICED" when booking moved to IN_PROGRESS
  - Removed automatic is_invoiced=True setting from cascade_booking_status_to_service_items function
  - Fixed confirm button visibility logic throughout booking details and dashboard
  - Updated service status workflow to properly display: REQUEST → IN_PROGRESS → CONFIRMED → INVOICED
  - Enhanced error logging for multi-segment flight confirmation debugging
- July 5, 2025: CRITICAL FIX - Resolved auto-invoicing bug and confirmation editing restrictions
  - Fixed services defaulting to "INVOICED" status when they should only be marked as invoiced when explicitly generating an invoice
  - Removed automatic is_invoiced=True setting in service creation logic
  - Updated confirmation button UI to show "View" for invoiced services vs "Confirm" for editable services
  - Enhanced multi-segment flight scanning for complex Qatar Airways tickets with connecting flights through Doha hub
  - Successfully tested with Qatar Airways round-trip ticket: 4 segments correctly extracted (QR 405, QR 846, QR 837, QR 402)
  - Improved OpenAI prompts to better recognize airline hub routing patterns and layover connections
  - Enhanced form filling logic for complex multi-city and connecting flight patterns
- July 3, 2025: Successfully implemented and tested multi-segment flight confirmation system
  - Enhanced flight confirmation interface with prominent styling and visual indicators
  - Added multi-segment flight container with clear visual borders and segment separation
  - Successfully processed round-trip flight with 2 segments (Etihad Airways EY 592 and EY 418)
  - System correctly captured passenger details, PNR, and flight times for both segments
  - Confirmed multi-segment data storage in JSON format within confirmation documents
- July 3, 2025: Added multi-segment flight scanning to confirmation form
  - Enhanced OpenAI helper to detect return trips and multi-city flights from single document upload
  - Updated flight confirmation form with AI scanning button for automatic form population
  - Added intelligent flight type detection (one-way, round-trip, multi-city) based on segment analysis
  - Created smart form filling that populates multiple flight segments automatically
  - Added backend endpoint `/booking/scan-flight-document` with CSRF exemption for secure document upload
  - Enhanced scanning modal with progress indicators and error handling
  - Updated voucher passenger display to show all passengers from all flight segments (fixed mixing issue)
- July 3, 2025: Successfully fixed multi-segment flight data extraction and voucher display
  - Resolved flight data mixing between different confirmation documents (Qatar Airways QR 405 and Etihad Airways EY 592)
  - Enhanced PNR data transfer from document level to segment level for multi-segment flights
  - Fixed airport information display in voucher tables with complete departure/arrival data
  - Separated single-flight and multi-segment flight processing to prevent cross-contamination
  - Server restart resolved caching issues - voucher now displays authentic data from both flight confirmations
  - Both flights show complete details: QR 405 (Amman→Doha, 02:20) and EY 592 (Queen Alia→Abu Dhabi, 11:35)
- December 30, 2025: Implemented professional airline-style voucher system
  - Created new AirlineVoucherGenerator service matching professional airline industry standards
  - Added passenger list display with names and types (Adult/Child) prominently at top
  - Implemented PNR/booking reference display in header section
  - Added E-ticket numbers in flight information table format
  - Enhanced flight details with professional table layout including aircraft type, seat assignments, baggage allowance
  - Integrated hotel confirmation numbers and detailed amenities grid
  - Added important travel information section with airline industry guidelines
  - Updated voucher routes to use new HTML-based generation instead of PDF
  - Fixed dashboard status constant mismatch (IN-PROGRESS to IN_PROGRESS) to match database
  - Removed duplicate dashboard function that was causing booking count display issues
- June 29, 2025: Added hotel address and phone number display to vouchers
  - Enhanced ModernVoucherGenerator to include hotel contact information in voucher hotel section
  - Added _get_hotel_contact_info method to look up addresses and phone numbers from CSV database
  - Hotel vouchers now display full address and phone number below hotel details when available
  - Integrated with existing hotel database containing 354 hotels with authentic contact information
- June 29, 2025: Enhanced hotel autocomplete system with comprehensive database
  - Processed CSV file with 354 hotels from multiple destinations (Turkey, Dubai, UAE)
  - Added hotels from Istanbul, Antalya, Bodrum, Kemer, Alanya, Marmaris, Dubai and other locations
  - Enhanced hotel_autocomplete_data.js with luxury resorts, boutique hotels, and international chains
  - Updated city list to include Turkish and UAE destinations for better location coverage
  - Improved hotel dropdown with authentic hotel names from operational database
- June 29, 2025: Made phone number mandatory with unique constraint
  - Updated Customer model to require phone field (nullable=False, unique=True)
  - Enhanced CustomerForm validation to make phone field required
  - Added database constraint validation with proper error handling for duplicate phone numbers
  - Applied database migration to resolve existing duplicate phone numbers
  - Added unique constraint (uq_customer_phone) to customer table phone column
- June 29, 2025: Enhanced passport scanning to support PDF files
  - Updated PassportScanner service to handle both image and PDF formats
  - Added PDF to image conversion using pdf2image library for document processing
  - Enhanced file type detection based on filename extension and file headers
  - Updated customer creation interface to accept PDF files (accept="image/*,application/pdf")
  - Modified UI text and button labels to reflect support for both images and PDFs
  - Added /customers/api/scan-passport to CSRF exemptions for proper API functionality
- June 29, 2025: Fixed voucher table alignment and font sizing issues
  - Adjusted table column widths to prevent text overlap (Service: 1.0", Description: 2.0", Dates: 1.5", Status: 1.0", Amount: 0.8")
  - Reduced font size from 8pt to 7pt for more compact display
  - Fixed hotel table to use actual confirmation data from Jumeirah Beach Hotel, Dubai
  - Applied consistent table styling across flight, hotel, and payment sections
  - Improved padding and spacing for better text alignment
  - Removed duplicate "Flight Details" header to eliminate redundancy
- June 28, 2025: Fixed database model conflicts and implemented comprehensive voucher system
  - Resolved table redefinition errors by removing duplicate model definitions from models.py
  - Properly imported User, Agent, Customer, and Booking models from dedicated app.models files
  - Implemented ModernVoucherGenerator with clean design matching user concept
  - Added blue headers and professional flight table layout for vouchers
  - Fixed initialization order issues in voucher generator color definitions
  - Cleaned up codebase by removing all duplicate voucher generators (voucher_generator.py, clean_voucher_generator.py, simple_voucher_generator.py)
  - Updated voucher format to use actual confirmation data (Emirates, EK905, Dubai→Queen Alia airports)
  - Replaced tabular flight layout with compact form-style design
  - Removed duplicate headers and streamlined flight information display
  - Enhanced flight data extraction to pull from real confirmation details instead of placeholder data
  - Removed duplicate customer section from voucher layout
  - Added passenger names and e-ticket information display
  - Integrated Arab Travel Group logo with proper header alignment
  - Fixed overlapping text issues in flight details section
  - Improved content width alignment for professional appearance
- June 26, 2025: Added AI-powered passport scanning for customer creation
  - Implemented PassportScanner service using OpenAI GPT-4o vision API
  - Created `/customers/api/scan-passport` endpoint for passport image processing
  - Enhanced customer creation form with passport scanning modal interface
  - Automatic form population with extracted passport data (name, passport number, nationality, dates)
  - Uses same OpenAI approach for document analysis as existing ticket scanning

## Changelog
- June 26, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.