# TravelBookPro - Comprehensive Travel Management System

## Overview
TravelBookPro is a Flask-based web application for travel agencies, designed to streamline booking operations, manage customer requests, confirm services, and track financial operations. It aims to enhance productivity and customer satisfaction by providing an efficient solution for the entire travel management workflow, from inquiry to financial tracking. The project's ambition is to be a comprehensive platform for inbound tour operators, offering AI-powered assistance and robust financial tools.

## User Preferences
Preferred communication style: Simple, everyday language.
**IMPORTANT**: 
- NO WIZARD WORKFLOW - Wizard routes completely disabled per user request. Users create new requests via `/inbound/new` which goes directly to the unified view/edit page.
- AUTO EDIT MODE - Forms load automatically in edit mode (no toggle needed) for immediate data entry.
- Nationality field uses comprehensive dropdown with 60+ countries.

## Recent Updates (December 2025)
- **Document Attachments**: New Documents tab in inbound requests for attaching passports, visas, tickets, confirmations, vouchers, contracts, and other files. Supports PDF, images, and office documents with drag-and-drop upload, categorization, and inline viewing.

## Recent Updates (November 2025)
- **ARD 1 Complete**: Enhanced Arrivals/Departures with visa status tracking, Meet & Assist, representative names, departure tax, and predefined location dropdowns
- **CARD 2 - Hotels Enhanced**: Added hotel categories, room type distribution (Single/Twin/King/Triple), multi-hotel support, hotel-level status tracking, **hotel date cascading** (check-in/check-out managed at hotel level, automatically cascade to all rooms)
- **CARD 3 - Transport Unified**: Comprehensive transport table with driver phone numbers, pickup/drop-off points, status tracking (REQUESTED/CONFIRMED/CANCELLED)
- **CARD 4 - Guides Enhanced**: Full guide profiles with telephone, national ID, tax number, language filtering, additional comments and internal comments (hidden duration/meeting point fields)
- **CARD 5 - Optional Extras**: New tab for services outside itinerary dates with flexible date handling
- **Overlay Workflow Sidebar**: Hidden-by-default overlay panel with floating toggle button, showing all 7 workflow stages (REQUEST → QUOTED → SUPPLIER_CONFIRMED → CONFIRMED → INVOICE → PROCESSING → COMPLETED). Features slide-in animation from left, semi-transparent backdrop, compact design (280px width), smaller fonts (0.8rem titles, 0.7rem descriptions), 32px status circles, and progress checkmarks. Completely hidden when not in use to maximize screen space. Fixed positioning ensures sidebar slides in from LEFT (not bottom)
- **Automatic Day Calculation**: Number of days field automatically calculates from travel dates (readonly field with instant updates)
- **Hotel Date Auto-Inheritance**: Hotels automatically inherit check-in/check-out dates from request from_date and to_date. When services are generated with hotel flags, the system creates hotel records with check_in_date = request.from_date, check_out_date = request.to_date, and automatically calculates nights
- **Hotel Date Cascading**: Check-in and check-out dates are now managed exclusively at hotel level (InboundHotel). All rooms (HotelRoom) access hotel dates via @property methods for single source of truth. Removed redundant date columns from hotel_room table. Rooms automatically inherit parent hotel's check_in_date, check_out_date, and nights

## System Architecture

### Backend
- **Framework**: Flask (Python 3.11)
- **Database**: PostgreSQL 16 with SQLAlchemy ORM
- **Authentication**: Flask-Login with OAuth support (Replit Auth)
- **Forms**: Flask-WTF for form handling and CSRF protection
- **Deployment**: Gunicorn WSGI server on Replit

### Frontend
- **Template Engine**: Jinja2
- **Styling**: Bootstrap 5 with custom CSS, FontAwesome 6
- **JavaScript**: Vanilla JS (ES6) for interactive features.
- **UI Components**: Bootstrap modals, tabs, responsive design.

### Database Design
- **ORM**: SQLAlchemy with declarative base model.
- **Migration Strategy**: Direct SQL migrations.
- **Connection Pooling**: Configured with pool recycling and pre-ping.

### Key Features & Design Patterns
- **Core Models**: User, Agent, OAuth, Booking, ServiceItem, Document, Customer, Supplier, Payment, Expense, FinancialMetric, ServiceConfirmation, InboundRequest, ItineraryRow, ArrivalDeparture, ArrivalBatch, DepartureBatch, InboundHotel, HotelRoom, InboundTransport, InboundGuide, InboundMeal, InboundOptional, InboundDocument, HotelCategory.
- **Booking Workflow**: Status progression (REQUEST → QUOTED → CONFIRMED → PROCESSING → COMPLETED). Individual service-level status tracking.
- **Service Types**: Flight, Hotel, Transport, Visa, Insurance, Restaurant, Guide, Meal, Optional Extras.
- **Financial Operations**: Invoice generation, payment tracking, supplier cost management, Excel expense report export.
- **Document Management**: File uploads, AI-powered ticket/voucher analysis, document categorization.
- **Modular Design**: Blueprint structure for core functionalities.
- **UI/UX Decisions**:
    - Consistent branding with yellow/orange color scheme.
    - Clean, modern typography (Segoe UI, Georgia serif).
    - Compact and horizontal layouts for headers and footers.
    - Dynamic UI elements for multi-segment flights and multi-room hotel bookings.
    - **Hub-Style Landing Page**: Tile-based home page with quick navigation.
    - **New Itinerary Creation**: Single page for creating new requests via `/inbound/new` (replacing wizard workflow). Includes customer autocomplete, dynamic service addition with auto-filled dates based on arrival/departure, dynamic hotel room cards, and a live itinerary preview grid.
    - Professional top navigation and mobile responsiveness.
    - Interactive service details in Run-Down Plan dashboard.
- **AI Integration**: AI-powered scanning for document data extraction and intelligent data population.
- **Voucher Generation**: Professional, airline-style PDF voucher generation with chronological service ordering. Creative PDF timeline voucher generation with dual layout options.
- **Inbound Tour Operator System**: Itinerary-first booking approach, service flag system, dynamic pricing, and a unified edit interface.
- **Hotel Room Distribution**: Enhanced hotel service with room type distribution, board basis selection, and dietary requirements.
- **Daily Operations Dashboard**: Comprehensive daily operational dashboard with filtering and export.
- **Arrival/Departure Details**: Comprehensive arrival and departure details in `InboundRequest` model including points, times, visa type, driver name, meeting assistance, and departure tax. `ArrivalDeparture` model for multi-leg journeys.

## External Dependencies

- **Database**: PostgreSQL
- **AI/ML**: OpenAI (for AI-powered document scanning)
- **PDF Processing**: `pdf2image`, `pypdf2`, `pillow`, `reportlab`, `weasyprint` (for PDF generation and image conversion)
- **Communication**: Twilio (for SMS integration)
- **Frontend Libraries**: Bootstrap 5, FontAwesome, Chart.js (for data visualization), Select2 (for enhanced autocomplete dropdowns)
- **OAuth**: Replit Auth (via Flask-Dance)