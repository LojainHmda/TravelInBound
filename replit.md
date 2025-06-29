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