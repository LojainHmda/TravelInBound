# TravelBookPro - Comprehensive Travel Management System

## Overview
TravelBookPro is a Flask-based web application designed for travel agencies to streamline booking operations, manage customer requests, confirm services, and track financial operations. It aims to enhance productivity and customer satisfaction by providing an efficient solution for the entire travel management workflow, from inquiry to financial tracking.

## User Preferences
Preferred communication style: Simple, everyday language.

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
    - **Wizard Workflow for New Itineraries**: 5-step guided wizard for creating new tour itineraries:
        1. Arrival/Departure Points & Borders (contact info, dates, times, border crossings)
        2. Driver Selection (transport providers with visual cards)
        3. Hotel Selection (accommodation providers with visual cards)
        4. Restaurant/Meal Selection (dining options with visual cards)
        5. Guide Selection (tour guide selection and final itinerary creation)
    - Progressive wizard UI with step indicators, session-based data persistence, and seamless flow between steps.
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
- **Frontend Libraries**: Bootstrap 5, FontAwesome, Chart.js (for data visualization)
- **OAuth**: Replit Auth (via Flask-Dance)