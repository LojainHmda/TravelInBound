"""
Screen Context AI Service
Processes user queries with awareness of current screen content
"""

import json
import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import OpenAI
from sqlalchemy import text
from app import db
from app.models import Booking, Customer, ServiceItem, Document, SupplierPayment

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)


class ScreenContextAI:
    def __init__(self):
        self.openai_client = openai_client

    def process_contextual_query(self, user_query: str, screen_context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user query with screen context awareness"""
        try:
            # Analyze the screen context and user intent
            context_analysis = self._analyze_screen_context(screen_context)
            
            # Generate contextual prompt
            system_prompt = self._build_system_prompt(context_analysis, screen_context)
            
            # Process the query with OpenAI
            ai_response = self._get_ai_response(system_prompt, user_query, screen_context)
            
            # Execute any required actions
            action_result = self._execute_contextual_actions(ai_response, screen_context, user_context)
            
            return {
                'success': True,
                'ai_response': ai_response.get('response', 'I can help you with that!'),
                'action_performed': action_result.get('action_performed'),
                'screen_updates': action_result.get('screen_updates', {}),
                'next_steps': action_result.get('next_steps', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'ai_response': f'I apologize, but I encountered an error while reading the screen context: {str(e)}',
                'action_performed': None,
                'screen_updates': {},
                'next_steps': []
            }

    def _analyze_screen_context(self, screen_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current screen context to understand what data is available"""
        analysis = {
            'page_type': screen_context.get('page', 'unknown'),
            'current_booking': None,
            'current_customer': None,
            'visible_bookings': [],
            'visible_customers': [],
            'available_actions': [],
            'form_fields': {},
            'data_summary': ''
        }

        # Extract current booking/customer from URL or page data
        current_data = screen_context.get('current_data', {})
        if current_data.get('booking_id'):
            analysis['current_booking'] = self._get_booking_details(current_data['booking_id'])
        if current_data.get('customer_id'):
            analysis['current_customer'] = self._get_customer_details(current_data['customer_id'])

        # Extract visible data from tables and cards
        visible_data = screen_context.get('visible_data', {})
        table_data = screen_context.get('table_data', {})
        
        # Process visible bookings
        for key, data in visible_data.items():
            if isinstance(data, dict) and data.get('booking_reference'):
                booking_info = self._enrich_booking_from_reference(data['booking_reference'])
                if booking_info:
                    analysis['visible_bookings'].append(booking_info)

        # Process table data for bookings and customers
        for table_key, table in table_data.items():
            rows = table.get('rows', [])
            for row in rows:
                # Check if this looks like a booking row
                if any('IR-' in str(value) for value in row.values()):
                    ref_match = None
                    for value in row.values():
                        if isinstance(value, str) and 'IR-' in value:
                            ref_match = re.search(r'IR-[A-Za-z0-9]+', value)
                            if ref_match:
                                booking_info = self._enrich_booking_from_reference(ref_match.group())
                                if booking_info:
                                    analysis['visible_bookings'].append(booking_info)
                                break

        # Extract available actions
        actions = screen_context.get('available_actions', [])
        analysis['available_actions'] = [action['text'] for action in actions if action.get('has_action')]

        # Extract form fields
        form_fields = screen_context.get('form_fields', {})
        analysis['form_fields'] = form_fields

        # Create data summary
        analysis['data_summary'] = self._create_data_summary(analysis)

        return analysis

    def _get_booking_details(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed booking information"""
        try:
            booking = Booking.query.get(int(booking_id))
            if booking:
                return {
                    'id': booking.id,
                    'reference': booking.reference_number,
                    'customer_name': booking.requester.username if booking.requester else 'Unknown',
                    'status': booking.status,
                    'total_amount': booking.total_amount,
                    'payment_status': booking.payment_status,
                    'service_count': len(booking.service_items)
                }
        except Exception:
            pass
        return None

    def _get_customer_details(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed customer information"""
        try:
            # Note: Using User model as customer for now
            from app.models import User
            customer = User.query.get(int(customer_id))
            if customer:
                return {
                    'id': customer.id,
                    'name': customer.username,
                    'email': customer.email,
                    'booking_count': len(customer.bookings) if hasattr(customer, 'bookings') else 0
                }
        except Exception:
            pass
        return None

    def _enrich_booking_from_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Get booking details from reference number"""
        try:
            booking = Booking.query.filter_by(reference_number=reference).first()
            if booking:
                return {
                    'id': booking.id,
                    'reference': booking.reference_number,
                    'customer_name': booking.requester.username if booking.requester else 'Unknown',
                    'status': booking.status,
                    'total_amount': booking.total_amount,
                    'payment_status': booking.payment_status
                }
        except Exception:
            pass
        return None

    def _create_data_summary(self, analysis: Dict[str, Any]) -> str:
        """Create a summary of available data"""
        summary_parts = []
        
        if analysis['current_booking']:
            booking = analysis['current_booking']
            summary_parts.append(f"Current booking: {booking['reference']} for {booking['customer_name']} (Status: {booking['status']}, Amount: ${booking['total_amount']})")
        
        if analysis['current_customer']:
            customer = analysis['current_customer']
            summary_parts.append(f"Current customer: {customer['name']} ({customer['email']}) with {customer['booking_count']} bookings")
        
        if analysis['visible_bookings']:
            summary_parts.append(f"Visible bookings: {len(analysis['visible_bookings'])} bookings shown")
            
        if analysis['available_actions']:
            summary_parts.append(f"Available actions: {', '.join(analysis['available_actions'][:5])}")

        return '; '.join(summary_parts) if summary_parts else 'No specific data detected on current page'

    def _build_system_prompt(self, context_analysis: Dict[str, Any], screen_context: Dict[str, Any]) -> str:
        """Build system prompt with current screen context"""
        
        page_type = context_analysis['page_type']
        data_summary = context_analysis['data_summary']
        
        prompt = f"""You are an AI assistant for a travel booking platform with full awareness of the current screen content.

CURRENT SCREEN CONTEXT:
- Page Type: {page_type}
- URL: {screen_context.get('pathname', 'unknown')}
- Data Available: {data_summary}

SCREEN-SPECIFIC INSTRUCTIONS:
"""

        if page_type == 'booking_details' and context_analysis['current_booking']:
            booking = context_analysis['current_booking']
            prompt += f"""
You are viewing booking {booking['reference']} for {booking['customer_name']}.
Current status: {booking['status']}
Payment status: {booking['payment_status']}
Total amount: ${booking['total_amount']}

When user says "this booking" or "update this", refer to booking {booking['reference']}.
You can help with status updates, payment processing, and booking modifications.
"""

        elif page_type == 'booking_list' and context_analysis['visible_bookings']:
            bookings = context_analysis['visible_bookings']
            prompt += f"""
You are viewing a list of {len(bookings)} bookings.
When user mentions "first booking", "top booking", or "highest value", refer to the appropriate booking from this list:
"""
            for i, booking in enumerate(bookings[:5]):
                prompt += f"- {i+1}. {booking['reference']} ({booking['customer_name']}) - ${booking['total_amount']}\n"

        elif page_type == 'main_dashboard':
            prompt += """
You are on the main dashboard showing booking overview and metrics.
You can explain metrics, suggest actions, and help navigate to specific areas.
"""

        prompt += f"""

AVAILABLE ACTIONS ON THIS PAGE: {', '.join(context_analysis['available_actions'][:10])}

RESPONSE GUIDELINES:
1. Be specific about what you see on the current screen
2. When user uses "this", "here", "current" - refer to the specific data shown
3. Offer concrete actions based on available buttons/links
4. If asked to perform an action, provide specific steps or indicate you'll do it
5. Always acknowledge the current context in your response

Respond as if you can see exactly what the user sees on their screen right now."""

        return prompt

    def _get_ai_response(self, system_prompt: str, user_query: str, screen_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI response with screen context awareness"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User asks: {user_query}\n\nScreen context: {json.dumps(screen_context, indent=2)}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {
                'response': f'I can see your current screen but had trouble processing your request: {str(e)}',
                'action_needed': None
            }

    def _execute_contextual_actions(self, ai_response: Dict[str, Any], screen_context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on AI response and screen context"""
        result = {
            'action_performed': None,
            'screen_updates': {},
            'next_steps': []
        }

        action_needed = ai_response.get('action_needed')
        if not action_needed:
            return result

        try:
            if action_needed == 'navigate_to_booking':
                booking_id = ai_response.get('booking_id')
                if booking_id:
                    result['screen_updates']['redirect_url'] = f'/booking/{booking_id}'
                    result['action_performed'] = f'Navigating to booking {booking_id}'

            elif action_needed == 'update_booking_status':
                booking_id = ai_response.get('booking_id')
                new_status = ai_response.get('new_status')
                if booking_id and new_status:
                    # Update booking status in database
                    booking = Booking.query.get(booking_id)
                    if booking:
                        booking.status = new_status
                        db.session.commit()
                        result['action_performed'] = f'Updated booking {booking.reference_number} status to {new_status}'
                        result['screen_updates']['highlight_element'] = '.status-badge'

            elif action_needed == 'highlight_field':
                field_name = ai_response.get('field_name')
                if field_name:
                    result['screen_updates']['highlight_element'] = f'[name="{field_name}"]'
                    result['action_performed'] = f'Highlighted {field_name} field'

            elif action_needed == 'suggest_values':
                field_name = ai_response.get('field_name')
                suggestions = ai_response.get('suggestions', [])
                if field_name and suggestions:
                    result['screen_updates']['field'] = field_name
                    result['screen_updates']['suggested_values'] = suggestions
                    result['action_performed'] = f'Provided suggestions for {field_name}'

        except Exception as e:
            result['action_performed'] = f'Action failed: {str(e)}'

        return result


# Global instance
screen_context_ai = ScreenContextAI()