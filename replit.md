# TravelBookPro - Comprehensive Travel Management System

## Overview
TravelBookPro is a Flask-based web application designed for travel agencies to streamline booking operations, manage customer requests, confirm services, and track financial operations. It aims to enhance productivity and customer satisfaction by providing an efficient solution for the entire travel management workflow, from inquiry to financial tracking.

## User Preferences
Preferred communication style: Simple, everyday language.
**IMPORTANT**: NO WIZARD WORKFLOW - Wizard routes completely disabled per user request. Users create new requests via `/inbound/new` which goes directly to the unified view/edit page.

## System Architecture

### Backend
- **Framework**: Flask (Python 3.11)
- **Database**: PostgreSQL 16 with SQLAlchemy ORM
- **Authentication**: Flask-Login with OAuth support (Replit Auth)
- **Forms**: Flask-WTF for form handling and CSRF protection
- **Deployment**: Gunicorn WSGI server on Replit

### Frontend
- **Template Engine**: Jinja2
- **Styling**: Bootstrap 5 with custom CSS
- **JavaScript**: Vanilla JS for interactive features, with a focus on modern ES6 class structures and event delegation for maintainability.
- **Icons**: FontAwesome 6
- **UI Components**: Bootstrap modals, tabs, and responsive design.

### Database Design
- **ORM**: SQLAlchemy with declarative base model.
- **Migration Strategy**: Direct SQL migrations.
- **Connection Pooling**: Configured with pool recycling and pre-ping.

### Key Features & Design Patterns
- **Core Models**: User, Agent, OAuth, Booking, ServiceItem, Document, Customer, Supplier, Payment, Expense, FinancialMetric, ServiceConfirmation.
- **Booking Workflow**: Status progression (REQUEST → BOOKED → IN-PROGRESS → CONFIRMED).
- **Service Types**: Flight, Hotel, Transport, Visa, Insurance, Restaurant, Guide.
- **Financial Operations**: Invoice generation (professional "Windows of Jordan" template with banking details), payment tracking, supplier cost management.
- **Document Management**: File uploads, AI-powered ticket/voucher analysis, document categorization.
- **Modular Design**: Blueprint structure for main routes, booking, voucher generation, authentication, and finance.
- **UI/UX Decisions**:
    - Consistent branding with yellow/orange color scheme for status badges and company logo.
    - Clean, modern typography (Segoe UI, Georgia serif) for readability, especially in vouchers.
    - Compact and horizontal layouts for headers and footers to optimize space.
    - Dynamic UI elements for multi-segment flights and multi-room hotel bookings.
    - **Hub-Style Landing Page**: Modern tile-based home page with large, clickable cards for quick navigation to key features (New Itinerary, Bookings, Run-Down, Customers, Finance, Suppliers, Documents, Reports). Features floating action button (FAB) and quick stats bar.
    - **Wizard Workflow for New Itineraries**: 3-step service-based wizard fully integrated with the inbound tour operator system:
        1. **Arrival & Departure**: Capture arrival/departure points (border/airport), dates, times, contact name (with Select2 customer autocomplete dropdown), customer type, nationality, PAX, and special notes. Automatically calculates tour duration. **Customer Autocomplete**: Select2-powered AJAX search integrated with customer database for quick customer selection.
        2. **Add Services**: Service-based wizard where ALL service types (hotels, transport, meals, guides) are added in one page using dynamic JavaScript cards with FROM/TO date logic that auto-generates itinerary rows. **Auto-filled Dates**: All service date fields automatically default to arrival/departure dates for improved UX:
            - **Hotel Service**: Check-in/check-out dates (default to arrival/departure dates) with room distribution (single, double, triple, other rooms). **Room Details Table**: Auto-generated table appears AFTER room distribution with rows matching distribution counts. Table columns include room type (pre-selected based on category), board basis (Room Only/BB/HB/FB/AI), adults (with smart defaults), children, and lead passenger name. Auto-generates itinerary rows for each NIGHT with inherited rooming across all nights. Example: Check-in Jan 1 → Check-out Jan 4 creates 3 rows (Jan 1, 2, 3) with same rooming.
            - **Transport Service**: Single date (defaults to arrival date) with pickup/dropoff locations and vehicle type. Creates itinerary row for that date with transport flag.
            - **Meal Service**: FROM/TO date range (defaults to arrival/departure dates) with meal type and restaurant selection. Creates itinerary rows for each day in range with meal flag. Example: FROM Dec 25 → TO Dec 27 creates 3 rows (Dec 25, 26, 27).
            - **Guide Service**: FROM/TO date range (defaults to arrival/departure dates) with service type and language. Creates itinerary rows for each day in range with guide flag.
            - Services on the same date are automatically MERGED into a single itinerary row with multiple service flags.
            - Form field naming convention: `services[INDEX][FIELD_NAME]` for dynamic service addition/removal; nested room fields use `services[INDEX][rooms][ROOM_INDEX][FIELD_NAME]` pattern.
            - **Robust Parsing**: Backend parsing logic handles both simple 2-level fields and complex 3-level nested room structures, ensuring data integrity throughout wizard flow.
        3. **Review & Create**: Summary page showing all tour information and color-coded service cards (blue=hotel, purple=transport, yellow=meal, green=guide) before final submission.
    - Progressive wizard UI with 3-step indicators (purple gradient for active, green for completed), session-based data persistence, safe numeric parsing with validation, hotel date validation (check-out must be after check-in), service merging logic, empty-service validation, and proper transaction rollback on errors.
    - Professional top navigation with a "Die Menu" dropdown system and mobile responsiveness.
    - Interactive service details in Run-Down Plan dashboard with hover tooltips and clickable modals.
- **AI Integration**: AI-powered scanning for document data extraction (e.g., flight details, hotel details, passport information, ticket numbers, passenger types, PNRs) with sequential mapping and intelligent data population into forms.
- **Voucher Generation**: Professional, airline-style PDF voucher generation with detailed layouts for flights, hotels, and comprehensive passenger/ticket information, ensuring accurate chronological ordering of services. Creative PDF timeline voucher generation for tour itineraries with dual (vertical/horizontal) layout options and SVG icons.
- **Inbound Tour Operator System**: Itinerary-first booking approach with new models (InboundRequest, ItineraryRow, etc.), service flag system for auto-generation of linked service records, dynamic pricing, and a unified edit interface for master details and itinerary.
- **Hotel Room Distribution**: Enhanced hotel service with room type distribution, board basis selection, and dietary requirements functionality.
- **Daily Operations Dashboard**: Comprehensive daily operational dashboard for inbound travel management, showing services organized by date with advanced filtering and export functionalities (Excel, PDF).

## External Dependencies

- **Database**: PostgreSQL
- **AI/ML**: OpenAI (for AI-powered document scanning and data extraction)
- **PDF Processing**: `pdf2image`, `pypdf2`, `pillow`, `reportlab`, `weasyprint` (for PDF generation and image conversion)
- **Communication**: Twilio (for SMS integration)
- **Frontend Libraries**: Bootstrap 5, FontAwesome, Chart.js (for data visualization), Select2 (for enhanced autocomplete dropdowns)
- **OAuth**: Replit Auth (via Flask-Dance)

## Recent Enhancements (October 2025)

### Wizard Improvements (Latest - October 2025)

1. **Contact & Group Information - FIRST SECTION (Step 1)**: 
   - **Section Order**: Contact & Group Information appears FIRST, before Arrival/Departure sections
   - **Customer Dropdown**: Select2-powered autocomplete with clean, modern styling
   - Searches customer database via AJAX (`/customers/api/search` endpoint)
   - Placeholder text: "Search for customer..."
   - Shows customer name, email, and company in dropdown results
   - **Create New Customer**: Click "Create New Customer" link to open modal
   - Modal form with fields: First Name, Last Name, Email, Phone, Company, Nationality, Customer Type
   - AJAX submission to `/customers/api/create` endpoint
   - Newly created customer auto-selected in dropdown

2. **Auto-filled Service Dates (Step 2)**: 
   - All service date fields intelligently default to itinerary arrival/departure dates:
     - Hotel check-in/out → arrival/departure dates
     - Transport date → arrival date
     - Meal from/to dates → arrival/departure dates (date range, not single date)
     - Guide from/to dates → arrival/departure dates

3. **Dynamic Hotel Room Cards (Step 2)**: 
   - Card-based room management with add/remove buttons (matching confirm_hotel.js pattern)
   - Each card includes:
     - Room Type dropdown (Single, Double, Twin, Triple, Family, Suite, Deluxe, etc.)
     - Board Basis dropdown (Room Only, BB, HB, FB, AI, Ultra AI)
     - Number inputs for Adults and Children (with smart defaults)
     - Text input for Lead Passenger name
   - Auto-adds first room when hotel service is created
   - Dynamic add/remove functionality for multiple rooms
   - Form naming: `services[INDEX][rooms][ROOM_INDEX][FIELD_NAME]`

4. **Live Itinerary Preview Grid (Step 2)**:
   - Dynamic preview table that updates in real-time
   - Shows all dates covered by services with day numbers
   - Color-coded service flag icons:
     - Hotel (blue): 🏨
     - Transport (purple): 🚌
     - Meal (orange): 🍽️
     - Guide (green): 👔
   - Updates automatically when:
     - Services are added/removed
     - Date fields are edited via change event listeners
   - Services on same date merge into single row
   - Hidden when no services, visible when services exist

5. **Meal Service Date Range (Step 2)**:
   - FROM/TO date range (not single date)
   - Both fields default to arrival/departure dates
   - Backend creates one itinerary row per day in range
   - Example: FROM Jan 1 → TO Jan 4 creates 4 rows (Jan 1, 2, 3, 4)

6. **Robust Session Parsing**: 
   - Backend parsing handles complex nested data structures:
     - Simple fields: `services[INDEX][FIELD]`
     - Nested room fields: `services[INDEX][rooms][ROOM_INDEX][FIELD]`
   - Ensures data integrity across wizard steps
   - Safe numeric parsing with validation

### Expense Report Export (Latest - October 2025)

1. **Excel Expense Report Export**:
   - Matches "Windows of Jordan Actual Expense Sheet" template format
   - Header: Company name, title, file number, date, reference, PAX count
   - Table columns: Item | Cost PP | Pax | Total
   - Auto-calculates totals using Excel formulas (=D*E)
   - Subtotal, Advance Payment, and Final Total rows
   - Signature lines for Authorization and Guide/Driver
   - Route: `/inbound/api/<request_id>/export-expense-report`
   - Download button in itinerary view with green gradient styling
   - Pulls expense data from InboundCashExpense model
   - Professional formatting with yellow header fills and bold fonts