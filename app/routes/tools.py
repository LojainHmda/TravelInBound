import os
import base64
import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from app.utils.openai_helper import analyze_flight_ticket

# Create a blueprint for tool-related routes
tools_bp = Blueprint('tools', __name__, url_prefix='/tools')

@tools_bp.route('/ticket-scanner')
def ticket_scanner():
    """Display the flight ticket scanner tool page"""
    return render_template('tools/ticket_scanner.html')

@tools_bp.route('/analyze-ticket', methods=['POST'])
def analyze_ticket():
    """API endpoint for analyzing ticket images with AI"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'Invalid file'}), 400
        
        # Check if the file is an image
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return jsonify({'error': 'File must be an image (JPG, JPEG, PNG)'}), 400
        
        # Check if OpenAI API key is available
        if not os.environ.get("OPENAI_API_KEY"):
            return jsonify({'error': 'OpenAI API key is not configured. Please contact the administrator.'}), 500
        
        # Read file and convert to base64
        file_data = file.read()
        img_data = base64.b64encode(file_data).decode('utf-8')
        
        # Log that we're calling the OpenAI API
        current_app.logger.info(f"Calling OpenAI API to analyze ticket image of size {len(img_data)}")
        
        # Analyze the image with OpenAI
        analysis_results = analyze_flight_ticket(img_data)
        
        # Check if we got an error from the OpenAI analysis
        if 'error' in analysis_results and analysis_results['error']:
            return jsonify({'error': f"OpenAI analysis error: {analysis_results['error']}"}), 500
        
        current_app.logger.info(f"Successfully analyzed ticket image")
        return jsonify({
            'success': True,
            'results': analysis_results
        })
    except Exception as e:
        current_app.logger.error(f"Error in API ticket analysis: {str(e)}")
        return jsonify({'error': f"Error processing ticket: {str(e)}"}), 500