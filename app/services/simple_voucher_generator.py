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
        
        # Extract and display passenger information
        passenger_info = []
        for item in confirmed_services:
            service_documents = service_models.Document.query.filter_by(
                service_item_id=item.id,
                document_type='CONFIRMATION'
            ).all()
            
            for service_doc in service_documents:
                if service_doc.notes:
                    try:
                        confirmation_data = json.loads(service_doc.notes)
                        passenger_names = confirmation_data.get('passenger_names', [])
                        pnr = confirmation_data.get('pnr', '')
                        ticket_number = confirmation_data.get('ticket_number', '')
                        
                        if passenger_names:
                            if isinstance(passenger_names, list):
                                for passenger in passenger_names:
                                    passenger_info.append({
                                        'name': passenger,
                                        'pnr': pnr,
                                        'ticket': ticket_number,
                                        'service_type': item.service_type
                                    })
                            else:
                                passenger_info.append({
                                    'name': str(passenger_names),
                                    'pnr': pnr,
                                    'ticket': ticket_number,
                                    'service_type': item.service_type
                                })
                    except (json.JSONDecodeError, AttributeError):
                        pass
        
        # Display passenger information if available
        if passenger_info:
            passenger_title = Paragraph(
                '<b>Passenger Information</b>',
                ParagraphStyle('PassengerTitle', fontSize=12, textColor=colors.darkblue, spaceAfter=10)
            )
            story.append(passenger_title)
            
            passenger_data = [['Passenger Name', 'PNR', 'Ticket Number', 'Service']]
            for passenger in passenger_info:
                passenger_data.append([
                    passenger['name'],
                    passenger['pnr'] or 'N/A',
                    passenger['ticket'] or 'N/A',
                    passenger['service_type']
                ])
            
            passenger_table = Table(passenger_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            passenger_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(passenger_table)
            story.append(Spacer(1, 20))
        
        # Service details
        if confirmed_services:
            service_data = [['Service', 'Flight Details', 'Travel Dates', 'Status', 'Amount']]
            
            for item in confirmed_services:
                service_icon = {
                    'FLIGHT': '✈',
                    'HOTEL': '🏨',
                    'TRANSPORT': '🚗',
                    'VISA': '📋',
                    'INSURANCE': '🛡'
                }.get(item.service_type, '📋')
                
                service_name = f"{service_icon} {item.service_type}"
                dates = f"{item.start_date.strftime('%d %b')} - {item.end_date.strftime('%d %b %Y')}"
                amount = f"${item.amount:.2f}" if item.amount else "$0.00"
                description = item.description or "N/A"
                
                # Extract route from confirmation data
                service_documents = service_models.Document.query.filter_by(
                    service_item_id=item.id,
                    document_type='CONFIRMATION'
                ).all()
                
                for service_doc in service_documents:
                    if service_doc.notes:
                        try:
                            confirmation_data = json.loads(service_doc.notes)
                            
                            if item.service_type == 'FLIGHT':
                                departure = confirmation_data.get('departure_airport', '')
                                arrival = confirmation_data.get('arrival_airport', '')
                                flight_num = confirmation_data.get('flight_number', '')
                                airline = confirmation_data.get('airline', '')
                                flight_date = confirmation_data.get('flight_date', '')
                                flight_time = confirmation_data.get('flight_time', '')
                                travel_class = confirmation_data.get('travel_class', '')
                                ticket_number = confirmation_data.get('ticket_number', '')
                                pnr = confirmation_data.get('pnr', '')
                                passenger_names = confirmation_data.get('passenger_names', [])
                                
                                if departure and arrival:
                                    # Build comprehensive flight description
                                    flight_info = []
                                    if flight_num and airline:
                                        flight_info.append(f"{airline} {flight_num}")
                                    
                                    flight_info.append(f"{departure} → {arrival}")
                                    
                                    if flight_date:
                                        flight_info.append(f"Date: {flight_date}")
                                    
                                    if flight_time:
                                        flight_info.append(f"Time: {flight_time}")
                                    
                                    if travel_class:
                                        flight_info.append(f"Class: {travel_class}")
                                    
                                    if ticket_number:
                                        flight_info.append(f"Ticket: {ticket_number}")
                                    
                                    if pnr:
                                        flight_info.append(f"PNR: {pnr}")
                                    
                                    if passenger_names:
                                        passengers = ', '.join(passenger_names) if isinstance(passenger_names, list) else str(passenger_names)
                                        flight_info.append(f"Passengers: {passengers}")
                                    
                                    description = ' | '.join(flight_info)
                                        
                            elif item.service_type == 'HOTEL':
                                hotel_name = confirmation_data.get('hotel_name', '')
                                city = confirmation_data.get('city', '')
                                if hotel_name:
                                    description = f"{hotel_name}" + (f", {city}" if city else "")
                                    
                        except (json.JSONDecodeError, AttributeError):
                            pass
                
                service_data.append([
                    service_name,
                    description,
                    dates,
                    "Confirmed",
                    amount
                ])
            
            service_table = Table(service_data, colWidths=[0.8*inch, 3.5*inch, 1.2*inch, 0.8*inch, 0.7*inch])
            service_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
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