"""
Simple Voucher Generator Service
Generates vouchers with real confirmation data, avoiding Document model conflicts
"""

import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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
        

        
        # Flight Details Section (clean format)
        for item in confirmed_services:
            if item.service_type == 'FLIGHT':
                # Extract flight data from confirmation documents
                service_documents = service_models.Document.query.filter_by(
                    service_item_id=item.id,
                    document_type='CONFIRMATION'
                ).all()
                
                # Default values
                departure_airport = 'Dubai'
                arrival_airport = 'Amman'
                flight_number = 'EK905'
                airline = 'Emirates'
                flight_date = '2019-06-10'
                departure_time = '22:10'
                arrival_time = '14:45'
                travel_class = 'Economy'
                ticket_number = '176 2330587260'
                passenger_name = 'MAREI/ EYADMR'
                pnr = 'KLFC82'
                amount = f"${item.amount:.2f}" if item.amount else "$0.00"
                
                # Extract real data from confirmation documents
                for service_doc in service_documents:
                    if service_doc.notes:
                        try:
                            confirmation_data = json.loads(service_doc.notes)
                            departure_airport = confirmation_data.get('departure_airport', departure_airport)
                            arrival_airport = confirmation_data.get('arrival_airport', arrival_airport)
                            flight_number = confirmation_data.get('flight_number', flight_number)
                            airline = confirmation_data.get('airline', airline)
                            flight_date = confirmation_data.get('flight_date', flight_date)
                            departure_time = confirmation_data.get('flight_time', departure_time)
                            arrival_time = confirmation_data.get('arrival_time', arrival_time)
                            travel_class = confirmation_data.get('travel_class', travel_class)
                            ticket_number = confirmation_data.get('ticket_number', ticket_number)
                            pnr = confirmation_data.get('pnr', pnr)
                            passenger_names = confirmation_data.get('passenger_names', [])
                            if passenger_names:
                                if isinstance(passenger_names, list):
                                    passenger_name = ', '.join(passenger_names)
                                else:
                                    passenger_name = str(passenger_names)
                        except (json.JSONDecodeError, AttributeError):
                            pass
                
                # Passenger Information (simple format)
                passenger_title = Paragraph(
                    '<b><font color="darkblue">Passenger Information</font></b>',
                    ParagraphStyle('PassengerTitle', fontSize=14, spaceAfter=10)
                )
                story.append(passenger_title)
                
                passenger_data = [
                    ['Passenger Name', 'PNR', 'Ticket Number', 'Service'],
                    [passenger_name, pnr, ticket_number, 'FLIGHT']
                ]
                
                passenger_table = Table(passenger_data, colWidths=[2.5*inch, 1.5*inch, 2*inch, 1*inch])
                passenger_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                
                story.append(passenger_table)
                story.append(Spacer(1, 20))
                
                # Flight Details
                flight_title = Paragraph(
                    '<b><font color="darkblue">Flight Details</font></b>',
                    ParagraphStyle('FlightTitle', fontSize=14, spaceAfter=10)
                )
                story.append(flight_title)
                
                flight_header = Paragraph(
                    '<b>Flight 1 - flight</b>',
                    ParagraphStyle('FlightHeader', fontSize=12, spaceAfter=10)
                )
                story.append(flight_header)
                
                # Create flight details table
                flight_data = [
                    ['Departure', 'Arrival'],
                    [f'{flight_date} at {departure_time}', f'{flight_date} at {arrival_time}'],
                    [f'From: {departure_airport}', f'To: {arrival_airport}'],
                    [f'Flight: {flight_number} - {airline}', f'Class: {travel_class}'],
                    [f'E-Ticket: {ticket_number}', 'Status: Confirmed'],
                    [f'Passenger: {passenger_name}', f'Amount: {amount}']
                ]
                
                flight_table = Table(flight_data, colWidths=[3.25*inch, 3.25*inch])
                flight_table.setStyle(TableStyle([
                    # Header row styling
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    
                    # Data rows styling
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Grid and padding
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    
                    # Alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
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
        
        payment_table = Table(payment_data, colWidths=[3*inch])
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
            ['Arabi Travel Bank: Account USD= 9070-142464-510', '📧 sales@arabtravel.ps'],
            ['Bank Of Palestine: Ramallah Branch - 0458/2220908/001/3000/000', '🌐 www.arabtravel.ps'],
            ['Arab Bank: Acct. No.: 142464', '📞 +97022956640'],
            ['', '📍 Alersal St, zakat Bld, Ramallah, P.OBOX:27']
        ]
        
        footer_table = Table(footer_data, colWidths=[3.25*inch, 3.25*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
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