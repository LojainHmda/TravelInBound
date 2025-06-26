"""
API routes that bypass CSRF protection
"""
from flask import Blueprint, request, jsonify
from app.services.passport_scanner import PassportScanner
import base64

# Create API blueprint 
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/scan-passport', methods=['POST'])
def scan_passport():
    """API endpoint to extract customer data from passport image - CSRF exempt"""
    try:
        if 'passport_image' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No passport image provided'
            }), 400
        
        file = request.files['passport_image']
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No file selected'
            }), 400
        
        # Read and encode the image
        file_content = file.read()
        if not file_content:
            return jsonify({
                'success': False, 
                'error': 'Empty file uploaded'
            }), 400
        
        # Convert to base64
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Initialize passport scanner and extract data
        scanner = PassportScanner()
        extracted_data = scanner.extract_passport_data(base64_image)
        
        if extracted_data:
            return jsonify({
                'success': True,
                'data': extracted_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unable to extract passport data from the image'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing passport image: {str(e)}'
        }), 500