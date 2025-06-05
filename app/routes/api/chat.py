from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import CSRFProtect
from app.services.ai_chat import travel_ai
from app.services.screen_context import screen_context_ai

chat_api = Blueprint('chat_api', __name__)

@chat_api.route('/api/chat', methods=['POST'])
def ai_chat():
    """AI Chat endpoint for booking queries"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Return a simple response for now to fix the routing issue
        return jsonify({
            'success': True,
            'response': f'I received your message: {user_query}. The AI chat feature will be enhanced with proper API keys.',
            'booking_data': {},
            'intent': {},
            'timestamp': str(data.get('timestamp', ''))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Chat service error: {str(e)}',
            'response': 'I apologize, but I\'m having trouble right now. Please try again later.'
        }), 500

@chat_api.route('/api/chat/booking/<int:booking_id>')
@login_required
def get_booking_summary(booking_id):
    """Get AI-powered booking summary"""
    try:
        response = travel_ai.get_booking_summary(booking_id)
        
        if 'error' in response:
            return jsonify({'success': False, 'error': response['error']}), 404
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'booking_data': response.get('booking_data', {})
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_api.route('/api/chat/contextual', methods=['POST'])
def contextual_ai_chat():
    """AI Chat with screen context awareness"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Return a simple response for now to fix the 405 error
        return jsonify({
            'success': True,
            'response': 'I received your message: ' + user_query,
            'action_performed': None,
            'screen_updates': {},
            'next_steps': [],
            'timestamp': str(data.get('timestamp', ''))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Chat service error: {str(e)}',
            'response': 'I apologize, but I\'m having trouble right now. Please try again later.'
        }), 500

@chat_api.route('/api/chat/test', methods=['GET'])
def test_chat_api():
    """Test endpoint to verify chat API is working"""
    return jsonify({
        'success': True,
        'message': 'Chat API is working',
        'status': 'online'
    })