from flask import Blueprint, jsonify, send_file, request
from app import db
from app.models.booking import Booking
from app.models.customer import Customer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from datetime import datetime

invoice_api = Blueprint('invoice_api', __name__)

@invoice_api.route('/api/invoice/<int:booking_id>/generate', methods=['POST'])

def generate_invoice_pdf(booking_id):
    """Generate PDF invoice for a booking"""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Company header
        company_style = ParagraphStyle(
            'CompanyHeader',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.blue,
            alignment=1  # Center
        )
        story.append(Paragraph("Travel Booking System", company_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Invoice title
        invoice_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.black
        )
        story.append(Paragraph(f"INVOICE - {booking.reference_number}", invoice_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Customer and booking info
        info_data = [
            ['Customer:', booking.requester.first_name + ' ' + booking.requester.last_name if booking.requester else 'Unknown'],
            ['Email:', booking.requester.email if booking.requester else 'N/A'],
            ['Booking Reference:', booking.reference_number],
            ['Booking Date:', booking.created_at.strftime('%Y-%m-%d') if booking.created_at else 'N/A'],
            ['Status:', booking.status],
            ['Invoice Date:', datetime.now().strftime('%Y-%m-%d')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Services table
        story.append(Paragraph("Services:", styles['Heading3']))
        story.append(Spacer(1, 0.2*inch))
        
        service_data = [['Service Type', 'Description', 'Dates', 'Amount']]
        total_amount = 0
        
        for item in booking.service_items:
            date_range = ''
            if item.start_date and item.end_date:
                date_range = f"{item.start_date} to {item.end_date}"
            
            service_data.append([
                item.service_type,
                item.description or 'N/A',
                date_range,
                f"${item.amount:.2f}" if item.amount else "$0.00"
            ])
            total_amount += item.amount or 0
        
        service_table = Table(service_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(service_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Total
        total_data = [['TOTAL AMOUNT:', f"${total_amount:.2f}"]]
        total_table = Table(total_data, colWidths=[5*inch, 1.5*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ]))
        story.append(total_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"invoice_{booking.reference_number}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate invoice: {str(e)}'}), 500

@invoice_api.route('/api/invoice/<int:booking_id>/download')

def download_invoice(booking_id):
    """Quick download link for invoice"""
    return generate_invoice_pdf(booking_id)