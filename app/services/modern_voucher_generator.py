
"""
Modern Voucher Generator Service
Creates clean, professional vouchers with improved visual design
"""

import json
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF


class ModernVoucherGenerator:
    def __init__(self):
        # Brand colors matching dashboard - define these first
        self.primary_color = colors.Color(0, 0.031, 0.5)  # #000080 - Dark blue
        self.accent_color = colors.Color(1, 0.549, 0)     # #FF8C00 - Orange
        self.gold_color = colors.Color(1, 0.843, 0)       # #FFD700 - Gold
        self.light_gray = colors.Color(0.95, 0.95, 0.95)  # Light gray for backgrounds
        
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for modern design"""
        
        # Company header style
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=5,
            spaceBefore=10
        ))
        
        # Voucher title style
        self.styles.add(ParagraphStyle(
            name='VoucherTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.accent_color,
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold',
            spaceAfter=10
        ))
        
        # Section headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=self.primary_color,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=8,
            spaceBefore=16,
            leftIndent=0
        ))
        
        # Customer info style
        self.styles.add(ParagraphStyle(
            name='CustomerInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=4
        ))
        
        # Service details
        self.styles.add(ParagraphStyle(
            name='ServiceDetail',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=3
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=5
        ))

    def generate_voucher(self, booking_id: int) -> BytesIO:
        """Generate modern voucher PDF"""
        from app.models import Booking
        
        booking = Booking.query.get_or_404(booking_id)
        
        # Create PDF with custom page template
        buffer = BytesIO()
        pdf_document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f"Travel Voucher - {booking.reference_number}"
        )
        
        # Build document content
        content = []
        
        # Company header
        content.extend(self._create_company_header())
        
        # Header section
        content.extend(self._create_header(booking))
        
        # Customer information section
        content.extend(self._create_customer_section(booking))
        
        # Only show confirmed services in voucher
        confirmed_services = [item for item in booking.service_items if item.status == 'CONFIRMED']
        
        if confirmed_services:
            # Services section with only confirmed services
            content.extend(self._create_services_section_confirmed(booking, confirmed_services))
        else:
            # If no confirmed services, show a message
            content.append(Paragraph("No confirmed services to display in voucher.", self.styles['ServiceDetail']))
            content.append(Spacer(1, 0.2*inch))
        
        # Payment section
        content.extend(self._create_payment_section(booking))
        
        # Footer
        content.extend(self._create_footer())
        
        # Build PDF
        pdf_document.build(content)
        buffer.seek(0)
        return buffer

    def _create_company_header(self):
        """Create company header"""
        content = []
        
        # Company name and voucher title
        content.append(Paragraph("ARABI TRAVEL", self.styles['CompanyHeader']))
        content.append(Paragraph("TRAVEL VOUCHER", self.styles['VoucherTitle']))
        content.append(Spacer(1, 0.3*inch))
        
        return content

    def _create_header(self, booking):
        """Create clean header matching the concept design"""
        content = []
        
        # Customer and Voucher Details sections side by side
        customer_name = booking.customer.name if booking.customer else booking.requester.username
        customer_email = booking.customer.email if booking.customer else booking.requester.email
        
        confirmed_services = [item for item in booking.service_items if item.status == 'CONFIRMED']
        
        header_data = [
            [
                Paragraph("<b>Customer:</b>", self.styles['SectionHeader']),
                Paragraph("<b>Voucher Details:</b>", self.styles['SectionHeader'])
            ],
            [
                Paragraph(f"{customer_name}<br/>{customer_email}", self.styles['CustomerInfo']),
                Paragraph(f"<b>Voucher Number:</b> {booking.reference_number}<br/>" + 
                         f"<b>Booking Date:</b> {booking.created_at.strftime('%d %b %Y')}<br/>" +
                         f"<b>Confirmed Services:</b> {len(confirmed_services)}<br/>" +
                         f"<b>Status:</b> <font color='green'>Confirmed</font>", 
                         self.styles['CustomerInfo'])
            ]
        ]
        
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        content.append(header_table)
        content.append(Spacer(1, 0.2*inch))
        
        return content

    def _create_customer_section(self, booking):
        """Create customer information section"""
        content = []
        
        # Customer details in a clean table format
        customer_name = booking.customer.name if booking.customer else booking.requester.username
        customer_email = booking.customer.email if booking.customer else booking.requester.email
        customer_phone = getattr(booking.customer, 'phone', 'N/A') if booking.customer else 'N/A'
        
        confirmed_services = [item for item in booking.service_items if item.status == 'CONFIRMED']
        
        customer_data = [
            ["Customer:", customer_name, "Voucher Number:", booking.reference_number],
            ["Email:", customer_email, "Booking Date:", booking.created_at.strftime('%d %b %Y')],
            ["Phone:", customer_phone, "Confirmed Services:", str(len(confirmed_services))],
            ["", "", "Status:", "Confirmed"]
        ]
        
        customer_table = Table(customer_data, colWidths=[1*inch, 2.5*inch, 1.2*inch, 1.3*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_color),
            ('TEXTCOLOR', (2, 0), (2, -1), self.primary_color),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        content.append(customer_table)
        content.append(Spacer(1, 0.3*inch))
        
        return content

    def _create_services_section_confirmed(self, booking, confirmed_services):
        """Create services section with only confirmed services"""
        content = []
        
        if not confirmed_services:
            content.append(Paragraph("No confirmed services found for this booking.", self.styles['ServiceDetail']))
            return content
        
        # Group confirmed services by type
        services_by_type = {}
        for item in confirmed_services:
            service_type = item.service_type
            if service_type not in services_by_type:
                services_by_type[service_type] = []
            services_by_type[service_type].append(item)
        
        # Create services summary table first
        summary_data = [['Service Type', 'Quantity', 'Status', 'Amount']]
        total_amount = 0
        
        for service_type, items in services_by_type.items():
            quantity = len(items)
            service_total = sum(item.amount for item in items if item.amount)
            
            summary_data.append([
                service_type.title(),
                str(quantity),
                "Confirmed",
                f"${service_total:.2f}"
            ])
            total_amount += service_total
        
        # Add total row
        summary_data.append(['TOTAL', '', '', f"${total_amount:.2f}"])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.light_gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.primary_color),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.primary_color),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), self.light_gray),
        ]))
        
        content.append(Paragraph("Confirmed Services", self.styles['SectionHeader']))
        content.append(summary_table)
        content.append(Spacer(1, 0.2*inch))
        
        # Detailed service information for confirmed services only
        for service_type, items in services_by_type.items():
            content.extend(self._create_service_details(service_type, items))
        
        return content

    def _create_service_details(self, service_type, items):
        """Create detailed service information"""
        content = []
        
        content.append(Paragraph(f"{service_type.title()} Details", self.styles['SectionHeader']))
        
        for i, item in enumerate(items, 1):
            # Get confirmation details from documents
            confirmation_details = self._get_confirmation_details(item)
            
            if service_type == 'FLIGHT':
                content.extend(self._create_flight_details(item, confirmation_details, i))
            elif service_type == 'HOTEL':
                content.extend(self._create_hotel_details(item, confirmation_details, i))
            else:
                content.extend(self._create_general_service_details(item, confirmation_details, i))
        
        content.append(Spacer(1, 0.15*inch))
        return content

    def _create_flight_details(self, item, confirmation_details, index):
        """Create flight details matching the concept design"""
        content = []
        
        # Main Flight Details header with blue background
        flight_header = Table([["Flight Details"]], colWidths=[6*inch])
        flight_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.2, 0.4, 0.6)),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(flight_header)
        
        # Outbound Journey header
        journey_date = item.start_date.strftime('%d %b %Y')
        outbound_header = Table([[f"Outbound Journey ({journey_date})"]], colWidths=[6*inch])
        outbound_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.4, 0.6, 0.8)),  # Lighter blue
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(outbound_header)
        
        # Flight details table with headers
        flight_headers = ["Airline", "Flight No.", "Route", "Departure", "Arrival", "Class"]
        
        # Extract flight data from confirmation details or use defaults
        airline = confirmation_details.get('airline', 'TBD') if confirmation_details else 'TBD'
        flight_no = confirmation_details.get('flight_number', 'TBD') if confirmation_details else 'TBD'
        route = confirmation_details.get('route', item.description) if confirmation_details else item.description
        departure_time = confirmation_details.get('departure_time', 'TBD') if confirmation_details else 'TBD'
        arrival_time = confirmation_details.get('arrival_time', 'TBD') if confirmation_details else 'TBD'
        flight_class = confirmation_details.get('class', 'Economy') if confirmation_details else 'Economy'
        
        # Format departure and arrival with dates
        departure = f"{item.start_date.strftime('%d %b %Y')} {departure_time}"
        arrival = f"{item.end_date.strftime('%d %b %Y')} {arrival_time}"
        
        flight_data = [
            flight_headers,
            [airline, flight_no, route, departure, arrival, flight_class]
        ]
        
        # Check if there's a connecting flight or return journey
        if confirmation_details and 'connecting_flight' in confirmation_details:
            connecting = confirmation_details['connecting_flight']
            flight_data.append([
                connecting.get('airline', 'TBD'),
                connecting.get('flight_number', 'TBD'),
                connecting.get('route', 'TBD'),
                connecting.get('departure', 'TBD'),
                connecting.get('arrival', 'TBD'),
                connecting.get('class', 'Economy')
            ])
        
        flight_table = Table(flight_data, colWidths=[1*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch, 0.6*inch])
        flight_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.4, 0.6, 0.8)),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            
            # Grid and padding
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(flight_table)
        content.append(Spacer(1, 0.2*inch))
        return content

    def _create_hotel_details(self, item, confirmation_details, index):
        """Create hotel-specific details"""
        content = []
        
        hotel_title = f"Hotel {index} - {item.description}"
        content.append(Paragraph(hotel_title, self.styles['ServiceDetail']))
        
        # Hotel details table
        hotel_data = [
            ["Hotel Information", "Booking Details"],
            [
                f"Hotel: {confirmation_details.get('hotel_name', item.description) if confirmation_details else item.description}",
                f"Check-in: {item.start_date.strftime('%d %b %Y')}"
            ],
            [
                f"Address: {confirmation_details.get('address', 'TBD') if confirmation_details else 'TBD'}",
                f"Check-out: {item.end_date.strftime('%d %b %Y')}"
            ]
        ]
        
        if confirmation_details:
            nights = (item.end_date - item.start_date).days
            hotel_data.extend([
                [f"Phone: {confirmation_details.get('phone', 'TBD')}", f"Nights: {nights} nights"],
                [f"Confirmation: {confirmation_details.get('confirmation_number', 'TBD')}", f"Status: Confirmed"],
                [f"Room: {confirmation_details.get('room_type', 'TBD')}", f"Amount: ${item.amount:.2f}" if item.amount else "Amount: TBD"]
            ])
        else:
            nights = (item.end_date - item.start_date).days
            hotel_data.extend([
                [f"Phone: TBD", f"Nights: {nights} nights"],
                [f"Confirmation: TBD", f"Status: Confirmed"],
                [f"Room: TBD", f"Amount: ${item.amount:.2f}" if item.amount else "Amount: TBD"]
            ])
        
        hotel_table = Table(hotel_data, colWidths=[3*inch, 3*inch])
        hotel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.light_gray),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(hotel_table)
        content.append(Spacer(1, 0.1*inch))
        
        return content

    def _create_general_service_details(self, item, confirmation_details, index):
        """Create general service details for other service types"""
        content = []
        
        service_title = f"{item.service_type.title()} {index} - {item.description}"
        content.append(Paragraph(service_title, self.styles['ServiceDetail']))
        
        # General service table
        service_data = [
            ["Service Information", "Details"],
            [f"Type: {item.service_type.title()}", f"Start: {item.start_date.strftime('%d %b %Y')}"],
            [f"Description: {item.description}", f"End: {item.end_date.strftime('%d %b %Y')}"],
            [f"Status: Confirmed", f"Amount: ${item.amount:.2f}" if item.amount else "Amount: TBD"]
        ]
        
        service_table = Table(service_data, colWidths=[3*inch, 3*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.light_gray),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(service_table)
        content.append(Spacer(1, 0.1*inch))
        
        return content

    def _create_payment_section(self, booking):
        """Create payment summary section"""
        content = []
        
        content.append(Paragraph("Payment Summary", self.styles['SectionHeader']))
        
        # Calculate total from confirmed services only
        confirmed_services = [item for item in booking.service_items if item.status == 'CONFIRMED']
        total_amount = sum(item.amount for item in confirmed_services if item.amount)
        
        # Get total payments
        total_payments = sum(payment.amount for payment in booking.payments) if booking.payments else 0
        balance_due = total_amount - total_payments
        
        payment_data = [
            ["Total Amount:", f"${total_amount:.2f}"],
            ["Amount Paid:", f"${total_payments:.2f}"],
            ["Balance Due:", f"${balance_due:.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.primary_color),
            ('LINEBELOW', (0, -1), (-1, -1), 2, self.accent_color),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        content.append(payment_table)
        content.append(Spacer(1, 0.2*inch))
        
        # Travel information note
        travel_note = """
        <b>Travel Information</b><br/>
        Please keep this voucher with you during travel. Present it at check-in and to service providers as confirmation of your booking.
        """
        content.append(Paragraph(travel_note, self.styles['ServiceDetail']))
        content.append(Spacer(1, 0.2*inch))
        
        return content

    def _create_footer(self):
        """Create footer with contact and banking information"""
        content = []
        
        # Banking and contact information
        footer_data = [
            ["Banking Information", "Contact Information"],
            ["Arabi Travel Bank", "sales@arabtravel.ps"],
            ["Account USD= 9070-142464-510", "www.arabtravel.ps"],
            ["Bank Of Palestine", "+97022956640"],
            ["Branch Name: Ramallah Branch", "Alersal St, zakat Bld"],
            ["0458/2220908/001/3000/000", "Ramallah, P.OBOX:27"]
        ]
        
        footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.light_gray),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.primary_color),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(footer_table)
        content.append(Spacer(1, 0.2*inch))
        
        # Thank you message
        thank_you = """
        <para align="center"><b>ARABI TRAVEL</b><br/>
        Thank you for booking with Arabi Travel</para>
        """
        content.append(Paragraph(thank_you, self.styles['Footer']))
        
        return content

    def _get_confirmation_details(self, service_item):
        """Extract confirmation details from service item documents"""
        confirmation_details = {}
        
        # Look for confirmation documents
        if hasattr(service_item, 'documents') and service_item.documents:
            for document in service_item.documents:
                if document.document_type == 'CONFIRMATION' and document.notes:
                    try:
                        # Parse JSON notes for confirmation details
                        doc_data = json.loads(document.notes)
                        confirmation_details.update(doc_data)
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, treat as plain text
                        pass
        
        return confirmation_details
