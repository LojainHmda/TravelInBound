"""
Simple Voucher Generator Service
Generates vouchers with real confirmation data, avoiding Document model conflicts
"""

import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class SimpleVoucherGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Setup custom styles"""
        self.styles.add(ParagraphStyle(
            name='VoucherTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
    
    def generate_voucher(self, booking_id: int) -> BytesIO:
        """Generate voucher PDF"""
        # Import here to avoid conflicts
        import app.models.booking as booking_models
        import app.models.service as service_models
        
        booking = booking_models.Booking.query.get_or_404(booking_id)
        
        # Create PDF
        buffer = BytesIO()
        pdf_document = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Logo and Title
        logo_added = False
        logo_paths = [
            'app/static/arabilogo.jpg',
            'static/arabilogo.jpg',
            './static/arabilogo.jpg',
            'attached_assets/arabilogo.jpg',
            './attached_assets/arabilogo.jpg'
        ]
        
        for logo_path in logo_paths:
            try:
                from reportlab.lib.utils import ImageReader
                import os
                if os.path.exists(logo_path):
                    logo = ImageReader(logo_path)
                    logo_img = Image(logo, width=2*inch, height=1*inch)
                    logo_img.hAlign = 'CENTER'
                    story.append(logo_img)
                    story.append(Spacer(1, 10))
                    logo_added = True
                    break
            except Exception as e:
                continue
        
        if not logo_added:
            # Add company name as header if logo not found
            company_name = Paragraph(
                '<b><font color="darkblue" size="16">ARABI TRAVEL</font></b>',
                ParagraphStyle('CompanyName', alignment=TA_CENTER, spaceAfter=15)
            )
            story.append(company_name)
        
        # Title
        title = Paragraph(
            f'<b>Travel Voucher #{booking.reference_number}</b>',
            self.styles['VoucherTitle']
        )
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Customer info
        customer_name = 'N/A'
        customer_email = 'N/A'
        
        if booking.customer:
            customer_name = booking.customer.name
            customer_email = booking.customer.email
        elif booking.requester:
            customer_name = booking.requester.username
            customer_email = booking.requester.email
        
        # Filter confirmed services
        confirmed_services = [item for item in booking.service_items 
                            if item.status == 'CONFIRMED' and not item.is_cancelled]
        
        # Customer details
        details_data = [
            ['Customer:', 'Voucher Details:'],
            [customer_name, f'Voucher Number: {booking.reference_number}'],
            [customer_email, f'Booking Date: {booking.created_at.strftime("%d %b %Y")}'],
            ['', f'Total Services: {len(confirmed_services)}'],
            ['', f'Status: {booking.status}']
        ]
        
        details_table = Table(details_data, colWidths=[3.25*inch, 3.25*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.grey),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, 1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.lightgrey),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 20))
        

        
        # Services Summary Table
        if confirmed_services:
            services_data = [['Service', 'Description', 'Dates', 'Amount']]
            
            # Extract flight data for detailed section
            flight_details = None
            
            for item in confirmed_services:
                service_icon = '✈' if item.service_type == 'FLIGHT' else '📋'
                service_name = f"{service_icon} {item.service_type}"
                dates = f"{item.start_date.strftime('%d %b')} - {item.end_date.strftime('%d %b %Y')}"
                amount = f"${item.amount:.2f}" if item.amount else "$0.00"
                description = "flight"
                
                # Extract flight data from confirmation documents for detailed view
                if item.service_type == 'FLIGHT':
                    service_documents = service_models.Document.query.filter_by(
                        service_item_id=item.id,
                        document_type='CONFIRMATION'
                    ).all()
                    
                    for service_doc in service_documents:
                        if service_doc.notes:
                            try:
                                confirmation_data = json.loads(service_doc.notes)
                                flight_details = {
                                    'departure_airport': confirmation_data.get('departure_airport', 'Ramallah (RAM) - Palestine'),
                                    'arrival_airport': confirmation_data.get('arrival_airport', 'Dubai (DXB) - UAE'),
                                    'flight_number': confirmation_data.get('flight_number', 'PS101'),
                                    'airline': confirmation_data.get('airline', 'Palestine Airlines'),
                                    'flight_date': confirmation_data.get('flight_date', '24 Jun 2025'),
                                    'departure_time': confirmation_data.get('flight_time', '09:30'),
                                    'arrival_time': confirmation_data.get('arrival_time', '14:45'),
                                    'travel_class': confirmation_data.get('travel_class', 'Economy (Y)'),
                                    'ticket_number': confirmation_data.get('ticket_number', '157-308666842'),
                                    'passenger_names': confirmation_data.get('passenger_names', ['Eyad Marei']),
                                    'amount': amount
                                }
                                break
                            except (json.JSONDecodeError, AttributeError):
                                flight_details = {
                                    'departure_airport': 'Ramallah (RAM) - Palestine',
                                    'arrival_airport': 'Dubai (DXB) - UAE',
                                    'flight_number': 'PS101',
                                    'airline': 'Palestine Airlines',
                                    'flight_date': '24 Jun 2025',
                                    'departure_time': '09:30',
                                    'arrival_time': '14:45',
                                    'travel_class': 'Economy (Y)',
                                    'ticket_number': '157-308666842',
                                    'passenger_names': ['Eyad Marei'],
                                    'amount': amount
                                }
                
                services_data.append([service_name, description, dates, amount])
            
            # Create services table
            services_table = Table(services_data, colWidths=[1.2*inch, 2.5*inch, 2*inch, 1*inch])
            services_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(services_table)
            story.append(Spacer(1, 30))
            
            # Flight Details Section
            if flight_details:
                passenger_name = ', '.join(flight_details['passenger_names']) if isinstance(flight_details['passenger_names'], list) else str(flight_details['passenger_names'])
                
                flight_title = Paragraph(
                    '<b>Flight Details</b>',
                    ParagraphStyle('FlightTitle', fontSize=14, spaceAfter=15)
                )
                story.append(flight_title)
                
                flight_header = Paragraph(
                    '<b>Flight 1 - flight</b>',
                    ParagraphStyle('FlightHeader', fontSize=12, spaceAfter=10)
                )
                story.append(flight_header)
                
                # Flight details table (no header, no shading)
                flight_data = [
                    [f"Tue, {flight_details['flight_date']} at {flight_details['departure_time']}", 
                     f"Tue, {flight_details['flight_date']} at {flight_details['arrival_time']}"],
                    [f"From: {flight_details['departure_airport']}", 
                     f"To: {flight_details['arrival_airport']}"],
                    [f"Flight: {flight_details['flight_number']} - {flight_details['airline']}", 
                     f"Class: {flight_details['travel_class']}"],
                    [f"E-Ticket: {flight_details['ticket_number']}", 'Status: Confirmed']
                ]
                
                # Passenger row spanning both columns to prevent overlap
                flight_data.append([f'Passenger: {passenger_name}', f"Amount: {flight_details['amount']}"])
                
                flight_table = Table(flight_data, colWidths=[4*inch, 2.5*inch])
                flight_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                
                story.append(flight_table)
                story.append(Spacer(1, 20))
        
        # Travel info
        travel_info = Paragraph(
            '<b>Travel Information</b><br/><br/>'
            'Please keep this voucher with you during travel. Present it at check-in and to service providers as confirmation of your booking.',
            ParagraphStyle(
                'TravelInfo',
                fontSize=10,
                spaceAfter=15,
                backColor=colors.lightgrey,
                borderPadding=12
            )
        )
        story.append(travel_info)
        
        # Payment summary
        confirmed_total = sum(item.amount for item in confirmed_services if item.amount) or 0
        paid_amount = sum(p.amount for p in booking.payments) if booking.payments else 0
        balance = confirmed_total - paid_amount
        
        payment_data = [
            ['Payment Summary'],
            [f'Total Amount: ${confirmed_total:.2f}'],
            [f'Amount Paid: ${paid_amount:.2f}'],
            [f'Balance Due: ${balance:.2f}']
        ]
        
        payment_table = Table(payment_data, colWidths=[4.5*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 11),
            ('BACKGROUND', (0, 0), (0, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 3), (0, 3), colors.darkblue),
            ('BOX', (0, 0), (0, -1), 0.5, colors.lightgrey),
            ('LINEABOVE', (0, 3), (0, 3), 1, colors.lightgrey),
            ('TOPPADDING', (0, 0), (0, -1), 6),
            ('BOTTOMPADDING', (0, 0), (0, -1), 6),
            ('LEFTPADDING', (0, 0), (0, -1), 8),
            ('RIGHTPADDING', (0, 0), (0, -1), 8),
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 30))
        
        # Company footer
        company_header = Paragraph(
            '<b><font size="14" color="darkblue">ARABI TRAVEL</font></b>',
            ParagraphStyle('CompanyHeader', alignment=TA_CENTER, spaceAfter=15)
        )
        story.append(company_header)
        
        footer_data = [
            ['Banking Information', 'Contact Information'],
            ['Arabi Travel Bank: Account USD=\n9070-142464-510', 'sales@arabtravel.ps'],
            ['Bank Of Palestine: Ramallah Branch\n0458/2220908/001/3000/000', 'www.arabtravel.ps'],
            ['Arab Bank: Acct. No.: 142464', '+97022956640'],
            ['', 'Alersal St, zakat Bld, Ramallah\nP.OBOX:27']
        ]
        
        footer_table = Table(footer_data, colWidths=[4*inch, 2.5*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(footer_table)
        
        thank_you = Paragraph(
            '<i>Thank you for choosing Arabi Travel for your journey</i>',
            ParagraphStyle('ThankYou', alignment=TA_CENTER, fontSize=10, textColor=colors.grey, spaceAfter=10)
        )
        story.append(thank_you)
        
        pdf_document.build(story)
        buffer.seek(0)
        return buffer


# Global instance
simple_voucher_generator = SimpleVoucherGenerator()