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
        """Build the header section with company logo and booking info"""
        story = []
        
        # Company header table
        header_data = [
            [
                f"VOUCHER: #{booking.reference_number}",
                "TravelBookPro",
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
            ]
        ]
        
        header_table = Table(header_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 16),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#000080')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F8FF')),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
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
        """Build detailed service information"""
        story = []
        
        if not booking.service_items:
            return story
            
        story.append(Paragraph("Service Details", self.styles['SectionHeader']))
        
        for i, service in enumerate(booking.service_items, 1):
            story.append(Paragraph(f"Service {i} Details", self.styles['Heading3']))
            
            # Service information table
            service_data = [
                ["Service Type:", service.service_type.replace('_', ' ').title()],
                ["Description:", service.description or "N/A"],
                ["Start Date:", service.start_date.strftime('%d/%m/%Y')],
                ["End Date:", service.end_date.strftime('%d/%m/%Y')],
                ["Amount:", f"$ {service.amount:.2f}" if service.amount else "$ 0.00"],
                ["Status:", service.status.replace('_', ' ').title()],
            ]
            
            service_table = Table(service_data, colWidths=[2*inch, 4*inch])
            service_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('RIGHTPADDING', (0, 0), (0, -1), 10),
                ('LEFTPADDING', (1, 0), (1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(service_table)
            story.append(Spacer(1, 15))
            
            # Documents if any
            if service.documents:
                story.append(Paragraph("Related Documents:", self.styles['Heading4']))
                for doc in service.documents:
                    doc_info = f"• {doc.document_type}: {doc.document_number or 'N/A'}"
                    story.append(Paragraph(doc_info, self.styles['Normal']))
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
        """Build footer with company information"""
        story = []
        
        # Company details
        footer_info = """
        <para align=center>
        <b>TravelBookPro</b><br/>
        Your Trusted Travel Partner<br/>
        Email: info@travelbookpro.com • Phone: +1-555-TRAVEL<br/>
        www.travelbookpro.com<br/><br/>
        <b>Thank you for choosing TravelBookPro!</b>
        </para>
        """
        
        story.append(Paragraph(footer_info, self.styles['Normal']))
        
        return story


# Global instance
voucher_generator = VoucherGenerator()