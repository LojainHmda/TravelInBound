"""
Screen Context AI Service
Provides AI with awareness of the current screen and enables contextual actions
"""

import json
from datetime import datetime
from app.services.ai_chat import travel_ai

class ScreenContextAI:
    def __init__(self):
        self.ai_assistant = travel_ai
    
    def process_contextual_query(self, user_query, screen_context, user_context=None):
        """Process query with screen context awareness"""
        
        # Enhance the query with screen context
        enhanced_intent = self._analyze_contextual_intent(user_query, screen_context)
        
        # Process with context-aware data fetching
        response = self._handle_contextual_actions(enhanced_intent, screen_context, user_context)
        
        return response
    
    def _analyze_contextual_intent(self, query, screen_context):
        """Analyze query with screen context"""
        
        system_prompt = f"""
        You are an AI assistant with screen context awareness for a travel booking platform.
        
        Current Screen Context:
        - Page: {screen_context.get('page', 'unknown')}
        - URL: {screen_context.get('url', 'unknown')}
        - Visible Elements: {json.dumps(screen_context.get('elements', {}), indent=2)}
        - Current Data: {json.dumps(screen_context.get('current_data', {}), indent=2)}
        
        User Query: "{query}"
        
        Analyze the query considering the current screen context and extract:
        1. Intent (contextual_action, screen_interaction, data_manipulation, navigation, etc.)
        2. Target elements or data on screen
        3. Desired actions
        4. Context-specific entities
        
        Examples:
        - On booking detail page + "update status" → intent: "update_booking_status"
        - On customer list + "send email to this customer" → intent: "send_customer_email"
        - On dashboard + "show me details of the top booking" → intent: "expand_booking_details"
        
        Respond with JSON:
        {{
            "intent": "contextual_action",
            "screen_action": "update_field",
            "target_element": "booking_status",
            "action_type": "update",
            "entities": {{}},
            "requires_confirmation": true,
            "confidence": 0.9
        }}
        """
        
        try:
            response = self.ai_assistant.client.chat.completions.create(
                model=self.ai_assistant.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "intent": "general_help",
                "error": str(e),
                "confidence": 0.5
            }
    
    def _handle_contextual_actions(self, intent, screen_context, user_context):
        """Handle actions based on screen context"""
        
        action_type = intent.get("screen_action")
        target = intent.get("target_element")
        
        response = {
            "success": True,
            "action_performed": None,
            "screen_updates": {},
            "ai_response": "",
            "next_steps": []
        }
        
        try:
            # Handle different contextual actions
            if action_type == "update_field":
                response = self._handle_field_update(intent, screen_context)
            elif action_type == "navigate":
                response = self._handle_navigation(intent, screen_context)
            elif action_type == "filter_data":
                response = self._handle_data_filtering(intent, screen_context)
            elif action_type == "bulk_action":
                response = self._handle_bulk_action(intent, screen_context)
            elif action_type == "create_record":
                response = self._handle_record_creation(intent, screen_context)
            else:
                # Default: provide contextual information
                response = self._provide_contextual_info(intent, screen_context)
                
        except Exception as e:
            response["success"] = False
            response["error"] = str(e)
        
        return response
    
    def _handle_field_update(self, intent, screen_context):
        """Handle field updates on current screen"""
        
        target_field = intent.get("target_element")
        current_page = screen_context.get("page")
        current_data = screen_context.get("current_data", {})
        
        response = {
            "success": True,
            "action_performed": f"update_{target_field}",
            "screen_updates": {
                "field": target_field,
                "suggested_values": [],
                "form_action": f"/api/update/{current_page}"
            },
            "ai_response": f"I can help you update the {target_field}. ",
            "next_steps": [
                f"Click on the {target_field} field",
                "Select or enter the new value",
                "Click Save to confirm"
            ]
        }
        
        # Provide context-specific suggestions
        if target_field == "status" and "booking" in current_page:
            response["screen_updates"]["suggested_values"] = [
                "REQUEST", "IN_PROGRESS", "CONFIRMED", "CANCELLED"
            ]
            response["ai_response"] += "Here are the available booking status options."
        
        elif target_field == "payment_status":
            response["screen_updates"]["suggested_values"] = [
                "NONE", "PARTIAL", "FULL"
            ]
            response["ai_response"] += "Here are the payment status options."
        
        return response
    
    def _handle_navigation(self, intent, screen_context):
        """Handle navigation requests"""
        
        target_page = intent.get("target_element")
        current_data = screen_context.get("current_data", {})
        
        # Build navigation URL based on context
        nav_url = "/"
        if target_page == "booking_details" and current_data.get("booking_id"):
            nav_url = f"/booking/{current_data['booking_id']}"
        elif target_page == "customer_details" and current_data.get("customer_id"):
            nav_url = f"/customer/{current_data['customer_id']}"
        elif target_page == "finance":
            nav_url = "/finance"
        
        return {
            "success": True,
            "action_performed": "navigate",
            "screen_updates": {
                "redirect_url": nav_url,
                "new_page": target_page
            },
            "ai_response": f"Navigating to {target_page}...",
            "next_steps": ["Page will load automatically"]
        }
    
    def _handle_data_filtering(self, intent, screen_context):
        """Handle data filtering on current screen"""
        
        filter_criteria = intent.get("entities", {})
        current_page = screen_context.get("page")
        
        return {
            "success": True,
            "action_performed": "filter_data",
            "screen_updates": {
                "filters": filter_criteria,
                "table_update": True,
                "filter_url": f"/api/filter/{current_page}"
            },
            "ai_response": "Applying filters to the current data view...",
            "next_steps": ["Data will refresh with applied filters"]
        }
    
    def _handle_bulk_action(self, intent, screen_context):
        """Handle bulk actions on multiple items"""
        
        action = intent.get("target_element")
        selected_items = screen_context.get("selected_items", [])
        
        return {
            "success": True,
            "action_performed": f"bulk_{action}",
            "screen_updates": {
                "bulk_action": action,
                "affected_items": len(selected_items),
                "confirmation_required": True
            },
            "ai_response": f"Ready to perform {action} on {len(selected_items)} selected items.",
            "next_steps": [
                "Review selected items",
                "Confirm the bulk action",
                "Monitor progress"
            ]
        }
    
    def _provide_contextual_info(self, intent, screen_context):
        """Provide helpful information based on current screen"""
        
        current_page = screen_context.get("page", "unknown")
        current_data = screen_context.get("current_data", {})
        
        # Generate contextual AI response
        context_prompt = f"""
        The user is currently on the {current_page} page with this data:
        {json.dumps(current_data, indent=2)}
        
        Provide helpful information about what they can do on this screen,
        what the data means, and suggest relevant actions.
        Be specific to their current context.
        """
        
        try:
            response = self.ai_assistant.client.chat.completions.create(
                model=self.ai_assistant.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for a travel booking platform. Provide contextual help based on the current screen."},
                    {"role": "user", "content": context_prompt}
                ]
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as e:
            ai_response = f"I can see you're on the {current_page} page. How can I help you with the information displayed here?"
        
        return {
            "success": True,
            "action_performed": "contextual_help",
            "screen_updates": {},
            "ai_response": ai_response,
            "next_steps": ["Ask me about specific elements on this page"]
        }

# Global instance
screen_context_ai = ScreenContextAI()