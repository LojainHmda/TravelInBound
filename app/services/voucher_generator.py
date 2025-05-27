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
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000080'),
            backgroundColor=colors.HexColor('#F0F8FF'),
            alignment=TA_LEFT,
            spaceAfter=10,
            leftIndent=10,
            topPadding=5,
            bottomPadding=5
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
        """Build the header section matching the voucher format with logo"""
        story = []
        
        # Invoice header with logo section
        invoice_header_data = [
            [
                f"INVOICE: #{booking.reference_number}",
                "",
                "ARABI TRAVEL"
            ],
            [
                "",
                "",
                "+1-555-TRAVEL"
            ],
            [
                f"Booking ID: {booking.reference_number}",
                "",
                "info@travelbookpro.com"
            ],
            [
                f"Booking Date: {booking.created_at.strftime('%d/%m/%Y')}",
                "",
                "www.travelbookpro.com"
            ],
            [
                f"Due Date: {booking.created_at.strftime('%d/%m/%Y')}",
                "",
                ""
            ],
            [
                f"GDS PNR : {booking.reference_number[:6]} {booking.reference_number[6:] if len(booking.reference_number) > 6 else ''}",
                "",
                ""
            ]
        ]
        
        invoice_header_table = Table(invoice_header_data, colWidths=[3*inch, 1*inch, 2.5*inch])
        invoice_header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (2, 0), 14),
            ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#000080')),  # Dark blue for Arabi Travel
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#000080')),  # Dark blue header
            ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#FFC107')),  # Yellow text
        ]))
        
        story.append(invoice_header_table)
        story.append(Spacer(1, 20))
        
        # Customer info and booking summary section
        customer_name = booking.requester.username if booking.requester else "N/A"
        customer_location = booking.requester.email if booking.requester else "N/A"
        total_pax = len(booking.service_items) if booking.service_items else 1
        start_date = booking.service_items[0].start_date.strftime('%d/%m/%Y') if booking.service_items else "N/A"
        booked_by = booking.requester.username if booking.requester else "N/A"
        
        customer_header_data = [
            [
                f"{customer_name}",
                "",
                f"Total Pax: {total_pax:02d}"
            ],
            [
                f"{customer_location}",
                "",
                f"Start Date: {start_date}"
            ],
            [
                "",
                "",
                f"Booked By: {booked_by}"
            ]
        ]
        
        customer_header_table = Table(customer_header_data, colWidths=[3*inch, 1*inch, 2.5*inch])
        customer_header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(customer_header_table)
        story.append(Spacer(1, 25))
        
        return story

    def _build_booking_details(self, booking):
        """Build booking summary section"""
        story = []
        
        # Booking summary
        summary_data = [
            ["Total Services:", str(len(booking.service_items))],
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
        """Build customer information section"""
        story = []
        
        story.append(Paragraph("Customer Details", self.styles['SectionHeader']))
        
        customer_info = f"""
        <b>{booking.requester.username if booking.requester else 'N/A'}</b><br/>
        Email: {booking.requester.email if booking.requester else 'N/A'}<br/>
        Booking Reference: {booking.reference_number}
        """
        
        story.append(Paragraph(customer_info, self.styles['BookingInfo']))
        story.append(Spacer(1, 15))
        
        return story

    def _build_service_details(self, booking):
        """Build detailed service information matching voucher format"""
        story = []
        
        if not booking.service_items:
            return story
        
        # Group services by type for better organization
        flight_services = [s for s in booking.service_items if s.service_type == 'FLIGHT']
        hotel_services = [s for s in booking.service_items if s.service_type == 'HOTEL']
        other_services = [s for s in booking.service_items if s.service_type not in ['FLIGHT', 'HOTEL']]
        
        # Build Flight Details Section
        if flight_services:
            story.extend(self._build_flight_details(flight_services))
        
        # Build Hotel Details Section  
        if hotel_services:
            story.extend(self._build_hotel_details(hotel_services))
            
        # Build Other Services Section
        if other_services:
            story.extend(self._build_other_services(other_services))
        
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
        """Build payment summary section"""
        story = []
        
        story.append(Paragraph("Fare Details", self.styles['SectionHeader']))
        
        # Calculate totals
        total_amount = booking.total_amount or 0
        paid_amount = sum(payment.amount for payment in booking.payments) if booking.payments else 0
        balance = total_amount - paid_amount
        
        payment_data = [
            ["Total Amount", f"$ {total_amount:.2f}"],
            ["Amount Paid", f"$ {paid_amount:.2f}"],
            ["Balance Outstanding", f"$ {balance:.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[4*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (1, 0), (1, -1), 20),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F8FF')),
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 30))
        
        return story

    def _build_footer(self):
        """Build footer with bank details matching voucher format"""
        story = []
        
        # Bank details section
        bank_info = """
        <para align=center>
        <b>TravelBookPro Bank</b><br/>
        Account USD= 1234-567890-001<br/>
        ------------------<br/><br/>
        <b>Bank Of America</b><br/>
        Branch Name : Main Branch<br/>
        1234/5678901/001/2000/000<br/><br/>
        <b>Thank You</b>
        </para>
        """
        
        story.append(Paragraph(bank_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Company footer
        company_footer = """
        <para align=center>
        <b>Bank Details:</b> Bank Name: TravelBookPro Bank, Acct. No.: 567890<br/>
        www.travelbookpro.com • info@travelbookpro.com • +1-555-TRAVEL<br/>
        <b>TravelBookPro</b><br/>
        123 Travel Street, Business District, City, State 12345<br/>
        <b>Thank you for booking with TravelBookPro</b>
        </para>
        """
        
        story.append(Paragraph(company_footer, self.styles['Normal']))
        
        return story


# Global instance
voucher_generator = VoucherGenerator()