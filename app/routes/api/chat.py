from flask import Blueprint, request, jsonify
import os
from openai import OpenAI

chat_api = Blueprint('chat_api', __name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@chat_api.route('/api/chat', methods=['POST'])
def ai_chat():
    """AI Chat endpoint for booking queries"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process query with OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful travel booking assistant. You can help users:
                    1. Create new bookings for flights, hotels, transport, visas, and insurance
                    2. Check booking status and details
                    3. Answer travel-related questions
                    4. Provide travel recommendations
                    
                    When users ask to create bookings, guide them through the process and ask for necessary details like:
                    - Destination and dates
                    - Number of passengers
                    - Service type (flight, hotel, etc.)
                    - Budget preferences
                    
                    Keep responses helpful, professional, and concise."""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Analyze if this is a booking creation request
        booking_intent = analyze_booking_intent(user_query)
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'booking_data': booking_intent,
            'intent': {'type': 'booking_assistance'},
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

def analyze_booking_intent(query):
    """Analyze if the query is related to booking creation"""
    booking_keywords = ['book', 'create', 'reserve', 'flight', 'hotel', 'travel', 'trip', 'vacation', 'visa', 'insurance']
    query_lower = query.lower()
    
    if any(keyword in query_lower for keyword in booking_keywords):
        return {
            'is_booking_request': True,
            'suggested_action': 'create_booking',
            'confidence': 0.8
        }
    
    return {
        'is_booking_request': False,
        'suggested_action': None,
        'confidence': 0.1
    }

@chat_api.route('/api/chat/test', methods=['GET'])
def test_chat_api():
    """Test endpoint to verify chat API is working"""
    return jsonify({
        'success': True,
        'message': 'Chat API is working',
        'status': 'online'
    })