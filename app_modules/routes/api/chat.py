from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.ai_chat import travel_ai
from app.services.screen_context import screen_context_ai

chat_api = Blueprint('chat_api', __name__)

@chat_api.route('/api/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI Chat endpoint for booking queries"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user context
        user_context = {
            'user_id': current_user.id,
            'username': current_user.username if hasattr(current_user, 'username') else 'User'
        }
        
        # Process the query with AI
        response = travel_ai.process_query(user_query, user_context)
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'booking_data': response.get('booking_data', {}),
            'intent': response.get('intent', {}),
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
@login_required
def contextual_ai_chat():
    """AI Chat with screen context awareness"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        screen_context = data.get('screen_context', {})
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user context
        user_context = {
            'user_id': current_user.id,
            'username': current_user.username if hasattr(current_user, 'username') else 'User'
        }
        
        # Process with screen context awareness
        response = screen_context_ai.process_contextual_query(user_query, screen_context, user_context)
        
        return jsonify({
            'success': response.get('success', True),
            'response': response.get('ai_response', 'I can help you with that!'),
            'action_performed': response.get('action_performed'),
            'screen_updates': response.get('screen_updates', {}),
            'next_steps': response.get('next_steps', []),
            'timestamp': str(data.get('timestamp', ''))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Contextual chat service error: {str(e)}',
            'response': 'I apologize, but I\'m having trouble understanding the current screen context. Please try again.'
        }), 500