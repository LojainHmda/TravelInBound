"""
Clean Voucher Generator Service
Generates professional travel vouchers with clean, simple layout matching the preview
"""

import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class CleanVoucherGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup clean, simple styles"""
        self.styles.add(ParagraphStyle(
            name='CleanTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.grey
        ))
        
        self.styles.add(ParagraphStyle(
            name='CleanNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_voucher(self, booking_id: int) -> BytesIO:
        """Generate a clean voucher PDF"""
        from app.models import Booking
        
        booking = Booking.query.get_or_404(booking_id)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
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
            self.styles['CleanTitle']
        )
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Get customer details (prefer customer over requester)
        customer_name = 'N/A'
        customer_email = 'N/A'
        
        if booking.customer:
            customer_name = booking.customer.name
            customer_email = booking.customer.email
        elif booking.requester:
            customer_name = booking.requester.username
            customer_email = booking.requester.email
        
        # Filter for confirmed services only (exclude cancelled and unconfirmed)
        confirmed_services = [item for item in booking.service_items 
                            if item.status == 'CONFIRMED' and not item.is_cancelled]
        
        # Customer and Voucher Details
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
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),  # Headers
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.grey),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),  # Customer name
            ('FONTSIZE', (0, 1), (0, 1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.lightgrey),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        # Service Details Table - Only show confirmed services
        if confirmed_services:
            service_data = [
                ['Service', 'Description', 'Dates', 'Status', 'Amount']
            ]
            
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
                
                # Get description from confirmation data if available
                description = item.description or "N/A"
                
                # Extract better description from confirmation documents
                for doc in item.documents:
                    if doc.document_type == 'CONFIRMATION' and doc.notes:
                        try:
                            confirmation_data = json.loads(doc.notes)
                            
                            if item.service_type == 'FLIGHT':
                                # Build flight description from confirmation data
                                departure = confirmation_data.get('departure_airport', '')
                                arrival = confirmation_data.get('arrival_airport', '')
                                flight_num = confirmation_data.get('flight_number', '')
                                airline = confirmation_data.get('airline', '')
                                
                                if departure and arrival:
                                    if flight_num and airline:
                                        description = f"{airline} {flight_num}: {departure} → {arrival}"
                                    else:
                                        description = f"{departure} → {arrival}"
                                        
                            elif item.service_type == 'HOTEL':
                                # Build hotel description from confirmation data
                                hotel_name = confirmation_data.get('hotel_name', '')
                                city = confirmation_data.get('city', '')
                                if hotel_name:
                                    description = f"{hotel_name}" + (f", {city}" if city else "")
                                    
                        except (json.JSONDecodeError, AttributeError):
                            pass  # Keep original description if parsing fails
                
                # Since we're only showing confirmed services, all should show as "Confirmed"
                status = "Confirmed"
                
                service_data.append([
                    service_name,
                    description,
                    dates,
                    status,
                    amount
                ])
            
            service_table = Table(service_data, colWidths=[1.2*inch, 2.2*inch, 1.3*inch, 1*inch, 0.8*inch])
            service_table.setStyle(TableStyle([
                # Header row
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                
                # Grid and alignment
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (4, 0), (4, -1), 'RIGHT'),  # Amount column
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(service_table)
            story.append(Spacer(1, 20))
        
        # Travel Information
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
        
        # Payment Summary - Calculate based on confirmed services only
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
        
        # Company Footer
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
        
        doc.build(story)
        buffer.seek(0)
        return buffer


# Global instance
clean_voucher_generator = CleanVoucherGenerator()