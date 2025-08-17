# TravelBookPro - Comprehensive Travel Management System

## Overview
TravelBookPro is a Flask-based web application for travel agencies, managing booking operations, customer requests, service confirmations, and financial operations. It streamlines the entire workflow from initial customer inquiry to service confirmation and financial tracking, providing a complete solution for modern travel agencies. The project aims to empower travel businesses with efficient tools to enhance productivity and customer satisfaction.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (August 2025)

### Modern Dashboard Landing Page Redesign
- **Date**: August 14, 2025  
- **Feature**: Complete dashboard visual overhaul with modern, professional design
- **Components Added**:
  - Hero welcome section with "Windows of Jordan" branding and gradient background
  - Modern stat cards with gradient colors, hover animations, and improved typography
  - Beautiful table design with better spacing, colors, and visual hierarchy
  - Responsive design optimized for all screen sizes
  - Yellow/orange color scheme consistent with brand identity
  - Professional buttons with hover effects and modern styling
- **Visual Elements**: Blue gradient hero section, colorful stat cards, clean modern table, yellow accent colors
- **User Experience**: Improved visual appeal, better readability, modern animations
- **Status**: Fully implemented with responsive modern design replacing old grey layout

### Modern Top Navigation with Die Menu System
- **Date**: August 14, 2025
- **Feature**: Complete navigation system overhaul with professional top navigation bar and dropdown menus
- **Components Added**:
  - Modern top navigation bar with TravelBookPro branding and "Windows of Jordan" tagline
  - Die menu (dropdown) system with smooth animations and professional styling
  - Organized navigation: Home, Tours & Booking dropdown, Management dropdown, Dashboard
  - Tours & Booking includes: Inbound Tours, New Booking, Search & History, Travel Operations
  - Management includes: Customers, Suppliers, Finance (role-based), User Management (admin-only)
  - Mobile-responsive design with hamburger menu for smaller screens
  - Clean mobile sidebar without redundant branding
  - Professional gradient styling with yellow (#FFBF00) accent colors
- **Visual Elements**: Dark blue gradient background, yellow highlights, smooth hover animations
- **Mobile Design**: Collapsible sidebar with clean close button, overlay for better UX
- **Status**: Fully implemented with responsive design and interactive dropdown functionality

### Visual Timeline Voucher for Inbound Tours
- **Date**: August 13, 2025 (Updated August 17, 2025)
- **Feature**: Creative PDF timeline voucher generation for tour itineraries with dual layout options
- **Components Added**:
  - New templates: `voucher_timeline.html` (vertical) and `voucher_timeline_horizontal.html` (landscape)
  - Dropdown menu to select between vertical and horizontal timeline layouts
  - SVG icons replacing emojis for better print quality (Hotel, Transport, Meal, Guide, Airport)
  - PDF generation using WeasyPrint library with landscape mode for horizontal layout
  - Professional tour itinerary layout with cost breakdown
  - Bold fonts throughout for improved readability
- **Visual Elements**: Yellow (#fbbf24) headers with dark text, service icons in light grey (#e5e7eb) boxes
- **Latest Updates**: 
  - **Fixed multiple icons display**: Both layouts now show all service icons when multiple services exist on same day
  - **Removed grey boxes**: All grey backgrounds replaced with yellow (#fbbf24) and dark text for readability
  - **Compact day circles**: Horizontal layout uses smaller (40x40px) yellow circles with black text
  - **Horizontal Layout Optimization (Aug 17, 2025)**: Changed to 4-column grid layout to prevent overflow, light grey service boxes (#e5e7eb), removed duplicate dates
  - **Grid Layout**: Horizontal timeline now uses CSS Grid with 4 days per row for better spacing and page fitting
  - **Service Icons Styling**: Changed from yellow to light grey (#e5e7eb) background with dark grey (#374151) text and icons
- **Status**: Fully implemented with optimized horizontal layout for better print formatting

## Recent Changes (August 2025)

### Hotel Room Distribution Enhancement with Dietary Information
- **Date**: August 15, 2025
- **Feature**: Expanded hotel service with room type distribution and dietary requirements functionality
- **Components Added**:
  - Database columns: hotel_single_rooms, hotel_double_rooms, hotel_triple_rooms, hotel_other_rooms in ItineraryRow table
  - Dynamic room distribution UI that expands when hotel checkbox is selected
  - Professional dark blue header styling with white text for better contrast
  - Room table expanded to 1800px minimum width with horizontal scrolling
  - Added Board Basis dropdown (Room Only, B&B, Half Board, Full Board, All Inclusive, Ultra All Inclusive)
  - Added Dietary Requirements field for special meal needs (Vegetarian, Halal, Gluten-free, etc.)
  - JavaScript integration for real-time room count updates and "Add Room" functionality
  - Backend save/load functionality for room distribution and dietary data
- **Visual Elements**: Expanded table with 11 columns, optimized column widths, 200px Lead Passenger field
- **Flow**: Room counts from itinerary automatically populate hotel confirmation pages with dietary options
- **Status**: Fully implemented with comprehensive room and meal management capabilities

### Inbound Tour Operator System Implementation
- **Date**: August 9-10, 2025
- **Feature**: Complete inbound tour operator module with itinerary-first booking approach
- **Components Added**:
  - New models: InboundRequest, ItineraryRow, InboundHotel, InboundTransport, InboundMeal, InboundGuide
  - Service flag system for auto-generation of linked service records
  - Auto request number generation (INB-YYYYMM-####)
  - Dynamic pricing with Per Person/Per Group cost units
  - Itinerary table with service flags (Hotel, M&G/Guide, Transport, Meal, Airport)
  - Service auto-generation creates normal ServiceItem records linked to Booking
  - Blueprint routing: /inbound/* for all inbound operations
  - Forms and templates for comprehensive itinerary management
  - JavaScript modules for real-time itinerary editing and service management
  - Integration with normal booking workflow (/booking/124 format)
  - New service types: SERVICE_RESTAURANT and SERVICE_GUIDE for inbound operations
- **Workflow**: Generate itinerary → Generate Services & Open Booking → Use normal confirmation flow
- **Latest Updates (Aug 10)**:
  - **Unified Edit Interface**: Combined master details and itinerary on single page for better UX
  - **Real-time Master Details Editing**: Agent, contact, dates, pax, customer selection all editable inline
  - **Auto Date Calculation**: Dynamic calculation of number of days when dates change
  - **Single Save Operation**: "Save All Changes" button updates both master details and itinerary
  - **Customer Integration**: Customer selection dropdown integrated into master details form
  - **Enhanced User Experience**: Eliminated need for separate navigation between master and itinerary sections
- **Status**: Unified interface implemented with comprehensive master details editing

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
- **JavaScript**: Vanilla JS for interactive features
- **Icons**: FontAwesome 6
- **UI Components**: Bootstrap modals, tabs, and responsive design

### Database Design
- **ORM**: SQLAlchemy with declarative base model
- **Migration Strategy**: Direct SQL migrations
- **Connection Pooling**: Configured with pool recycling and pre-ping

### Key Features & Design Patterns
- **Core Models**: User, Agent, OAuth, Booking, ServiceItem, Document, Customer, Supplier, Payment, Expense, FinancialMetric, ServiceConfirmation.
- **Booking Workflow**: REQUEST → BOOKED → IN-PROGRESS → CONFIRMED status progression.
- **Service Types**: Flight, Hotel, Transport, Visa, Insurance.
- **Financial Operations**: Invoice generation, payment tracking, supplier cost management.
- **Document Management**: File uploads, AI-powered ticket/voucher analysis, document categorization.
- **Blueprint Structure**: Modular design for main routes, booking, voucher generation, authentication, and finance.
- **UI/UX Decisions**: Consistent branding with yellow/orange color scheme for status badges and company logo. Use of clean, modern typography (Segoe UI, Georgia serif) for readability, especially in vouchers. Compact and horizontal layouts for headers and footers to optimize space. Dynamic UI elements for multi-segment flights and multi-room hotel bookings.
- **AI Integration**: AI-powered scanning for document data extraction (e.g., flight details, hotel details, passport information, ticket numbers, passenger types, PNRs) with sequential mapping and intelligent data population into forms.
- **Voucher Generation**: Professional, airline-style PDF voucher generation with detailed layouts for flights, hotels, and comprehensive passenger/ticket information, ensuring accurate chronological ordering of services.

## External Dependencies

- **Database**: PostgreSQL
- **AI/ML**: OpenAI (for AI-powered document scanning and data extraction)
- **PDF Processing**: `pdf2image`, `pypdf2`, `pillow`, `reportlab`, `weasyprint` (for PDF generation and image conversion)
- **Communication**: Twilio (for SMS integration)
- **Frontend Libraries**: Bootstrap 5, FontAwesome, Chart.js (for data visualization)
- **OAuth**: Replit Auth (via Flask-Dance)