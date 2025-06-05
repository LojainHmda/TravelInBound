from flask import Blueprint, request, jsonify

chat_api = Blueprint('chat_api', __name__)

@chat_api.route('/api/chat', methods=['POST'])
def ai_chat():
    """AI Chat endpoint for booking queries"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Simple response without AI dependencies
        return jsonify({
            'success': True,
            'response': f'I received your message: {user_query}. AI chat features require OpenAI API key configuration.',
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
def get_booking_summary(booking_id):
    """Get booking summary"""
    try:
        return jsonify({
            'success': True,
            'response': f'Booking summary for ID {booking_id} will be available when AI services are configured.',
            'booking_data': {}
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
        
        # Simple response without AI dependencies
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