import os
import base64
import logging
import traceback
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from app.utils.openai_helper import analyze_flight_ticket

# Create a blueprint for tool-related routes
tools_bp = Blueprint('tools', __name__, url_prefix='/tools')

@tools_bp.route('/ticket-scanner')
def ticket_scanner():
    """Display the flight ticket scanner tool page"""
    has_api_key = bool(os.environ.get("OPENAI_API_KEY"))
    return render_template('tools/ticket_scanner.html', has_api_key=has_api_key)

@tools_bp.route('/analyze-ticket', methods=['POST'])
def analyze_ticket():
    """API endpoint for analyzing ticket images with AI"""
    # This route is exempted from CSRF protection since it's an API endpoint
    # called from JavaScript
    try:
        if not os.environ.get("OPENAI_API_KEY"):
            return jsonify({'error': 'OpenAI API key is not configured. Please contact the administrator.'}), 500

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'Invalid file'}), 400

        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return jsonify({'error': 'File must be an image (JPG, JPEG, PNG)'}), 400

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        try:
            file_data = file.read()
            file_size = len(file_data)

            if file_size > 5 * 1024 * 1024:
                return jsonify({'error': 'File too large. Please upload an image smaller than 5MB'}), 400

            if file_size < 100:
                return jsonify({'error': 'File too small. The image may be corrupt or empty'}), 400

            img_data = base64.b64encode(file_data).decode('utf-8')

            current_app.logger.info(
                f"[{timestamp}] Received image: {file.filename}, size: {file_size} bytes"
            )

        except Exception as e:
            current_app.logger.error(f"[{timestamp}] Error reading image file: {str(e)}")
            return jsonify({'error': f"Could not process image: {str(e)}"}), 400

        current_app.logger.info(f"[{timestamp}] Sending image to OpenAI for analysis.")

        analysis_results = analyze_flight_ticket(img_data)

        if 'error' in analysis_results and analysis_results['error']:
            error_msg = analysis_results['error']
            current_app.logger.error(f"[{timestamp}] OpenAI analysis error: {error_msg}")
            return jsonify({'error': f"OpenAI analysis error: {error_msg}"}), 500

        current_app.logger.info(
            f"[{timestamp}] Success - Flight: {analysis_results.get('flight_number')}, "
            f"Airline: {analysis_results.get('airline')}, "
            f"{analysis_results.get('departure_airport')} → {analysis_results.get('arrival_airport')}"
        )

        return jsonify({'success': True, 'results': analysis_results})

    except Exception as e:
        stack_trace = traceback.format_exc()
        current_app.logger.error(f"Unhandled error: {str(e)}\n{stack_trace}")
        return jsonify({'error': f"Error processing ticket: {str(e)}"}), 500
