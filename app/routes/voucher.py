"""
Voucher generation routes
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.services.airline_voucher_generator import AirlineVoucherGenerator
from app.models import Booking
import tempfile
import os

voucher_bp = Blueprint('voucher', __name__)

@voucher_bp.route('/booking/<int:booking_id>/voucher/preview')
@login_required
def voucher_preview(booking_id):
    """Show voucher preview page"""
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking/voucher_preview_new.html', booking=booking)

@voucher_bp.route('/booking/<int:booking_id>/voucher', methods=['POST', 'GET'])
def generate_voucher(booking_id):
    """Generate voucher - HTML for GET, PDF for POST - TEMPORARILY NO AUTH FOR TESTING"""
    return _generate_voucher_internal(booking_id)

@voucher_bp.route('/booking/<int:booking_id>/voucher/test', methods=['POST', 'GET'])
def test_voucher_generation(booking_id):
    """Test voucher generation without authentication"""
    return _generate_voucher_internal(booking_id)

def _generate_voucher_internal(booking_id):
    """Generate voucher - HTML for GET, PDF for POST"""
    try:
        from flask import Response
        # Get the booking
        booking = Booking.query.get_or_404(booking_id)
        
        # Generate the voucher using airline generator
        generator = AirlineVoucherGenerator(booking)
        
        if request.method == 'POST':
            # Generate PDF for download
            import logging
            logging.info(f"Generating PDF for booking {booking.reference_number}")
            pdf_buffer = generator.generate_pdf()
            
            # Log PDF generation success
            pdf_size = len(pdf_buffer.getvalue())
            logging.info(f"PDF generated successfully, size: {pdf_size} bytes")
            
            # Return PDF as download
            return Response(
                pdf_buffer.getvalue(),
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename=Voucher_{booking.reference_number}.pdf',
                    'Content-Type': 'application/pdf'
                }
            )
        else:
            # Return HTML voucher for preview
            voucher_html = generator.generate_html()
            return voucher_html
        
    except Exception as e:
        flash(f'Error generating voucher: {str(e)}', 'error')
        return redirect(url_for('voucher.voucher_preview', booking_id=booking_id))



@voucher_bp.route('/api/booking/<int:booking_id>/voucher', methods=['POST'])
@login_required
def api_generate_voucher(booking_id):
    """API endpoint to generate airline-style voucher"""
    try:
        # Get the booking
        booking = Booking.query.get_or_404(booking_id)
        
        # Generate the voucher PDF using airline generator
        generator = AirlineVoucherGenerator(booking)
        voucher_buffer = generator.generate_pdf()
        
        return jsonify({
            'success': True,
            'message': f'Voucher generated successfully for booking {booking.reference_number}',
            'voucher_url': f'/booking/{booking_id}/voucher'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500