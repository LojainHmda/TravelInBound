# TravelBookPro - Comprehensive Travel Management System

## Overview
TravelBookPro is a Flask-based web application for travel agencies, managing booking operations, customer requests, service confirmations, and financial operations. It streamlines the entire workflow from initial customer inquiry to service confirmation and financial tracking, providing a complete solution for modern travel agencies. The project aims to empower travel businesses with efficient tools to enhance productivity and customer satisfaction.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (August 2025)

### Inbound Tour Operator System Implementation
- **Date**: August 9, 2025
- **Feature**: Complete inbound tour operator module with itinerary-first booking approach
- **Components Added**:
  - New models: InboundRequest, ItineraryRow, InboundHotel, InboundTransport, InboundMeal, InboundGuide
  - Service flag system for auto-generation of linked service records
  - Auto request number generation (INB-YYYYMM-####)
  - Dynamic pricing with Per Person/Per Group cost units
  - Itinerary table with service flags (Hotel, M&G/Guide, Transport, Meal, Airport)
  - Service auto-generation based on flags with intelligent defaults
  - Blueprint routing: /inbound/* for all inbound operations
  - Forms and templates for comprehensive itinerary management
  - JavaScript modules for real-time itinerary editing and service management
- **Status**: Core functionality implemented, ready for testing

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