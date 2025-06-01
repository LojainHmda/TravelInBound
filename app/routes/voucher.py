"""
Voucher generation routes
"""

from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.voucher_generator import voucher_generator
from app.models import Booking
import tempfile
import os

voucher_bp = Blueprint('voucher', __name__)

@voucher_bp.route('/booking/<int:booking_id>/voucher/preview')
@login_required
def voucher_preview(booking_id):
    """Show voucher preview page"""
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking/voucher_preview.html', booking=booking)

@voucher_bp.route('/booking/<int:booking_id>/voucher', methods=['POST', 'GET'])
@login_required
def generate_voucher(booking_id):
    """Generate and download voucher for booking"""
    try:
        # Get the booking
        booking = Booking.query.get_or_404(booking_id)
        
        # Get instructions from query parameter
        instructions = request.args.get('instructions', '')
        
        # Generate the voucher PDF with instructions
        voucher_buffer = voucher_generator.generate_voucher(booking_id, instructions)
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(voucher_buffer.getvalue())
        temp_file.close()
        
        # Generate filename
        filename = f"Voucher_{booking.reference_number}.pdf"
        
        # Return the file for download
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating voucher: {str(e)}', 'error')
        return redirect(url_for('voucher.voucher_preview', booking_id=booking_id))

@voucher_bp.route('/booking/<int:booking_id>/voucher')
@login_required  
def download_voucher(booking_id):
    """Download voucher PDF directly"""
    return generate_voucher(booking_id)

@voucher_bp.route('/api/booking/<int:booking_id>/voucher', methods=['POST'])
@login_required
def api_generate_voucher(booking_id):
    """API endpoint to generate voucher"""
    try:
        # Get the booking
        booking = Booking.query.get_or_404(booking_id)
        
        # Generate the voucher PDF
        voucher_buffer = voucher_generator.generate_voucher(booking_id)
        
        return jsonify({
            'success': True,
            'message': f'Voucher generated successfully for booking {booking.reference_number}',
            'download_url': f'/booking/{booking_id}/voucher'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500