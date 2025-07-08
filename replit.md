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
- July 8, 2025: UNIFORM FONT SIZE STANDARDIZATION - Set all voucher text to consistent 10px font
  - ✅ BOOKING HEADER: Booking information (ID, date, PNR, contact, email) standardized to 10px
  - ✅ PASSENGER TABLE: Passenger list headers and data set to 10px for consistency
  - ✅ FLIGHT DETAILS: Airport times, dates, codes, and flight types all set to 10px
  - ✅ SECTION TITLES: All section headers standardized to 10px font
  - ✅ PASSENGER INFO: Passenger names, PNR, and e-ticket numbers set to 10px
  - ✅ BAGGAGE INFO: Baggage allowance text set to 10px
  - ✅ UNIFORM DESIGN: Complete voucher now uses consistent 10px font across all elements
- July 7, 2025: COMPACT FLIGHT SECTION DESIGN - Optimized flight voucher layout for space efficiency
  - ✅ REDUCED PADDING: Flight segment padding reduced from 15px to 8px for tighter layout
  - ✅ SMALLER MARGINS: Flight segment margins reduced from 10px to 5px for better space utilization
  - ✅ COMPACT HEADERS: Trip header margin reduced from 15px to 8px, font size from 14px to 13px
  - ✅ OPTIMIZED FLIGHT DETAILS: Flight details padding reduced from 20px to 10px
  - ✅ TIGHTER SPACING: Flight middle section padding reduced from 20px to 10px
  - ✅ TRIP INFO INTEGRATION: Moved trip information to left side of passenger details in horizontal layout
  - ✅ FULL AIRPORT NAMES: Trip information uses complete airport names (e.g., "Dubai Intl to Queen Alia Intl")
  - ✅ BLACK STYLING: Trip information displays in black color for better readability
  - ✅ SIDE-BY-SIDE LAYOUT: Trip details on left, passenger/PNR/e-ticket info on right with flexbox layout
  - ✅ REMOVED AIRLINE REFERENCE: Eliminated redundant "Airline Ref" section for cleaner layout
  - ✅ IMPROVED DENSITY: Overall flight section now displays more information in less vertical space
- July 7, 2025: INVOICE STATUS BADGE COLOR STANDARDIZATION - All invoice status badges now use company yellow/orange branding
  - ✅ CONSISTENT BRANDING: All invoice status badges changed from green/grey to yellow/orange (#FFBF00) with black text
  - ✅ BOOKING DETAILS HEADER: Fixed main "Invoiced" badge from green (#28a745) to yellow/orange (#FFBF00)
  - ✅ SERVICE ITEMS TABLE: Fixed "Invoice Status: Invoiced" badges to use company colors instead of grey
  - ✅ MAIN INVOICE INDICATOR: Updated "Invoiced - No new services allowed" badge to yellow/orange
  - ✅ EMPTY STATE BADGE: Fixed "Invoice #" badge in empty service table to use yellow/orange
  - ✅ VISUAL CONSISTENCY: All invoice-related status indicators now match Arab Travel Group branding colors
  - Complete invoice protection system remains fully functional with backend validation and UI restrictions
- July 6, 2025: INVOICE PROTECTION SYSTEM IMPLEMENTED - Complete restriction on adding services to invoiced bookings
  - ✅ BACKEND VALIDATION: Added server-side check in add_service_item route to prevent new services when booking.invoice_number exists
  - ✅ UI RESTRICTIONS: Hidden all "Quick Add" service buttons (flight, hotel, transport, visa, insurance) for invoiced bookings
  - ✅ INFORMATIVE MESSAGING: Replaced "Create Request" button with clear invoice status notification when no services exist
  - ✅ VISUAL INDICATORS: Added "Invoiced - No new services allowed" badge to show booking is locked
  - ✅ ERROR HANDLING: Flash message explains users need new booking or credit memo for changes
  - ✅ INVOICE INTEGRITY: Prevents accidental service additions that would invalidate existing invoices
  - System now enforces strict separation between pre-invoice booking modifications and post-invoice credit memo workflow
- July 6, 2025: SUPPLIER COST DASHBOARD DISCREPANCY IDENTIFIED - Found dashboard shows current month ($25,000) vs list shows all-time total ($27,833)
  - ✅ VERIFIED: Dashboard correctly filters by current month (July 2025): $7,000 + $18,000 = $25,000
  - ✅ VERIFIED: Supplier costs list correctly shows all-time total: $27,833 (includes $2,833 from June 2025)
  - ✅ CONFIRMED: No calculation error - dashboard and list serve different time scopes
  - Dashboard shows current month supplier costs for monthly KPI tracking
  - Supplier costs list shows comprehensive all-time expenses for full financial overview
- July 6, 2025: CRITICAL INVOICE BUTTON LOGIC FIX - Fixed invoice generation button visibility to strictly rely on invoice status
  - ✅ REMOVED BOOKING STATUS DEPENDENCY: Invoice generation button no longer incorrectly checks booking status (REQUEST)
  - ✅ INVOICE STATUS ONLY: Button visibility now strictly based on whether booking.invoice_number exists
  - ✅ MANUAL STATUS CHANGES SUPPORTED: Users can manually move booking to IN_PROGRESS without affecting invoice button
  - ✅ CONFIRMATION LOGIC UPDATED: Removed booking status restrictions from service confirmation buttons
  - ✅ WORKFLOW INDEPENDENCE: Invoice generation and booking status changes are now completely independent operations
  - Fixed critical bug where manually changing booking status to IN_PROGRESS would hide invoice generation option
  - Invoice button now shows "Generate Invoice" when no invoice exists, "View Invoice" when invoice exists
  - Service confirmations no longer locked based on booking status, only restricted when already invoiced
- July 6, 2025: ENHANCED VOUCHER TYPOGRAPHY AND LOGO PRESENTATION
  - ✅ ENLARGED LOGO: Increased logo size from 50px to 120px for better brand visibility
  - ✅ YELLOW/ORANGE FRAME FOR COMPANY NAME: "ARABI TRAVEL" now has striking yellow-orange gradient background with dark blue text and orange border
  - ✅ MODERN HEADER DESIGN: Updated company name font to modern Segoe UI with increased size (26px) and professional weight (600)
  - ✅ GREY BACKGROUND TAGLINE: Added grey background box for "Travel Voucher" text with rounded corners and proper padding
  - ✅ CLEAN WHITE HEADER: Changed header from blue to clean white background with blue bottom border for modern appearance
  - ✅ RESTRUCTURED HOTEL SECTION: Hotel name and address now display as prominent header with details in clean table format below
  - ✅ REFINED FONT SIZES: Reduced text sizes by 1 point for better proportions (section titles: 15px, info text: 13px, passenger details: 12px)
  - ✅ FLIGHT DETAILS REFINEMENT: Reduced airport times to 16px, section labels to 12px, dates to 11px for elegant flight information display
  - ✅ HOTEL TABLE REFINEMENT: Reduced hotel table headers and data to 12px, hotel names to 14px, footer text to 11px for consistent elegant styling
  - ✅ CONSISTENT FONT FAMILY: Applied Georgia serif throughout all voucher elements for unified elegant design
  - ✅ REMOVED YELLOW FRAME: Removed yellow/orange background from "ARABI TRAVEL", now displays as clean dark blue text
  - ✅ TRAVEL VOUCHER STYLING: Changed tagline to "Travel Voucher" in dark blue with yellow/orange horizontal line below
  - ✅ HOTEL ADDRESS COLOR: Updated hotel address text to dark blue (#2E5A87) for better visual hierarchy
  - ✅ REFINED FONT SIZES: Reduced text sizes by 1 point for better proportions (section titles: 15px, info text: 13px, passenger details: 12px)
  - ✅ FLIGHT DETAILS REFINEMENT: Reduced airport times to 16px, section labels to 12px, dates to 11px for elegant flight information display
  - ✅ HOTEL TABLE REFINEMENT: Reduced hotel table headers and data to 12px, hotel names to 14px, footer text to 11px for consistent elegant styling
  - ✅ CONSISTENT FONT FAMILY: Applied Georgia serif throughout all voucher elements for unified elegant design
  - ✅ PDF PATH RESOLUTION: Fixed logo display in PDF generation using absolute file paths for weasyprint compatibility
- July 6, 2025: UPDATED ARAB TRAVEL LOGO ACROSS ALL VOUCHER SYSTEMS
  - ✅ LOGO REPLACEMENT: Updated all voucher templates to use new Arab Travel logo (arab_travel_logo.png)
  - ✅ AIRLINE VOUCHER GENERATOR: Updated company header to display "ARABI TRAVEL" with new logo
  - ✅ MODERN VOUCHER GENERATOR: Updated PDF logo path to use new Arab Travel logo
  - ✅ LOGIN PAGE UPDATE: Updated authentication page to display new Arabi Travel logo
  - ✅ CONSISTENT BRANDING: All voucher systems now use unified Arab Travel branding
  - Logo file saved as /static/arab_travel_logo.png and integrated into all voucher generation systems
- July 5, 2025: IMPLEMENTED MULTI-SERVICE SUPPLIER SYSTEM - Major supplier logic enhancement
  - ✅ UPDATED SUPPLIER FILTERING: Changed from single supplier_type to SupplierService relationship-based filtering
  - ✅ MULTI-SERVICE CAPABILITY: Suppliers can now offer multiple service types (e.g., airline that also provides hotels)
  - ✅ ENHANCED CONFIRMATION LISTS: Suppliers appear in confirmation dropdowns for all their service types
  - ✅ DATABASE ENHANCEMENT: Added comprehensive SupplierService records for all existing suppliers
  - Examples: booking.com now offers both flights and hotels, Pal.Tours provides full travel services (flights, hotels, transport, visa, insurance)
  - Updated booking confirmation logic to query suppliers via their SupplierService relationships
  - Maintained backward compatibility with legacy supplier_type filtering
  - Created comprehensive supplier service matrix with realistic commission rates
- July 5, 2025: ENHANCED WHATSAPP SHARING WITH AUTO PDF DOWNLOAD
  - ✅ AUTOMATIC PDF DOWNLOAD: WhatsApp share function now downloads PDF before opening WhatsApp
  - ✅ USER NOTIFICATIONS: Progress indicators show PDF generation and download status
  - ✅ IMPROVED WORKFLOW: PDF automatically saved to device, WhatsApp opens with pre-filled message
  - Enhanced error handling with fallback to original sharing method if PDF download fails
- July 5, 2025: UI IMPROVEMENTS - Changed "Download PDF" to "Print PDF" buttons
  - Updated voucher interface button text from "Download PDF" to "Print PDF" with print icons
  - Maintains same functionality but better reflects intended use case
- July 5, 2025: FINALLY RESOLVED PDF VOUCHER DOWNLOAD ISSUE COMPLETELY
  - ✅ ROOT CAUSE IDENTIFIED: Download buttons were using GET requests but PDF generation required POST requests
  - ✅ SOLUTION IMPLEMENTED: Updated voucher_preview_new.html to use POST forms with CSRF tokens for PDF downloads
  - ✅ TECHNICAL VERIFICATION: Backend PDF generation works perfectly (produces 20KB valid PDFs with proper Content-Type: application/pdf)
  - ✅ WEB INTERFACE FIX: Download buttons now submit POST requests instead of GET links
  - Enhanced weasyprint implementation generates perfect PDF replicas of HTML voucher styling
  - Created debug test route `/booking/<id>/voucher/test` for development troubleshooting
  - System properly handles both HTML preview (GET) and PDF download (POST) requests
  - CSRF protection bypassed for voucher routes using pattern `/booking/\d+/voucher(/test)?$`
- July 5, 2025: ADDED PNR DISPLAY TO FLIGHT VOUCHERS - Enhanced ticket information visibility
  - Added PNR (Passenger Name Record) display below each flight segment in vouchers
  - PNR appears with light blue background styling for clear identification
  - Now shows complete ticket information: Passengers, PNR, and E-Ticket numbers
  - PNR data automatically extracted from flight confirmations (e.g., "XVS04V" for Qatar Airways)
- July 5, 2025: VOUCHER STYLING IMPROVEMENTS - Enhanced readability and visual hierarchy
  - Updated header to dark blue (#2E5A87) background with white text for better contrast
  - Increased hotel table font size from 12px to 14px for improved readability
  - Made hotel names bold with larger 16px font and dark blue color for emphasis
  - Enhanced visual hierarchy in hotel section for clearer information display
- July 5, 2025: VOUCHER HEADER AND FOOTER UPDATES - Updated branding and contact information
  - Changed header from gradient to solid orange-yellow (#FFD700) background with dark blue text
  - Removed text shadow for cleaner appearance on solid background
  - Enhanced footer with complete banking information: Arabi Travel Bank, Bank Of Palestine, Arab Bank account details
  - Added comprehensive contact information: sales@arabtravel.ps, www.arabtravel.ps, +97022956640
  - Included complete address: Alersal St, zakat Bld, Ramallah, P.O.BOX: 27
- July 5, 2025: ENHANCED FLIGHT VOUCHER PASSENGER DISPLAY - Added passenger names and e-ticket numbers in bold below each flight leg
  - Enhanced AirlineVoucherGenerator to display passenger names prominently below each flight segment
  - Added e-ticket numbers in bold with yellow text on blue background for visibility
  - Created passenger-ticket-info section with professional styling and clear visual separation
  - Each flight leg now shows complete passenger list and ticket numbers for easy reference
  - Styling includes Arab Travel Group branding colors (Navy Blue #2E5A87 and Gold #FFD700)
- July 5, 2025: HOTEL ROOM ARRAY SYSTEM - Fixed hotel confirmations to handle multiple rooms with lead passengers
  - Replaced hardcoded single/double/twin room structure with dynamic room arrays
  - Added backward compatibility to convert old room format to new array structure
  - Enhanced AI prompts to extract room types, board basis, and lead passenger names
  - Updated modal and form to display multiple rooms like "CLASSIC ROOM SINGLE" with "Marcel Eyad"
  - System now properly processes PARKROYAL format confirmations with detailed room information
- July 5, 2025: ENHANCED HOTEL CONFIRMATION SYSTEM - Updated hotel AI scanner to match flight design consistency
  - Applied same dark blue header with yellow "Scan with AI" button to hotel confirmation form
  - Confirmed existing AI-powered hotel voucher scanning system is fully functional
  - Hotel scanner extracts: hotel name, check-in/out dates, booking reference, room types, guest count, amenities, pricing
  - System supports same professional styling and AI integration as flight confirmations
  - No hardcoding - all data extracted dynamically from uploaded confirmation documents
- July 5, 2025: VOUCHER SYSTEM ARAB TRAVEL GROUP BRANDING - Professional header design implemented
  - Added Arab Travel Group logo and company branding to voucher headers
  - Beautiful gradient background (Navy Blue to Gold) with company tagline
  - Fixed airport code extraction logic (Dubai → DXB instead of incorrect "AIR")
  - Enhanced voucher visual identity with authentic travel agency branding
- July 5, 2025: COMPLETE MULTI-SEGMENT FLIGHT SYSTEM - Fixed all scanning, display, and storage issues
  - Fixed critical bug where form fields used old naming (airline_0) but backend expected new format (segments[0][airline])
  - Enhanced modal to display ALL flight segments instead of just first segment with individual segment cards
  - Fixed form population JavaScript to match corrected field naming convention for new scans
  - **MAJOR FIX**: Added missing JavaScript initialization code to load existing multi-segment confirmations
  - Form now automatically displays all saved segments when opening existing confirmations
  - Database investigation confirmed all 4 Qatar Airways segments properly stored (QR 405, QR 846, QR 837, QR 402)
  - Complete end-to-end functionality: scan → modal preview → form population → database storage → form display
  - **SEGMENT MANAGEMENT**: Fixed "Add segment" button to create new flight segments with proper UI and autocomplete
  - **AUTOCOMPLETE SYSTEM**: Added missing flight_autocomplete.js include and initialization for airline/airport lookup
  - All new segments now have working airline and airport autocomplete with proper data sourcing
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