"""
Voucher generation routes
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.airline_voucher_generator import AirlineVoucherGenerator
from app.models import Booking

voucher_bp = Blueprint('voucher', __name__)

@voucher_bp.route('/booking/<int:booking_id>/voucher/preview')
@login_required
def voucher_preview(booking_id):
    """Show voucher preview page"""
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking/voucher_preview_new.html', booking=booking)

@voucher_bp.route('/booking/<int:booking_id>/voucher', methods=['POST', 'GET'])
@login_required
def generate_voucher(booking_id):
    """Generate and display airline-style voucher for booking"""
    try:
        # Get the booking
        booking = Booking.query.get_or_404(booking_id)
        
        # Generate the voucher HTML using airline generator
        generator = AirlineVoucherGenerator(booking)
        voucher_html = generator.generate_html()
        
        # Return HTML directly for display/printing
        return voucher_html
        
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
    """API endpoint to generate airline-style voucher"""
    try:
        # Get the booking
        booking = Booking.query.get_or_404(booking_id)
        
        # Generate the voucher HTML using airline generator
        generator = AirlineVoucherGenerator(booking)
        voucher_html = generator.generate_html()
        
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