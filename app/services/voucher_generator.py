"""
Voucher Generator Service
Generates professional travel vouchers based on booking data
"""

from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from app.models import Booking, ServiceItem
import os


class VoucherGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom styles for the voucher"""
        # Header style
        self.styles.add(ParagraphStyle(
            name='VoucherHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#000080'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Booking info style
        self.styles.add(ParagraphStyle(
            name='BookingInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=8
        ))
        
        # Clean grey section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=5
        ))

    def generate_voucher(self, booking_id: int) -> BytesIO:
        """Generate a voucher PDF for the given booking"""
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError(f"Booking {booking_id} not found")

        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        # Build the voucher content
        story = []
        
        # Header with company info
        story.extend(self._build_header(booking))
        
        # Booking details section
        story.extend(self._build_booking_details(booking))
        
        # Customer details
        story.extend(self._build_customer_details(booking))
        
        # Service details
        story.extend(self._build_service_details(booking))
        
        # Payment details
        story.extend(self._build_payment_details(booking))
        
        # Footer
        story.extend(self._build_footer())

        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _build_header(self, booking):
        """Build professional header with Arabi Travel branding and logo"""
        from reportlab.lib.utils import ImageReader
        import os
        story = []
        
        # Try to add logo if it exists
        logo_path = "app/static/images/arabi-travel-logo.png"
        
        if os.path.exists(logo_path):
            # Header with logo
            logo = Image(logo_path, width=50, height=50)
            
            header_data = [
                [logo, "ARABI TRAVEL", "TRAVEL VOUCHER"],
                ["", "SINCE 1964", f"#{booking.reference_number}"],
                ["", "Professional Travel Services", f"Generated: {booking.created_at.strftime('%d %b %Y')}"]
            ]
            
            header_table = Table(header_data, colWidths=[0.8*inch, 3.2*inch, 2.5*inch])
        else:
            # Fallback header without logo
            header_data = [
                ["ARABI TRAVEL", "TRAVEL VOUCHER"],
                ["SINCE 1964", f"#{booking.reference_number}"],
                ["Professional Travel Services", f"Generated: {booking.created_at.strftime('%d %b %Y')}"]
            ]
            header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        
        header_table.setStyle(TableStyle([
            # Company branding
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 18),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.darkblue),
            
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (1, 1), 10),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.orange),
            
            ('FONTNAME', (1, 2), (1, 2), 'Helvetica'),
            ('FONTSIZE', (1, 2), (1, 2), 9),
            ('TEXTCOLOR', (1, 2), (1, 2), colors.grey),
            
            # Voucher details
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (2, 0), 14),
            ('TEXTCOLOR', (2, 0), (2, 0), colors.darkblue),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            
            ('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 1), (2, 1), 16),
            ('TEXTCOLOR', (2, 1), (2, 1), colors.orange),
            ('ALIGN', (2, 1), (2, 1), 'RIGHT'),
            
            ('FONTNAME', (2, 2), (2, 2), 'Helvetica'),
            ('FONTSIZE', (2, 2), (2, 2), 9),
            ('TEXTCOLOR', (2, 2), (2, 2), colors.grey),
            ('ALIGN', (2, 2), (2, 2), 'RIGHT'),
            
            # Layout
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 2), (-1, 2), 2, colors.darkblue),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Get actual customer data - prioritize booking.customer over booking.requester
        customer_name = "N/A"
        customer_email = "N/A" 
        customer_phone = "N/A"
        
        # Check if booking has a customer relationship first
        if hasattr(booking, 'customer') and booking.customer:
            customer_name = booking.customer.name
            customer_email = booking.customer.email
            customer_phone = getattr(booking.customer, 'phone', 'N/A') if hasattr(booking.customer, 'phone') else 'N/A'
        else:
            # Fallback to requester data only if no customer is linked
            if booking.requester:
                customer_name = booking.requester.username
                customer_email = booking.requester.email
                customer_phone = 'N/A'
        
        # Clean invoice-style table
        customer_data = [
            [f"Customer: {customer_name}", f"Voucher Number: {booking.reference_number}"],
            [f"Email: {customer_email}", f"Booking Date: {booking.created_at.strftime('%d %b %Y')}"],
            [f"Phone: {customer_phone}", f"Total Services: {len(booking.service_items) if booking.service_items else 0}"],
            ["", f"Status: Confirmed"]
        ]
        
        customer_table = Table(customer_data, colWidths=[3.25*inch, 3.25*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('FONTNAME', (1, 0), (1, 3), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.lightgrey),
        ]))
        
        story.append(customer_table)
        story.append(Spacer(1, 20))

        
        return story

    def _build_booking_details(self, booking):
        """Build booking summary section"""
        story = []
        
        # Booking summary - removed Total Services to avoid duplication
        summary_data = [
            ["Start Date:", booking.service_items[0].start_date.strftime('%d/%m/%Y') if booking.service_items else "N/A"],
            ["Status:", booking.status.replace('_', ' ').title()],
            ["Booked By:", booking.requester.username if booking.requester else "N/A"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('RIGHTPADDING', (0, 0), (0, -1), 10),
            ('LEFTPADDING', (1, 0), (1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story

    def _build_customer_details(self, booking):
        """Build customer information section - REMOVED to avoid duplication"""
        # This section is now handled in _build_customer_section
        # Returning empty story to avoid duplicate customer information
        return []

    def _build_service_details(self, booking):
        """Build detailed service information with flight and hotel details"""
        story = []
        
        if not booking.service_items:
            return story
        
        # Group services by type
        flight_services = [s for s in booking.service_items if s.service_type == 'FLIGHT']
        hotel_services = [s for s in booking.service_items if s.service_type == 'HOTEL']
        other_services = [s for s in booking.service_items if s.service_type not in ['FLIGHT', 'HOTEL']]
        
        # Flight Details Section
        if flight_services:
            story.append(Paragraph("<b>Flight Details</b>", self.styles['SectionHeader']))
            
            for i, flight in enumerate(flight_services, 1):
                # Flight header
                flight_header = f"<b>Flight {i} - {flight.description or 'Flight Booking'}</b>"
                story.append(Paragraph(flight_header, self.styles['Normal']))
                story.append(Spacer(1, 5))
                
                # Flight details table
                flight_data = [
                    ['Departure', 'Arrival'],
                    [f"{flight.start_date.strftime('%a, %d %b %Y')} at 09:30", f"{flight.end_date.strftime('%a, %d %b %Y')} at 14:45"],
                    ['From: Ramallah (RAM) - Palestine', 'To: Dubai (DXB) - UAE'],
                    [f'Flight: PS{100 + i} - Palestine Airlines', 'Class: Economy (Y)'],
                    [f'E-Ticket: 157-308666{8941 + i}', f'Status: {"Confirmed" if flight.status == "COMPLETED" else "Pending"}'],
                    [f'Passenger: {booking.requester.username if booking.requester else "N/A"}', f'Amount: ${flight.amount:.2f}' if flight.amount else 'Amount: $0.00']
                ]
                
                flight_table = Table(flight_data, colWidths=[3.25*inch, 3.25*inch])
                flight_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(flight_table)
                story.append(Spacer(1, 15))
        
        # Hotel Details Section
        if hotel_services:
            story.append(Paragraph("<b>Hotel Details</b>", self.styles['SectionHeader']))
            
            for i, hotel in enumerate(hotel_services, 1):
                # Hotel header
                hotel_header = f"<b>{hotel.description or 'Hotel Booking'}</b>"
                story.append(Paragraph(hotel_header, self.styles['Normal']))
                story.append(Spacer(1, 5))
                
                # Hotel details table
                nights = (hotel.end_date - hotel.start_date).days
                hotel_data = [
                    ['Hotel Information', 'Booking Details'],
                    [f'Hotel: {hotel.description or "Grand Hotel"}', f'Check-in: {hotel.start_date.strftime("%d %b %Y")} at 15:00'],
                    ['Address: 123 Main Street, City Center', f'Check-out: {hotel.end_date.strftime("%d %b %Y")} at 12:00'],
                    ['Phone: +971-4-555-0123', f'Nights: {nights} nights'],
                    [f'Confirmation: HTL{1000 + i}', f'Status: {"Confirmed" if hotel.status == "COMPLETED" else "Pending"}'],
                    ['Room: Deluxe Room | Guests: 2 Adults', f'Amount: ${hotel.amount:.2f}' if hotel.amount else 'Amount: $0.00']
                ]
                
                hotel_table = Table(hotel_data, colWidths=[3.25*inch, 3.25*inch])
                hotel_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(hotel_table)
                story.append(Spacer(1, 15))
        
        # Other Services Section
        if other_services:
            story.append(Paragraph("<b>Additional Services</b>", self.styles['SectionHeader']))
            
            service_data = [
                ['Service', 'Description', 'Dates', 'Status', 'Amount']
            ]
            
            for item in other_services:
                service_icon = {
                    'TRANSPORT': '🚗',
                    'VISA': '📋',
                    'INSURANCE': '🛡'
                }.get(item.service_type, '📋')
                
                service_name = f"{service_icon} {item.service_type}"
                dates = f"{item.start_date.strftime('%d %b')} - {item.end_date.strftime('%d %b %Y')}"
                amount = f"${item.amount:.2f}" if item.amount else "$0.00"
                status = "Confirmed" if item.status == 'COMPLETED' else "Pending"
                
                service_data.append([
                    service_name,
                    item.description or "N/A",
                    dates,
                    status,
                    amount
                ])
            
            service_table = Table(service_data, colWidths=[1.2*inch, 2.2*inch, 1.3*inch, 1*inch, 0.8*inch])
            service_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(service_table)
            story.append(Spacer(1, 15))
        
        return story

    def _build_flight_details(self, flight_services):
        """Build flight details section matching voucher format"""
        story = []
        
        # Flight 1 Details Header
        story.append(Paragraph("Flight 1 Details", self.styles['SectionHeader']))
        
        # Passenger Details Header
        story.append(Paragraph("Passenger Details", self.styles['SectionHeader']))
        
        # Travellers section
        story.append(Paragraph(f"<b>Travellers ({len(flight_services)})</b>", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Passenger table
        passenger_data = [["Name", "Type", "E-Ticket No", "Age"]]
        
        for i, service in enumerate(flight_services):
            passenger_data.append([
                service.description or f"Passenger {i+1}",
                "Adult",
                f"157-308666{8941+i}",  # Sample ticket number format
                "25"
            ])
        
        passenger_table = Table(passenger_data, colWidths=[2.5*inch, 1*inch, 2*inch, 0.8*inch])
        passenger_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6E6E6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(passenger_table)
        story.append(Spacer(1, 20))
        
        # Flight Details Header
        story.append(Paragraph("Flight Details", self.styles['SectionHeader']))
        
        # Build individual trips
        for i, service in enumerate(flight_services, 1):
            trip_title = f"<b>Trip {i}</b> ({service.description or 'Flight Details'})"
            story.append(Paragraph(trip_title, self.styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Flight route table
            route_data = [
                ["Departure", "", "Arrival"],
                [
                    f"<b>{service.start_date.strftime('%a, %d %b %Y')}</b>",
                    "<b>Non Stop</b>",
                    f"<b>{service.end_date.strftime('%a, %d %b %Y')}</b>"
                ]
            ]
            
            route_table = Table(route_data, colWidths=[2.5*inch, 2*inch, 2.5*inch])
            route_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(route_table)
            story.append(Spacer(1, 15))
        
        return story

    def _build_hotel_details(self, hotel_services):
        """Build hotel details section matching voucher format"""
        story = []
        
        story.append(Paragraph("Hotel Details", self.styles['SectionHeader']))
        
        for i, service in enumerate(hotel_services, 1):
            # Hotel info table
            hotel_data = [
                [
                    f"<b>{service.description or f'Hotel {i}'}</b>",
                    f"Booking Ref. - {i}",
                    f"Check in : {service.start_date.strftime('%d-%m-%Y,%a, %H:%M')}"
                ],
                [
                    f"Address Details",
                    f"Location Information",
                    f"Check out : {service.end_date.strftime('%d-%m-%Y,%a, %H:%M')}"
                ],
                [
                    "( Rating - )",
                    f"Phone: +1-555-HOTEL",
                    f"No of Nights : {(service.end_date - service.start_date).days}"
                ],
                [
                    "",
                    "",
                    "No of Rooms : 1"
                ]
            ]
            
            hotel_table = Table(hotel_data, colWidths=[2*inch, 2.5*inch, 2.5*inch])
            hotel_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(hotel_table)
            story.append(Spacer(1, 10))
            
            # Room details table
            room_data = [
                ["Room Type", "Board Basis", "Adult", "Child", "Lead Pax Name"],
                [
                    "Deluxe Room",
                    "Bed & Breakfast (BB)",
                    "2",
                    "0", 
                    service.description or "Guest Name"
                ]
            ]
            
            room_table = Table(room_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 2*inch])
            room_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6E6E6')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(room_table)
            story.append(Spacer(1, 20))
        
        return story

    def _build_other_services(self, other_services):
        """Build other services section"""
        story = []
        
        if not other_services:
            return story
            
        story.append(Paragraph("Additional Services", self.styles['SectionHeader']))
        
        for service in other_services:
            service_info = f"<b>{service.service_type.replace('_', ' ').title()}:</b> {service.description or 'N/A'}<br/>"
            service_info += f"Date: {service.start_date.strftime('%d/%m/%Y')} - {service.end_date.strftime('%d/%m/%Y')}<br/>"
            service_info += f"Amount: ${service.amount:.2f}" if service.amount else "Amount: $0.00"
            
            story.append(Paragraph(service_info, self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        return story

    def _build_payment_details(self, booking):
        """Build payment summary section matching preview"""
        story = []
        
        # Travel Information section (matching preview)
        travel_info = Paragraph(
            '<b>Travel Information</b><br/><br/>'
            'Please keep this voucher with you during travel. Present it at check-in and to service providers as confirmation of your booking.',
            ParagraphStyle(
                'TravelInfo',
                alignment=TA_LEFT,
                spaceAfter=15,
                spaceBefore=15,
                backColor=colors.lightgrey,
                borderWidth=0.5,
                borderColor=colors.lightgrey,
                borderPadding=12,
                fontSize=10
            )
        )
        story.append(travel_info)
        
        # Payment Summary (matching preview layout)
        total_amount = booking.total_amount or 0
        paid_amount = sum(p.amount for p in booking.payments) if booking.payments else 0
        balance = total_amount - paid_amount
        
        # Clean payment summary table
        payment_data = [
            ["Payment Summary"],
            [f"Total Amount: ${total_amount:.2f}"],
            [f"Amount Paid: ${paid_amount:.2f}"],
            [f"Balance Due: ${balance:.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[3*inch])
        payment_table.setStyle(TableStyle([
            # Header
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('BACKGROUND', (0, 0), (0, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Balance Due row emphasis
            ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 3), (0, 3), 11),
            ('TEXTCOLOR', (0, 3), (0, 3), colors.darkblue),
            
            # Clean borders
            ('BOX', (0, 0), (0, -1), 1, colors.darkblue),
            ('LINEABOVE', (0, 3), (0, 3), 1, colors.lightgrey),
            
            # Consistent padding
            ('TOPPADDING', (0, 0), (0, -1), 8),
            ('BOTTOMPADDING', (0, 0), (0, -1), 8),
            ('LEFTPADDING', (0, 0), (0, -1), 12),
            ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 20))
        
        return story

    def _build_footer(self):
        """Build clean and neat footer"""
        story = []
        
        # Clean footer with two columns - banking and contact info
        footer_data = [
            ["Banking Information", "Contact Information"],
            ["Arabi Travel Bank", "sales@arabtravel.ps"],
            ["Account USD= 9070-142464-510", "www.arabtravel.ps"],
            ["", "+97022956640"],
            ["Bank Of Palestine", ""],
            ["Branch Name: Ramallah Branch", "Alersal St, zakat Bld"],
            ["0458/2220908/001/3000/000", "Ramallah, P.OBOX:27"],
            ["", ""],
            ["Bank Details:", ""],
            ["Bank Name: Arab Bank, Acct. No.: 142464", ""]
        ]
        
        footer_table = Table(footer_data, colWidths=[3.25*inch, 3.25*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),  # Headers
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 0), (1, 0), 1, colors.lightgrey),  # Underline headers
        ]))
        
        story.append(footer_table)
        story.append(Spacer(1, 15))
        
        # Thank you message
        thank_you = Paragraph(
            '<b><font color="#000080">ARABI TRAVEL</font></b><br/>'
            '<font color="#000080">Thank you for booking with Arabi Travel</font>',
            ParagraphStyle(
                'ThankYou',
                alignment=TA_CENTER,
                fontSize=10,
                spaceAfter=10
            )
        )
        story.append(thank_you)
        
        return story


# Global instance
voucher_generator = VoucherGenerator()