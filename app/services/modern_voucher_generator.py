
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
        # Brand colors matching dashboard - using correct 0-1 range
        self.primary_color = colors.Color(0, 0, 0.5)      # #000080 - Dark blue
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
            fontSize=16,
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
            fontSize=12,
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
            fontSize=9,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=2
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
        
        # Header section (contains both customer and voucher details)
        content.extend(self._create_header(booking))
        
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
        """Create company header with logo and aligned content"""
        content = []
        
        # Logo and company info in a table for proper alignment
        from reportlab.lib.utils import ImageReader
        import os
        
        # Try to load the logo
        logo_path = os.path.join('static', 'images', 'arabilogo.jpg')
        if not os.path.exists(logo_path):
            logo_path = 'arabilogo.jpg'  # Try root directory
        
        if os.path.exists(logo_path):
            # Create header with logo and text aligned
            from reportlab.platypus import Image
            
            # Create image with proper sizing
            logo_img = Image(logo_path, width=1.2*inch, height=1.2*inch)
            
            header_data = [
                [logo_img, 
                 Paragraph("ARABI TRAVEL<br/>TRAVEL VOUCHER", self.styles['CompanyHeader'])]
            ]
            
            header_table = Table(header_data, colWidths=[1.5*inch, 4.5*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Logo left aligned
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Text center aligned
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            content.append(header_table)
        else:
            # Fallback without logo
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
        
        # Use full page width for header alignment
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
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
        """Create simple flight details from confirmation data"""
        content = []
        

        
        # Simple display of confirmation details
        if confirmation_details:
            airline = confirmation_details.get('airline', 'N/A')
            flight_number = confirmation_details.get('flight_number', 'N/A')
            departure_airport = confirmation_details.get('departure_airport', 'N/A')
            arrival_airport = confirmation_details.get('arrival_airport', 'N/A')
            flight_date = confirmation_details.get('flight_date', item.start_date.strftime('%Y-%m-%d'))
            flight_time = confirmation_details.get('flight_time', 'N/A')
            travel_class = confirmation_details.get('travel_class', 'Economy')
            passenger_names = confirmation_details.get('passenger_names', [])
            eticket_numbers = confirmation_details.get('eticket_numbers', [])
            ticket_number = confirmation_details.get('ticket_number', '')
            
            # Format date
            try:
                from datetime import datetime
                date_obj = datetime.strptime(flight_date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d %b %Y')
            except:
                formatted_date = flight_date
            
            # Format passenger names
            if passenger_names:
                passengers_text = ", ".join(passenger_names)
            else:
                # Try to get from booking customer or requester
                booking = item.booking
                if booking.customer:
                    passengers_text = booking.customer.name
                else:
                    passengers_text = booking.requester.username
            
            # Format e-ticket numbers - use ticket_number if eticket_numbers is empty
            if eticket_numbers:
                etickets_text = ", ".join(eticket_numbers)
            elif ticket_number:
                etickets_text = ticket_number
            else:
                etickets_text = "To be provided"
            
            # Create table with header row - combine route info in description
            route_info = f"{departure_airport} → {arrival_airport}"
            full_description = f"{airline} {flight_number}\n{route_info}"
            
            flight_data = [
                ["Service", "Description", "Dates", "Status", "Amount"],
                ["FLIGHT", full_description, formatted_date, "Confirmed", f"${item.amount:.2f}" if item.amount else "$0.00"],
                ["Class", travel_class, "", "", ""],
                ["Passengers", passengers_text, "", "", ""],
                ["Ticket Number", etickets_text, "", "", ""]
            ]
        else:
            # Fallback if no confirmation data
            booking = item.booking
            passenger_name = booking.customer.name if booking.customer else booking.requester.username
            
            flight_data = [
                ["Service:", item.description or "Flight Service"],
                ["Date:", item.start_date.strftime('%d %b %Y')],
                ["Passenger:", passenger_name],
                ["Status:", "Confirmed"]
            ]
        
        flight_table = Table(flight_data, colWidths=[1.0*inch, 2.0*inch, 1.5*inch, 1.0*inch, 0.8*inch])
        flight_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            
            # Alternating row colors for data rows only
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.98, 0.98, 0.98)]),
            
            # Only outer border and header line - no internal borders
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Compact padding with better spacing
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            
            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        content.append(flight_table)
        content.append(Spacer(1, 0.2*inch))
        return content

    def _extract_flight_info(self, item, confirmation_details):
        """Extract flight information from confirmation details"""
        if confirmation_details:
            # Use actual confirmation data
            airline = confirmation_details.get('airline', 'TBD')
            flight_number = confirmation_details.get('flight_number', 'TBD')
            departure_airport = confirmation_details.get('departure_airport', 'TBD')
            arrival_airport = confirmation_details.get('arrival_airport', 'TBD')
            flight_time = confirmation_details.get('flight_time', 'TBD')
            flight_class = confirmation_details.get('travel_class', 'Economy')
            
            # Use confirmation flight date if available, otherwise use service dates
            flight_date = confirmation_details.get('flight_date', item.start_date.strftime('%Y-%m-%d'))
            if flight_date and flight_date != item.start_date.strftime('%Y-%m-%d'):
                # Convert date format from YYYY-MM-DD to DD MMM YYYY
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(flight_date, '%Y-%m-%d')
                    departure_date = date_obj.strftime('%d %b %Y')
                except:
                    departure_date = item.start_date.strftime('%d %b %Y')
            else:
                departure_date = item.start_date.strftime('%d %b %Y')
                
            arrival_date = item.end_date.strftime('%d %b %Y')
            
            # Create route from airports
            if departure_airport != 'TBD' and arrival_airport != 'TBD':
                route = f"{departure_airport} → {arrival_airport}"
            else:
                route = item.description if item.description else 'TBD'
            
            departure = f"{departure_date} {flight_time}" if flight_time != 'TBD' else departure_date
            arrival = arrival_date  # Arrival time not typically in confirmation
            
        else:
            # Fallback to service item data only if no confirmation
            airline = 'TBD'
            flight_number = 'TBD'
            route = item.description if item.description else 'TBD'
            departure = item.start_date.strftime('%d %b %Y')
            arrival = item.end_date.strftime('%d %b %Y')
            flight_class = 'Economy'
        
        return {
            'airline': airline,
            'flight_number': flight_number,
            'route': route,
            'departure': departure,
            'arrival': arrival,
            'class': flight_class
        }

    def _create_hotel_details(self, item, confirmation_details, index):
        """Create hotel details using confirmation data with flight-style table"""
        content = []
        
        # Extract hotel information from confirmation details
        if confirmation_details:
            hotel_name = confirmation_details.get('hotel_name', item.description)
            from_date = confirmation_details.get('from_date', item.start_date.strftime('%Y-%m-%d'))
            to_date = confirmation_details.get('to_date', item.end_date.strftime('%Y-%m-%d'))
            meal_plan = confirmation_details.get('meal_plan', 'Room Only')
            rooms = confirmation_details.get('rooms', {})
            
            # Format dates
            try:
                from datetime import datetime
                checkin_obj = datetime.strptime(from_date, '%Y-%m-%d')
                checkout_obj = datetime.strptime(to_date, '%Y-%m-%d')
                formatted_checkin = checkin_obj.strftime('%d %b %Y')
                formatted_checkout = checkout_obj.strftime('%d %b %Y')
                nights = (checkout_obj - checkin_obj).days
            except:
                formatted_checkin = item.start_date.strftime('%d %b %Y')
                formatted_checkout = item.end_date.strftime('%d %b %Y')
                nights = (item.end_date - item.start_date).days
            
            # Format room information
            room_info = []
            if rooms.get('single', 0) > 0:
                room_info.append(f"{rooms['single']} Single")
            if rooms.get('double', 0) > 0:
                room_info.append(f"{rooms['double']} Double")
            if rooms.get('twin', 0) > 0:
                room_info.append(f"{rooms['twin']} Twin")
            if rooms.get('triple', 0) > 0:
                room_info.append(f"{rooms['triple']} Triple")
            
            room_text = ", ".join(room_info) if room_info else "1 Room"
            
            # Create table with same style as flight details
            hotel_data = [
                ["Service", "Description", "Dates", "Status", "Amount"],
                ["HOTEL", hotel_name, f"{formatted_checkin} - {formatted_checkout}", "Confirmed", f"${item.amount:.2f}" if item.amount else "$0.00"],
                ["Meal Plan", meal_plan, f"{nights} nights", "", ""],
                ["Rooms", room_text, "", "", ""]
            ]
        else:
            # Fallback if no confirmation data
            nights = (item.end_date - item.start_date).days
            hotel_data = [
                ["Service", "Description", "Dates", "Status", "Amount"],
                ["HOTEL", item.description, f"{item.start_date.strftime('%d %b %Y')} - {item.end_date.strftime('%d %b %Y')}", "Confirmed", f"${item.amount:.2f}" if item.amount else "$0.00"],
                ["Duration", f"{nights} nights", "", "", ""]
            ]
        
        hotel_table = Table(hotel_data, colWidths=[1.0*inch, 2.0*inch, 1.5*inch, 1.0*inch, 0.8*inch])
        hotel_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            
            # Alternating row colors for data rows only
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.98, 0.98, 0.98)]),
            
            # Only outer border and header line - no internal borders
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Compact padding with better spacing
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            
            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        content.append(hotel_table)
        content.append(Spacer(1, 0.2*inch))
        
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
        """Create payment summary section with integrated header"""
        content = []
        
        # Calculate total from confirmed services only
        confirmed_services = [item for item in booking.service_items if item.status == 'CONFIRMED']
        total_amount = sum(item.amount for item in confirmed_services if item.amount)
        
        # Get total payments
        total_payments = sum(payment.amount for payment in booking.payments) if booking.payments else 0
        balance_due = total_amount - total_payments
        
        payment_data = [
            ["Payment Summary", "Amount"],
            ["Total Amount", f"${total_amount:.2f}"],
            ["Amount Paid", f"${total_payments:.2f}"],
            ["Balance Due", f"${balance_due:.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[4.5*inch, 1.8*inch])
        payment_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            
            # Alternating row colors for data rows only
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.98, 0.98, 0.98)]),
            
            # Only outer border and header line - no internal borders
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Compact padding with better spacing
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            
            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
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
